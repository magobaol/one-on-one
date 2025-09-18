"""
OmniFocus Integration Client

This module provides integration with OmniFocus using AppleScript
to create hierarchical tags for one-on-one meetings.
"""

import os
import subprocess
import logging
import time
from typing import Dict, Any, Optional
from .perspective_generator import PerspectiveGenerator
from .output_manager import OutputManager


class OmniFocusClient:
    """
    Client for integrating with OmniFocus using AppleScript.
    
    This class handles:
    - Creating hierarchical tags for colleagues using AppleScript
    - Generating complete perspective plist files for import
    - Automatic import and opening of perspectives
    """
    
    def __init__(self, config: Dict[str, Any], output_manager: OutputManager):
        """
        Initialize OmniFocus client with configuration and output manager.
        
        Args:
            config: Dictionary containing OmniFocus configuration
            output_manager: OutputManager instance for organized file storage
        """
        self.config = config.get('omnifocus', {})
        self.method = self.config.get('method', 'applescript')
        self.tag_id = self.config.get('tag_id', '')
        self.tag_url = f"omnifocus:///tag/{self.tag_id}" if self.tag_id else ''
        self.output_manager = output_manager
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize perspective generator with output manager
        self.perspective_generator = PerspectiveGenerator(output_manager)
        
        # Validate configuration
        if self.method != 'applescript':
            raise ValueError(f"Unsupported OmniFocus method: {self.method}. Only 'applescript' is supported.")
        
        self.logger.info(f"Initialized OmniFocus client using {self.method} method")

    def create_colleague_perspective(self, colleague_name: str) -> bool:
        """
        Create an OmniFocus perspective plist file for the colleague.
        
        This generates a complete perspective plist file that can be imported
        by double-clicking the .ofocus-perspective folder.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            True if perspective plist was created successfully, False otherwise
        """
        try:
            self.logger.info(f"Generating OmniFocus perspective plist for: {colleague_name}")
            
            # Check if we have colleague tag info
            tag_info = self.get_tag_info(colleague_name)
            colleague_tag_id = tag_info.get('tag_id')
            
            if not colleague_tag_id:
                self.logger.error(f"No tag ID found for {colleague_name}. Create the tag first.")
                return False
            
            # Template path (XML template with placeholders)
            template_path = "resources/of-pespective.xml"
            
            # Generate the plist file
            output_file = self.perspective_generator.create_colleague_perspective_plist(
                colleague_name=colleague_name,
                colleague_tag_id=colleague_tag_id,
                template_path=template_path
            )
            
            # Show instructions to user
            self._show_import_instructions(colleague_name, output_file)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create OmniFocus perspective plist: {e}")
            return False

    def create_colleague_tag(self, colleague_name: str, slack_handle: str) -> bool:
        """
        Create a hierarchical tag in OmniFocus for the colleague.
        
        Args:
            colleague_name: Full name of the colleague
            slack_handle: Slack handle (without @)
            
        Returns:
            True if tag creation was successful, False otherwise
        """
        try:
            # Generate tag name from colleague name
            tag_name = self._generate_tag_name(colleague_name)
            
            self.logger.info(f"Creating OmniFocus tag: {tag_name}")
            
            return self._create_tag_via_applescript(tag_name, colleague_name, slack_handle)
                
        except Exception as e:
            self.logger.error(f"Failed to create OmniFocus tag: {e}")
            return False
    
    def _generate_tag_name(self, colleague_name: str) -> str:
        """
        Generate tag name from colleague's full name.
        With URL approach, this is just the colleague name since parent is referenced by URL.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Tag name (just the colleague's name)
        """
        return colleague_name
    
    def _create_tag_via_applescript(self, tag_name: str, colleague_name: str, slack_handle: str) -> bool:
        """
        Create tag under parent using OmniFocus URL reference.
        
        Args:
            tag_name: The colleague's name (will be created as child of parent tag)
            colleague_name: Full name of the colleague
            slack_handle: Slack handle (without @)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.tag_id:
                self.logger.error("No tag_id configured - please set omnifocus.tag_id in config.yaml")
                return False
                
            self.logger.info(f"Creating OmniFocus tag '{tag_name}' under parent tag URL: {self.tag_url}")
            
            # AppleScript to create tag under specific parent using tag ID
            applescript = f'''
            tell application "OmniFocus"
                tell default document
                    set parentTag to missing value
                    
                    try
                        -- Find parent tag by ID (search through all tags including children)
                        set tagID to "{self.tag_id}"
                        
                        -- Search top-level tags first
                        repeat with aTag in tags
                            if id of aTag as string is tagID then
                                set parentTag to aTag
                                exit repeat
                            end if
                        end repeat
                        
                        -- If not found, search child tags
                        if parentTag is missing value then
                            repeat with topTag in tags
                                repeat with childTag in tags of topTag
                                    if id of childTag as string is tagID then
                                        set parentTag to childTag
                                        exit repeat
                                    end if
                                    -- Search grandchildren (3rd level)
                                    repeat with grandTag in tags of childTag
                                        if id of grandTag as string is tagID then
                                            set parentTag to grandTag
                                            exit repeat
                                        end if
                                    end repeat
                                    if parentTag is not missing value then exit repeat
                                end repeat
                                if parentTag is not missing value then exit repeat
                            end repeat
                        end if
                        
                        if parentTag is missing value then
                            return "Error: Could not find parent tag with ID: {self.tag_id}"
                        end if
                        
                        -- Check if child tag already exists
                        set childExists to false
                        repeat with childTag in tags of parentTag
                            if (name of childTag) as string is "{tag_name}" then
                                set childExists to true
                                exit repeat
                            end if
                        end repeat
                        
                        if childExists then
                            return "Tag already exists: " & (name of parentTag) & " > {tag_name}"
                        else
                            -- Create new child tag
                            make new tag at parentTag with properties {{name:"{tag_name}"}}
                            return "Created tag: " & (name of parentTag) & " > {tag_name}"
                        end if
                        
                    on error errorMessage
                        return "AppleScript error: " & errorMessage
                    end try
                end tell
            end tell
            '''
            
            # Execute the AppleScript
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                self.logger.info(f"AppleScript result: {output}")
                
                if "Created tag:" in output or "Tag already exists:" in output:
                    self.logger.info(f"Successfully handled OmniFocus tag: {tag_name}")
                    return True
                elif "Error:" in output:
                    self.logger.error(f"AppleScript error: {output}")
                    return False
                else:
                    self.logger.warning(f"Unexpected AppleScript output: {output}")
                    return False
            else:
                self.logger.error(f"AppleScript failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout while running AppleScript for OmniFocus tag creation")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating OmniFocus tag via AppleScript: {e}")
            return False
    
    
    def get_tag_info(self, colleague_name: str) -> Dict[str, str]:
        """
        Get information about the tag for a colleague, including actual tag ID if it exists.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Dictionary containing tag information with actual tag ID
        """
        tag_name = self._generate_tag_name(colleague_name)
        
        # Try to find the actual child tag ID
        actual_tag_id = self._find_child_tag_id(colleague_name)
        
        return {
            'tag_name': tag_name,
            'method': self.method,
            'tag_id': actual_tag_id or self.tag_id  # Fall back to parent if child not found
        }
    
    def _find_child_tag_id(self, colleague_name: str) -> Optional[str]:
        """
        Find the actual tag ID for a colleague's child tag.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            The tag ID if found, None otherwise
        """
        try:
            tag_name = self._generate_tag_name(colleague_name)
            self.logger.debug(f"Searching for child tag: {tag_name}")
            
            # AppleScript to search for the child tag by name using nested loops
            applescript = f'''
            tell application "OmniFocus"
                tell default document
                    -- Search through all tags up to 3 levels deep
                    repeat with level1Tag in tags
                        if name of level1Tag is "{tag_name}" then
                            return id of level1Tag as string
                        end if
                        
                        -- Search level 2 (children of level 1)
                        repeat with level2Tag in tags of level1Tag
                            if name of level2Tag is "{tag_name}" then
                                return id of level2Tag as string
                            end if
                            
                            -- Search level 3 (children of level 2)
                            repeat with level3Tag in tags of level2Tag
                                if name of level3Tag is "{tag_name}" then
                                    return id of level3Tag as string
                                end if
                            end repeat
                        end repeat
                    end repeat
                    
                    return "NOT_FOUND"
                end tell
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                tag_id = result.stdout.strip()
                if tag_id and tag_id != "NOT_FOUND":
                    self.logger.debug(f"Found child tag ID for '{tag_name}': {tag_id}")
                    return tag_id
                else:
                    self.logger.debug(f"Child tag '{tag_name}' not found")
                    return None
            else:
                self.logger.warning(f"Failed to search for child tag: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.warning(f"Error searching for child tag ID: {e}")
            return None
    
    
    
    def _show_import_instructions(self, colleague_name: str, output_file: str) -> None:
        """Show instructions for importing the generated perspective plist."""
        perspective_folder = os.path.dirname(output_file)
        
        self.logger.info("✅ Perspective plist generated successfully!")
        self.logger.info(f"📁 Perspective file: {perspective_folder}")
        self.logger.info("")
        self.logger.info("📋 TO IMPORT INTO OMNIFOCUS:")
        self.logger.info("   1. Open Finder and navigate to the perspectives folder")
        self.logger.info(f"   2. Double-click the '{os.path.basename(perspective_folder)}' folder")
        self.logger.info("   3. OmniFocus will open and import the perspective automatically")
        self.logger.info(f"   4. The '{colleague_name}' perspective will appear in your perspectives list")
        self.logger.info("")
        self.logger.info("🎯 The perspective is already configured with:")
        self.logger.info(f"   • Tag filter: {colleague_name}")
        self.logger.info("   • Availability: Available and Waiting tasks")
        self.logger.info("   • Custom icon from profile photo")
        self.logger.info("   • All other settings from the Cristian template")
        
    def get_perspective_folder(self, colleague_name: str) -> str:
        """
        Get the path to the colleague's perspective folder for later import.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Path to the .ofocus-perspective folder
        """
        return self.output_manager.get_perspective_folder(colleague_name)
    
    def import_and_open_perspective(self, colleague_name: str) -> bool:
        """
        Import the OmniFocus perspective and open it (final step).
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the perspective folder path
            perspective_folder = self.get_perspective_folder(colleague_name)
            
            if not os.path.exists(perspective_folder):
                self.logger.warning(f"Perspective folder not found: {perspective_folder}")
                return False
            
            self.logger.info("")
            self.logger.info("🚀 FINAL STEP: Importing and opening OmniFocus perspective...")
            
            # Step 1: Automatically import the perspective by opening the .ofocus-perspective folder
            self.logger.info("📥 Auto-importing perspective into OmniFocus...")
            subprocess.run(['open', perspective_folder], timeout=10, check=True)
            
            # Give OmniFocus a moment to import the perspective
            time.sleep(2)
            
            # Step 2: Open the specific perspective using URL scheme
            perspective_url = f"omnifocus:///perspective/{colleague_name}"
            self.logger.info(f"🎯 Opening perspective: {colleague_name}")
            subprocess.run(['open', perspective_url], timeout=5, check=True)
            
            self.logger.info("✅ Perspective imported and opened successfully!")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.warning("⚠️  Timeout while importing perspective - OmniFocus may be slow to respond")
            self._show_manual_perspective_instructions(colleague_name)
            return False
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"⚠️  Failed to auto-import perspective: {e}")
            self._show_manual_perspective_instructions(colleague_name)
            return False
        except Exception as e:
            self.logger.warning(f"⚠️  Error during perspective import: {e}")
            self._show_manual_perspective_instructions(colleague_name)
            return False
    
    def _show_manual_perspective_instructions(self, colleague_name: str) -> None:
        """Show manual import instructions as fallback."""
        try:
            perspective_folder = self.get_perspective_folder(colleague_name)
            self.logger.info("")
            self.logger.info("📋 MANUAL PERSPECTIVE IMPORT INSTRUCTIONS:")
            self.logger.info("   1. Open Finder and navigate to the perspectives folder")
            self.logger.info(f"   2. Double-click the '{os.path.basename(perspective_folder)}' folder")
            self.logger.info("   3. OmniFocus will open and import the perspective automatically")
            self.logger.info(f"   4. The '{colleague_name}' perspective will appear in your perspectives list")
        except Exception as e:
            self.logger.debug(f"Could not show perspective instructions: {e}")
        
