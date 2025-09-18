"""
Keyboard Maestro Integration Client

This module provides functionality for automating Keyboard Maestro macros
using an export/modify/import approach for maximum reliability.

Key features:
- Export template macro XML via AppleScript
- Modify XML with colleague data and custom icons
- Create importable .kmmacros files for seamless import
- Automatic import and opening of created macros
"""

import logging
import subprocess
import uuid
from typing import Dict, Any, Optional, Tuple
import plistlib
import os
import time

from .output_manager import OutputManager


class KeyboardMaestroClient:
    """
    Client for integrating with Keyboard Maestro using export/modify/import approach.
    
    This class handles:
    - Exporting template macro XML via AppleScript
    - Modifying XML with colleague data and custom icons  
    - Creating importable .kmmacros files
    - Automatic import and opening of macros
    """
    
    def __init__(self, config: Dict[str, Any], output_manager: OutputManager):
        """
        Initialize Keyboard Maestro client.
        
        Args:
            config: Dictionary containing Keyboard Maestro configuration
            output_manager: OutputManager instance for accessing colleague files
        """
        self.config = config.get('keyboard_maestro', {})
        self.output_manager = output_manager
        self.template_uuid = self.config.get('template_uuid', 'B8D72CC1-7B5F-4F04-8F08-5A0A6B89B6C7')
        self.template_name = self.config.get('template_name', '-One-to-One - Template')
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Keyboard Maestro client initialized")
    
    def create_colleague_macro(self, colleague_name: str, slack_handle: str) -> Tuple[bool, Optional[str]]:
        """
        Create a new Keyboard Maestro macro for a colleague by exporting, modifying, and creating import file.
        
        Args:
            colleague_name: Full name of the colleague
            slack_handle: Slack handle (without @)
            
        Returns:
            Tuple of (success_status, macro_uuid): 
            - success_status: True if successful, False otherwise
            - macro_uuid: The generated macro UUID if successful, None if failed
        """
        try:
            self.logger.info(f"Creating Keyboard Maestro macro for {colleague_name}")
            
            # Step 1: Get template macro XML
            template_xml = self._get_macro_xml(self.template_uuid)
            if not template_xml:
                self.logger.error("Failed to get template macro XML")
                return (False, None)
            
            # Step 2: Create modified macro XML with colleague data
            modified_xml, macro_uuid = self._create_modified_macro_xml(template_xml, colleague_name)
            if not modified_xml or not macro_uuid:
                self.logger.error("Failed to create modified macro XML")
                return (False, None)
            
            # Step 3: Create importable .kmmacros file
            kmmacros_file = self._create_kmmacros_file(modified_xml, colleague_name)
            if not kmmacros_file:
                self.logger.error("Failed to create .kmmacros file")
                return (False, None)
            
            # Step 4: Provide user instructions
            self._show_import_instructions(kmmacros_file, colleague_name)
            
            self.logger.info(f"✅ Created Keyboard Maestro macro: One-to-One - {colleague_name}")
            self.logger.debug(f"Generated macro UUID: {macro_uuid}")
            return (True, macro_uuid)
            
        except Exception as e:
            self.logger.error(f"Failed to create Keyboard Maestro macro: {e}")
            return (False, None)
    
    
    
    
    
    
    
    def _get_macro_xml(self, macro_uuid: str) -> Optional[str]:
        """
        Get the XML representation of a macro by its UUID.
        
        Args:
            macro_uuid: UUID of the macro to retrieve
            
        Returns:
            XML string of the macro, or None if failed
        """
        try:
            applescript = f'''
            tell application "Keyboard Maestro"
                get xml of macro id "{macro_uuid}"
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                self.logger.error(f"Failed to get macro XML: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting macro XML: {e}")
            return None
    
    
    
    
    
    def _create_modified_macro_xml(self, template_xml: str, colleague_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create modified macro XML with colleague data and custom icon.
        
        Args:
            template_xml: Original template macro XML
            colleague_name: Name of the colleague for placeholder replacement
            
        Returns:
            Tuple of (modified_xml, macro_uuid): 
            - modified_xml: Modified XML content, or None if failed
            - macro_uuid: The generated macro UUID, or None if failed
        """
        try:
            # Parse the template XML
            plist_data = plistlib.loads(template_xml.encode())
            
            # Update macro name
            plist_data['Name'] = f"One-to-One - {colleague_name}"
            
            # Generate new UUID for the macro
            macro_uuid = str(uuid.uuid4()).upper()
            plist_data['UID'] = macro_uuid
            
            # Update creation and modification dates
            current_time = time.time() + 978307200  # Convert to Apple's timestamp format
            plist_data['ModificationDate'] = current_time
            
            # Replace placeholders in action parameters
            self._replace_placeholders_in_actions(plist_data.get('Actions', []), colleague_name)
            
            # Update custom icon with colleague's profile photo
            icon_data = self._get_tiff_icon_data(colleague_name)
            if icon_data:
                plist_data['CustomIconData'] = icon_data
                self.logger.debug("Updated macro with custom icon")
            else:
                self.logger.warning("Failed to get custom icon data, keeping template icon")
            
            # Convert back to XML and return both XML and UUID
            modified_xml = plistlib.dumps(plist_data, fmt=plistlib.FMT_XML).decode()
            return (modified_xml, macro_uuid)
            
        except Exception as e:
            self.logger.error(f"Error creating modified macro XML: {e}")
            return (None, None)
    
    def _replace_placeholders_in_actions(self, actions: list, colleague_name: str):
        """
        Replace placeholders in macro action parameters.
        
        Args:
            actions: List of action dictionaries from the macro
            colleague_name: Name of the colleague for replacement
        """
        try:
            for action in actions:
                if action.get('MacroActionType') == 'ExecuteSubroutine':
                    parameters = action.get('Parameters', [])
                    for i, param in enumerate(parameters):
                        if param == '#obsidianNoteName':
                            parameters[i] = colleague_name
                        elif param == '#ofPerspectiveName':
                            parameters[i] = colleague_name
                    self.logger.debug(f"Replaced placeholders in ExecuteSubroutine action")
                    
        except Exception as e:
            self.logger.error(f"Error replacing placeholders: {e}")
    
    def _get_tiff_icon_data(self, colleague_name: str) -> Optional[bytes]:
        """
        Get colleague's profile photo as base64-encoded TIFF data for CustomIconData.
        
        Args:
            colleague_name: Name of the colleague
            
        Returns:
            Base64 encoded TIFF data as bytes, or None if failed
        """
        try:
            photo_path = self.output_manager.get_photo_path(colleague_name)
            if not os.path.exists(photo_path):
                self.logger.warning(f"Profile photo not found at {photo_path}")
                return None
            
            # Convert to 32x32 TIFF using sips
            temp_tiff = '/tmp/km_icon_temp.tiff'
            result = subprocess.run(
                ['sips', '-s', 'format', 'tiff', '-Z', '32', photo_path, '--out', temp_tiff],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.warning(f"Failed to convert image to TIFF: {result.stderr}")
                return None
            
            # Read TIFF file as bytes (not base64 - plistlib will handle encoding)
            with open(temp_tiff, 'rb') as f:
                tiff_data = f.read()
            
            # Clean up temp file
            if os.path.exists(temp_tiff):
                os.remove(temp_tiff)
            
            self.logger.debug(f"Generated {len(tiff_data)} bytes of TIFF icon data")
            return tiff_data
            
        except Exception as e:
            self.logger.error(f"Error generating TIFF icon data: {e}")
            return None
    
    def _create_kmmacros_file(self, macro_xml: str, colleague_name: str) -> Optional[str]:
        """
        Create a .kmmacros file with the modified macro for import.
        
        Args:
            macro_xml: Modified macro XML content
            colleague_name: Name of the colleague (for filename)
            
        Returns:
            Path to the created .kmmacros file, or None if failed
        """
        try:
            # Parse the macro XML
            macro_data = plistlib.loads(macro_xml.encode())
            
            # Create the .kmmacros structure (array with macro group)
            kmmacros_data = [{
                "Activate": "Normal",
                "CreationDate": macro_data.get('CreationDate', 779903114.89810801),
                "CustomIconData": macro_data.get('CustomIconData', b''),  # Group icon (can be empty)
                "Macros": [macro_data],  # Array containing our macro
                "Name": "HS - One-to-one",  # Same group as template
                "ToggleMacroUID": "D2D3351C-E5E6-4593-AF0C-F7A8213419EE",  # Same as template
                "UID": "1ED018E5-412D-44C8-B02C-8C0A6619AF5B"  # Same group UID as template
            }]
            
            # Generate output path
            safe_name = colleague_name.replace(' ', '_').replace('/', '_')
            output_file = self.output_manager.get_colleague_folder(colleague_name)
            kmmacros_path = os.path.join(output_file, f"One-to-One - {safe_name}.kmmacros")
            
            # Write as plist
            with open(kmmacros_path, 'wb') as f:
                plistlib.dump(kmmacros_data, f, fmt=plistlib.FMT_XML)
            
            self.logger.info(f"Created .kmmacros file: {kmmacros_path}")
            return kmmacros_path
            
        except Exception as e:
            self.logger.error(f"Error creating .kmmacros file: {e}")
            return None
    
    def _show_import_instructions(self, kmmacros_file: str, colleague_name: str):
        """
        Display instructions for importing the macro into Keyboard Maestro.
        
        Args:
            kmmacros_file: Path to the .kmmacros file
            colleague_name: Name of the colleague
        """
        try:
            self.logger.info("")
            self.logger.info("📋 KEYBOARD MAESTRO MACRO READY:")
            self.logger.info(f"   Macro file: {os.path.basename(kmmacros_file)}")
            self.logger.info(f"   Macro name: One-to-One - {colleague_name}")
            self.logger.info("")
            self.logger.info("🔄 TO IMPORT INTO KEYBOARD MAESTRO:")
            self.logger.info("   1. Open Finder and navigate to the macro file")
            self.logger.info("   2. Double-click the .kmmacros file")
            self.logger.info("   3. Keyboard Maestro will open and import automatically")
            self.logger.info("   4. The macro will be added to the 'HS - One-to-one' group")
            self.logger.info("")
            self.logger.info("✨ FEATURES:")
            self.logger.info("   • Custom icon from colleague's profile photo")
            self.logger.info("   • Parameters automatically replaced")
            self.logger.info("   • Ready to use immediately after import")
            
        except Exception as e:
            self.logger.error(f"Error showing import instructions: {e}")
    
    def get_macro_file_path(self, colleague_name: str) -> str:
        """
        Get the path to the colleague's .kmmacros file for later import.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Path to the .kmmacros file
        """
        safe_name = colleague_name.replace(' ', '_').replace('/', '_')
        colleague_folder = self.output_manager.get_colleague_folder(colleague_name)
        return os.path.join(colleague_folder, f"One-to-One - {safe_name}.kmmacros")
    
    def import_and_open_macro(self, colleague_name: str) -> bool:
        """
        Import the Keyboard Maestro macro and open it (final step).
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the macro file path
            kmmacros_file = self.get_macro_file_path(colleague_name)
            
            if not os.path.exists(kmmacros_file):
                self.logger.warning(f"Macro file not found: {kmmacros_file}")
                return False
            
            self.logger.info("")
            self.logger.info("🚀 FINAL STEP: Importing and opening Keyboard Maestro macro...")
            
            # Step 1: Automatically import the macro by opening the .kmmacros file
            self.logger.info("📥 Auto-importing macro into Keyboard Maestro...")
            subprocess.run(['open', kmmacros_file], timeout=10, check=True)
            
            # Give Keyboard Maestro a moment to import the macro
            import time
            time.sleep(2)
            
            # Step 2: Open Keyboard Maestro to show the imported macro
            self.logger.info("🎯 Opening Keyboard Maestro...")
            subprocess.run(['open', '-a', 'Keyboard Maestro'], timeout=5, check=True)
            
            self.logger.info("✅ Macro imported and Keyboard Maestro opened successfully!")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.warning("⚠️  Timeout while importing macro - Keyboard Maestro may be slow to respond")
            self._show_manual_macro_instructions(colleague_name)
            return False
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"⚠️  Failed to auto-import macro: {e}")
            self._show_manual_macro_instructions(colleague_name)
            return False
        except Exception as e:
            self.logger.warning(f"⚠️  Error during macro import: {e}")
            self._show_manual_macro_instructions(colleague_name)
            return False
    
    def _show_manual_macro_instructions(self, colleague_name: str) -> None:
        """Show manual import instructions as fallback."""
        try:
            kmmacros_file = self.get_macro_file_path(colleague_name)
            self.logger.info("")
            self.logger.info("📋 MANUAL MACRO IMPORT INSTRUCTIONS:")
            self.logger.info("   1. Open Finder and navigate to the macro file")
            self.logger.info(f"   2. Double-click the '{os.path.basename(kmmacros_file)}' file")
            self.logger.info("   3. Keyboard Maestro will open and import automatically")
            self.logger.info(f"   4. The macro 'One-to-One - {colleague_name}' will be added to the group")
        except Exception as e:
            self.logger.debug(f"Could not show macro instructions: {e}")
    
    
