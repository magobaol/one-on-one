"""
Stream Deck Integration Client

This module provides integration with Elgato Stream Deck by automatically generating
colleague-specific action files that can be imported via double-click.

The implementation follows an export/modify/import approach similar to our successful
Keyboard Maestro and OmniFocus integrations:

1. Use a template .streamDeckAction file as the base
2. Parse the ZIP structure and JSON manifests
3. Replace Keyboard Maestro macro UUID with the generated colleague macro UUID
4. Update action labels and titles with colleague information
5. Convert profile photo to Stream Deck format (288x288 PNG)
6. Generate new image UUIDs and update references
7. Create a new .streamDeckAction ZIP file for import

Key Features:
- Template-based action generation for consistency
- Automatic UUID chaining with Keyboard Maestro macros
- Custom icon integration using colleague profile photos
- Proper ZIP packaging following Stream Deck format
- Double-click import workflow for user convenience
"""

import json
import logging
import os
import uuid
import zipfile
import tempfile
import shutil
from typing import Dict, Any, Optional, Tuple
from PIL import Image
from lib.output_manager import OutputManager


class StreamDeckClient:
    """
    Client for integrating with Elgato Stream Deck.
    
    This class handles:
    - Parsing template .streamDeckAction files
    - Generating colleague-specific action configurations
    - Converting profile photos to Stream Deck icon format (288x288 PNG)
    - Creating importable .streamDeckAction files with proper ZIP structure
    - Linking actions to Keyboard Maestro macros via UUID
    """
    
    def __init__(self, config: Dict[str, Any], output_manager: OutputManager):
        """
        Initialize Stream Deck client with fixed template and output manager.
        
        Args:
            config: Dictionary containing configuration (Stream Deck uses fixed settings)
            output_manager: OutputManager instance for accessing colleague files and output paths
        """
        self.config = config.get('stream_deck', {})
        self.grid_position = '0,0'  # Fixed position for standardized placement
        self.output_manager = output_manager
        
        # Use fixed template path from resources directory
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.template_path = os.path.join(script_dir, 'resources', 'streamDeckButton.streamDeckAction')
        
        self.logger = logging.getLogger(__name__)
        
        if not os.path.isfile(self.template_path):
            raise FileNotFoundError(f"Stream Deck template file not found at: {self.template_path}")
        
        self.logger.info(f"Stream Deck client initialized with template: {os.path.basename(self.template_path)}")
    
    def create_colleague_action(self, colleague_name: str, km_macro_uuid: str) -> bool:
        """
        Create a new Stream Deck action for a colleague that links to their Keyboard Maestro macro.
        
        Args:
            colleague_name: Full name of the colleague
            km_macro_uuid: UUID of the colleague's Keyboard Maestro macro
            
        Returns:
            True if action was created successfully, False otherwise
        """
        try:
            self.logger.info(f"Creating Stream Deck action for {colleague_name}")
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Step 1: Extract template action
                template_data = self._extract_template(temp_dir)
                if not template_data:
                    return False
                
                # Step 2: Modify action configuration
                modified_data = self._modify_action_config(
                    template_data, colleague_name, km_macro_uuid, temp_dir
                )
                if not modified_data:
                    return False
                
                # Step 3: Create colleague-specific icon
                icon_path = self._create_colleague_icon(colleague_name, temp_dir)
                if not icon_path:
                    return False
                
                # Step 4: Update image references
                self._update_image_references(modified_data, icon_path, temp_dir)
                
                # Step 5: Create final .streamDeckAction file
                action_file = self._create_action_file(modified_data, colleague_name, temp_dir)
                if not action_file:
                    return False
                
                self._show_import_instructions(action_file, colleague_name)
            
            self.logger.info(f"✅ Created Stream Deck action: One-to-One - {colleague_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Stream Deck action for {colleague_name}: {e}")
            return False
    
    def _extract_template(self, temp_dir: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse the template .streamDeckAction file.
        
        Args:
            temp_dir: Temporary directory for extraction
            
        Returns:
            Dictionary containing the extracted template data structure, or None if failed
        """
        try:
            self.logger.debug("Extracting template Stream Deck action")
            
            # Extract the ZIP file
            template_extract_dir = os.path.join(temp_dir, "template")
            with zipfile.ZipFile(self.template_path, 'r') as zip_ref:
                zip_ref.extractall(template_extract_dir)
            
            # Find the .sdProfile directory
            profile_dirs = [d for d in os.listdir(template_extract_dir) if d.endswith('.sdProfile')]
            if not profile_dirs:
                self.logger.error("No .sdProfile directory found in template")
                return None
            
            profile_dir = os.path.join(template_extract_dir, profile_dirs[0])
            
            # Read main manifest
            main_manifest_path = os.path.join(profile_dir, 'manifest.json')
            with open(main_manifest_path, 'r', encoding='utf-8') as f:
                main_manifest = json.load(f)
            
            # Find profiles with actions
            profiles_dir = os.path.join(profile_dir, 'Profiles')
            action_profiles = []
            
            if os.path.exists(profiles_dir):
                for profile_uuid in os.listdir(profiles_dir):
                    profile_path = os.path.join(profiles_dir, profile_uuid)
                    if not os.path.isdir(profile_path):
                        continue
                    
                    manifest_path = os.path.join(profile_path, 'manifest.json')
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            profile_manifest = json.load(f)
                        
                        # Check if this profile has actions
                        for controller in profile_manifest.get('Controllers', []):
                            if controller.get('Actions'):
                                action_profiles.append({
                                    'uuid': profile_uuid,
                                    'path': profile_path,
                                    'manifest': profile_manifest
                                })
                                break
            
            if not action_profiles:
                self.logger.error("No profiles with actions found in template")
                return None
            
            return {
                'extract_dir': template_extract_dir,
                'profile_dir': profile_dir,
                'profile_name': profile_dirs[0],
                'main_manifest': main_manifest,
                'action_profiles': action_profiles
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract template: {e}")
            return None
    
    def _modify_action_config(
        self, 
        template_data: Dict[str, Any], 
        colleague_name: str, 
        km_macro_uuid: str,
        temp_dir: str
    ) -> Optional[Dict[str, Any]]:
        """
        Modify the action configuration with colleague-specific data.
        
        Args:
            template_data: Extracted template data
            colleague_name: Name of the colleague
            km_macro_uuid: UUID of the Keyboard Maestro macro to link to
            temp_dir: Temporary directory for processing
            
        Returns:
            Modified template data, or None if failed
        """
        try:
            self.logger.debug(f"Modifying action config for {colleague_name}")
            
            # Work with the first action profile (template should have one main profile)
            action_profile = template_data['action_profiles'][0]
            manifest = action_profile['manifest'].copy()
            
            # Find and modify the first action
            for controller in manifest.get('Controllers', []):
                actions = controller.get('Actions')
                if not actions:
                    continue
                
                # Get the first action (assuming template has one action)
                first_action_key = next(iter(actions.keys()))
                action = actions[first_action_key]
                
                # Update the action settings
                if 'Settings' in action:
                    # Update the label (display name)
                    action['Settings']['label'] = f"One-to-One - {colleague_name}"
                    
                    # Update the Keyboard Maestro macro UUID
                    action['Settings']['uid'] = km_macro_uuid
                
                # Update the action states (button appearance)
                if 'States' in action:
                    for state in action['States']:
                        # Update the title
                        state['Title'] = colleague_name
                        
                        # We'll update the image reference later
                        # For now, just note that we need to replace it
                        state['_needs_image_update'] = True
                
                self.logger.debug(f"Updated action config: KM UUID = {km_macro_uuid}")
                break
            
            # Update the modified manifest in the template data
            action_profile['manifest'] = manifest
            
            return template_data
            
        except Exception as e:
            self.logger.error(f"Failed to modify action config: {e}")
            return None
    
    def _create_colleague_icon(self, colleague_name: str, temp_dir: str) -> Optional[str]:
        """
        Create a Stream Deck format icon (288x288 PNG) from the colleague's profile photo.
        
        Args:
            colleague_name: Name of the colleague
            temp_dir: Temporary directory for processing
            
        Returns:
            Path to the created icon file, or None if failed
        """
        try:
            self.logger.debug(f"Creating Stream Deck icon for {colleague_name}")
            
            # Get the source profile photo
            source_photo = self.output_manager.get_photo_path(colleague_name)
            if not os.path.exists(source_photo):
                self.logger.error(f"Profile photo not found: {source_photo}")
                return None
            
            # Convert to Stream Deck format (288x288 PNG)
            with Image.open(source_photo) as img:
                # Convert to RGB if necessary (in case of RGBA or other formats)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to 288x288 (Stream Deck button size)
                img_resized = img.resize((288, 288), Image.LANCZOS)
                
                # Save as PNG in temp directory
                icon_filename = f"{colleague_name.replace(' ', '_').replace('/', '_')}.png"
                icon_path = os.path.join(temp_dir, icon_filename)
                img_resized.save(icon_path, 'PNG', optimize=True)
                
                self.logger.debug(f"Created Stream Deck icon: {icon_path}")
                return icon_path
                
        except Exception as e:
            self.logger.error(f"Failed to create colleague icon: {e}")
            return None
    
    def _update_image_references(
        self, 
        template_data: Dict[str, Any], 
        icon_path: str, 
        temp_dir: str
    ) -> None:
        """
        Update image references in the action configuration and copy icon to proper location.
        
        Args:
            template_data: Modified template data
            icon_path: Path to the colleague's icon file
            temp_dir: Temporary directory for processing
        """
        try:
            self.logger.debug("Updating image references")
            
            # Generate a new image UUID
            new_image_uuid = str(uuid.uuid4()).replace('-', '').upper()
            new_image_filename = f"{new_image_uuid}.png"
            
            # Work with the action profile
            action_profile = template_data['action_profiles'][0]
            manifest = action_profile['manifest']
            
            # Update action states to reference the new image
            for controller in manifest.get('Controllers', []):
                actions = controller.get('Actions')
                if not actions:
                    continue
                
                for action_key, action in actions.items():
                    if 'States' in action:
                        for state in action['States']:
                            if state.get('_needs_image_update'):
                                # Update image reference
                                state['Image'] = f"Images/{new_image_filename}"
                                # Remove the temporary flag
                                del state['_needs_image_update']
            
            # Copy the icon to the Images directory in the profile
            images_dir = os.path.join(action_profile['path'], 'Images')
            os.makedirs(images_dir, exist_ok=True)
            
            dest_icon_path = os.path.join(images_dir, new_image_filename)
            shutil.copy2(icon_path, dest_icon_path)
            
            self.logger.debug(f"Updated image reference to: Images/{new_image_filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to update image references: {e}")
    
    def _create_action_file(
        self, 
        template_data: Dict[str, Any], 
        colleague_name: str, 
        temp_dir: str
    ) -> Optional[str]:
        """
        Create the final .streamDeckAction ZIP file.
        
        Args:
            template_data: Modified template data
            colleague_name: Name of the colleague
            temp_dir: Temporary directory for processing
            
        Returns:
            Path to the created .streamDeckAction file, or None if failed
        """
        try:
            self.logger.debug(f"Creating .streamDeckAction file for {colleague_name}")
            
            # Save modified manifests back to the extracted directory
            action_profile = template_data['action_profiles'][0]
            manifest_path = os.path.join(action_profile['path'], 'manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(action_profile['manifest'], f, separators=(',', ':'))
            
            # Create the output .streamDeckAction file
            safe_name = colleague_name.replace(' ', '_').replace('/', '_')
            colleague_folder = self.output_manager.get_colleague_folder(colleague_name)
            action_filename = f"One-to-One - {safe_name}.streamDeckAction"
            action_file_path = os.path.join(colleague_folder, action_filename)
            
            # Create ZIP archive with the proper structure
            with zipfile.ZipFile(action_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from the profile directory
                profile_dir = template_data['profile_dir']
                for root, dirs, files in os.walk(profile_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate archive path relative to profile_dir parent
                        arcname = os.path.relpath(file_path, os.path.dirname(profile_dir))
                        zipf.write(file_path, arcname)
            
            self.logger.info(f"Created Stream Deck action file: {action_file_path}")
            return action_file_path
            
        except Exception as e:
            self.logger.error(f"Failed to create .streamDeckAction file: {e}")
            return None
    
    def _show_import_instructions(self, action_file: str, colleague_name: str) -> None:
        """
        Show instructions to the user for importing the Stream Deck action.
        
        Args:
            action_file: Path to the created .streamDeckAction file
            colleague_name: Name of the colleague
        """
        self.logger.info(f"📱 Stream Deck Action Ready: {os.path.basename(action_file)}")
        self.logger.info(f"📁 To import: Double-click the .streamDeckAction file")
        self.logger.info(f"🔗 The action will trigger the Keyboard Maestro macro for {colleague_name}")
        self.logger.info(f"💡 Make sure to import the corresponding .kmmacros file first!")
