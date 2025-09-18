"""
Obsidian Integration Client

This module handles creating colleague notes and managing photos within an Obsidian vault.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from .output_manager import OutputManager


class ObsidianClient:
    """
    Client for integrating with Obsidian vaults.
    
    This class handles:
    - Creating colleague notes in the vault
    - Copying profile photos to person folders
    - Managing folder structure within the vault
    """
    
    def __init__(self, config: Dict[str, Any], output_manager: OutputManager):
        """
        Initialize Obsidian client with configuration.
        
        Args:
            config: Dictionary containing Obsidian configuration
            output_manager: OutputManager instance for accessing photos
        """
        self.config = config.get('obsidian', {})
        self.output_manager = output_manager
        
        # Vault configuration
        self.vault_path = os.path.expanduser(self.config.get('vault_path', ''))
        self.people_folder = self.config.get('people_folder', '80 Spaces/people')
        
        self.logger = logging.getLogger(__name__)
        
        # Validate vault path
        if not self.vault_path:
            raise ValueError("Obsidian vault_path is required in configuration")
        if not os.path.exists(self.vault_path):
            raise ValueError(f"Obsidian vault not found at: {self.vault_path}")
            
        self.logger.info(f"Obsidian client initialized: {self.vault_path}")
    
    def create_colleague_note(self, colleague_name: str, slack_handle: str) -> bool:
        """
        Create a note and copy photo for a colleague in the Obsidian vault.
        
        Args:
            colleague_name: Full name of the colleague
            slack_handle: Slack username (without @)
            
        Returns:
            True if note was created successfully, False otherwise
        """
        try:
            self.logger.info(f"Creating Obsidian note for {colleague_name}")
            
            # Create person folder
            person_folder = self._get_person_folder_path(colleague_name)
            self._ensure_folder_exists(person_folder)
            
            # Copy photo to person folder
            photo_success = self._copy_photo_to_vault(colleague_name, person_folder)
            if not photo_success:
                self.logger.warning("Failed to copy photo, continuing with note creation...")
            
            # Create the note
            note_success = self._create_note_file(colleague_name, person_folder)
            
            if note_success:
                self.logger.info(f"✅ Created Obsidian note: {colleague_name}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to create Obsidian note for {colleague_name}: {e}")
            return False
    
    def _get_person_folder_path(self, colleague_name: str) -> str:
        """Get the full path to a person's folder within the vault."""
        return os.path.join(self.vault_path, self.people_folder, colleague_name)
    
    def _ensure_folder_exists(self, folder_path: str) -> None:
        """Ensure a folder exists, creating it if necessary."""
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.logger.debug(f"Ensured folder exists: {folder_path}")
        except Exception as e:
            self.logger.error(f"Failed to create folder {folder_path}: {e}")
            raise
    
    def _copy_photo_to_vault(self, colleague_name: str, person_folder: str) -> bool:
        """
        Copy the colleague's profile photo to their person folder in the vault.
        
        Args:
            colleague_name: Full name of the colleague
            person_folder: Path to the person's folder in the vault
            
        Returns:
            True if photo was copied successfully, False otherwise
        """
        try:
            # Get source photo path from output manager
            source_photo = self.output_manager.get_photo_path(colleague_name)
            
            if not os.path.exists(source_photo):
                self.logger.warning(f"Source photo not found: {source_photo}")
                return False
            
            # Create destination path
            photo_filename = f"{colleague_name}.jpg"
            dest_photo = os.path.join(person_folder, photo_filename)
            
            # Copy the photo
            shutil.copy2(source_photo, dest_photo)
            self.logger.debug(f"Copied photo: {source_photo} -> {dest_photo}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy photo for {colleague_name}: {e}")
            return False
    
    def _create_note_file(self, colleague_name: str, person_folder: str) -> bool:
        """
        Create the Markdown note file for the colleague.
        
        Args:
            colleague_name: Full name of the colleague
            person_folder: Path to the person's folder in the vault
            
        Returns:
            True if note was created successfully, False otherwise
        """
        try:
            # Generate note filename (handle conflicts)
            note_filename = self._get_unique_note_filename(colleague_name, person_folder)
            note_path = os.path.join(person_folder, note_filename)
            
            # Create note content
            photo_link = f"![[{colleague_name}.jpg|200]]"
            note_content = f"# {colleague_name}\n\n{photo_link}\n"
            
            # Write the note
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
            
            self.logger.debug(f"Created note: {note_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create note file for {colleague_name}: {e}")
            return False
    
    def _get_unique_note_filename(self, colleague_name: str, person_folder: str) -> str:
        """
        Get a unique filename for the note, handling conflicts by appending (1), (2), etc.
        
        Args:
            colleague_name: Full name of the colleague
            person_folder: Path to the person's folder in the vault
            
        Returns:
            Unique filename for the note
        """
        base_filename = f"{colleague_name}.md"
        note_path = os.path.join(person_folder, base_filename)
        
        # If file doesn't exist, use the base name
        if not os.path.exists(note_path):
            return base_filename
        
        # Find next available number
        counter = 1
        while True:
            numbered_filename = f"{colleague_name} ({counter}).md"
            numbered_path = os.path.join(person_folder, numbered_filename)
            
            if not os.path.exists(numbered_path):
                self.logger.info(f"Note already exists, using: {numbered_filename}")
                return numbered_filename
                
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 100:
                raise ValueError(f"Too many existing notes for {colleague_name}")
    
    def get_vault_info(self) -> Dict[str, Any]:
        """
        Get information about the vault configuration.
        
        Returns:
            Dictionary with vault information
        """
        return {
            'vault_path': self.vault_path,
            'people_folder': self.people_folder,
            'full_people_path': os.path.join(self.vault_path, self.people_folder),
            'vault_exists': os.path.exists(self.vault_path)
        }
