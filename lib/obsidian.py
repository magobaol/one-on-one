"""
Obsidian Integration Client

This module handles creating colleague notes and managing photos within an Obsidian vault.
"""

import os
import logging
import shutil
import subprocess
import urllib.parse
from typing import Dict, Any
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
        self.logger = logging.getLogger(__name__)
        
        # Vault configuration
        self.vault_path = os.path.expanduser(self.config.get('vault_path', ''))
        self.people_folder = self.config.get('people_folder', '80 Spaces/people')
        
        # Extract vault name from path for URI
        self.vault_name = os.path.basename(self.vault_path)
        
        # Validate vault path
        if not self.vault_path:
            raise ValueError("Obsidian vault_path is required in configuration")
        if not os.path.exists(self.vault_path):
            raise ValueError(f"Obsidian vault not found at: {self.vault_path}")
            
        self.logger.info(f"Obsidian client initialized: {self.vault_path}")
    
    def create_colleague_note(self, colleague_name: str, slack_handle: str) -> bool:
        """
        Create a note and copy photo for a colleague using Obsidian URI.
        
        Args:
            colleague_name: Full name of the colleague
            slack_handle: Slack username (without @)
            
        Returns:
            True if note was created successfully, False otherwise
        """
        try:
            self.logger.info(f"Creating Obsidian note for {colleague_name}")
            
            # Create person folder and copy photo
            person_folder = self._get_person_folder_path(colleague_name)
            self._ensure_folder_exists(person_folder)
            
            photo_success = self._copy_photo_to_vault(colleague_name, person_folder)
            if not photo_success:
                self.logger.warning("Failed to copy photo, continuing with note creation...")
            
            # Create note using Obsidian URI
            note_success = self._create_note_via_uri(colleague_name, slack_handle)
            
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
    
    def _create_note_via_uri(self, colleague_name: str, slack_handle: str) -> bool:
        """
        Create a note using Obsidian URI, which handles duplicates and opens the note automatically.
        
        Args:
            colleague_name: Full name of the colleague
            slack_handle: Slack username (without @)
            
        Returns:
            True if note was created successfully, False otherwise
        """
        try:
            # Construct note path within vault - encode everything including slashes for 'file' parameter
            raw_note_path = f"{self.people_folder}/{colleague_name}/{colleague_name}"
            
            # Encode everything including slashes for the 'file' parameter
            encoded_note_path = urllib.parse.quote(raw_note_path, safe='')
            
            # Create note content
            note_content = self._generate_note_content(colleague_name, slack_handle)
            
            # Properly encode other URI parameters
            encoded_vault = urllib.parse.quote(self.vault_name)
            encoded_content = urllib.parse.quote(note_content)
            
            # Construct Obsidian URI with 'file' parameter and fully encoded path
            obsidian_uri = f"obsidian://new?vault={encoded_vault}&file={encoded_note_path}&content={encoded_content}"
            
            self.logger.debug(f"Opening Obsidian URI for note: {colleague_name}")
            
            # Open the URI (this will create and open the note in Obsidian)
            subprocess.run(['open', obsidian_uri], timeout=10, check=True)
            
            self.logger.debug(f"Note created via Obsidian URI")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout while opening Obsidian URI")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to open Obsidian URI: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating note via URI: {e}")
            return False
    
    def _generate_note_content(self, colleague_name: str, slack_handle: str) -> str:
        """
        Generate the same simple note content as before.
        
        Args:
            colleague_name: Full name of the colleague
            slack_handle: Slack username (without @) - unused but kept for compatibility
            
        Returns:
            Simple note content as markdown (same as original)
        """
        # Create the same simple content as the original implementation
        photo_link = f"![[{colleague_name}.jpg|200]]"
        note_content = f"# {colleague_name}\n\n{photo_link}\n"
        
        return note_content
    
