"""
OmniFocus Integration Client

This module provides integration with OmniFocus using AppleScript
to create hierarchical tags for one-on-one meetings.
"""

import subprocess
import urllib.parse
import logging
from typing import Dict, Any, Optional


class OmniFocusClient:
    """
    Client for integrating with OmniFocus using AppleScript.
    
    This class handles:
    - Creating hierarchical tags for colleagues (any number of levels)
    - Using AppleScript for direct tag creation without tasks
    - Checking if tags already exist
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OmniFocus client with configuration.
        
        Args:
            config: Dictionary containing OmniFocus configuration
        """
        self.config = config.get('omnifocus', {})
        self.method = self.config.get('method', 'applescript')
        self.tag_id = self.config.get('tag_id', '')
        self.tag_url = f"omnifocus:///tag/{self.tag_id}" if self.tag_id else ''
        self.create_task = self.config.get('create_task', False)
        
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if self.method not in ['applescript', 'callback_url', 'api']:
            raise ValueError(f"Unsupported OmniFocus method: {self.method}")
        
        self.logger.info(f"Initialized OmniFocus client using {self.method} method")
    
    def is_available(self) -> bool:
        """
        Check if OmniFocus is available on the system.
        
        Returns:
            True if OmniFocus is available, False otherwise
        """
        try:
            # Check if we can find OmniFocus application
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to exists application process "OmniFocus"'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and 'true' in result.stdout.lower()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.logger.warning(f"Could not check OmniFocus availability: {e}")
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
            
            if self.method == 'applescript':
                return self._create_tag_via_applescript(tag_name, colleague_name, slack_handle)
            elif self.method == 'callback_url':
                return self._create_tag_via_callback_url(tag_name, colleague_name, slack_handle)
            else:
                self.logger.error(f"Method {self.method} not implemented yet")
                return False
                
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
    
    def _create_tag_via_callback_url(self, tag_name: str, colleague_name: str, slack_handle: str) -> bool:
        """
        Create tag using OmniFocus x-callback-url scheme.
        
        Note: OmniFocus x-callback-url doesn't have a direct "create tag only" option.
        We create a task with the tag, which creates the tag as a side effect.
        
        Args:
            tag_name: The hierarchical tag name to create
            colleague_name: Full name of the colleague
            slack_handle: Slack handle (without @)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.create_task:
                # Create a persistent setup task
                task_name = f"One-on-one setup for {colleague_name}"
                note_content = f"Colleague: {colleague_name}\nSlack: @{slack_handle}\n\nSetup completed via automation script."
                self.logger.info(f"Creating OmniFocus task: {task_name}")
            else:
                # Create a temporary task just to create the tag
                task_name = f"[TEMP] Tag creation for {colleague_name}"
                note_content = f"TEMPORARY TASK: Created to generate tag '{tag_name}'\n\nThis task can be deleted - the tag will remain.\n\nColleague: {colleague_name}\nSlack: @{slack_handle}"
                self.logger.info(f"Creating temporary OmniFocus task to generate tag: {tag_name}")
                self.logger.warning("Note: OmniFocus requires creating a task to create a tag. You can delete the temporary task after the tag is created.")
            
            # Build the x-callback-url
            url_params = {
                'name': task_name,
                'tag': tag_name,
                'note': note_content
            }
            
            # URL encode the parameters
            encoded_params = urllib.parse.urlencode(url_params)
            callback_url = f"omnifocus:///add?{encoded_params}"
            
            self.logger.debug(f"Opening OmniFocus URL: {callback_url}")
            
            # Execute the x-callback-url
            result = subprocess.run(['open', callback_url], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                if self.create_task:
                    self.logger.info(f"Successfully created OmniFocus task and tag: {tag_name}")
                else:
                    self.logger.info(f"Successfully created OmniFocus tag: {tag_name} (via temporary task)")
                return True
            else:
                self.logger.error(f"Failed to open OmniFocus URL: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout while trying to create OmniFocus tag")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating OmniFocus tag: {e}")
            return False
    
    def get_tag_info(self, colleague_name: str) -> Dict[str, str]:
        """
        Get information about the tag that would be created for a colleague.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Dictionary containing tag information
        """
        tag_name = self._generate_tag_name(colleague_name)
        
        return {
            'tag_name': tag_name,
            'method': self.method,
            'tag_id': self.tag_id,
            'create_task': self.create_task
        }
