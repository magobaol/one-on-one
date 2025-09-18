"""
Output Manager for One-on-One Automation

Manages the organized folder structure for colleague-specific files.
Creates a base folder with subfolders for each colleague containing
all their related files (photos, perspectives, notes, etc.).
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any


class OutputManager:
    """Manages organized output folder structure for colleague files."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output manager with configuration.
        
        Args:
            config: Configuration dictionary with output settings
        """
        self.config = config.get('output', {})
        self.base_folder = os.path.expanduser(self.config.get('base_folder', '.output'))
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Output manager initialized: {self.base_folder}")
    
    def get_colleague_folder(self, colleague_name: str) -> str:
        """
        Get the folder path for a specific colleague, creating it if needed.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Path to the colleague's folder
        """
        # Sanitize colleague name for folder use
        safe_name = self._sanitize_folder_name(colleague_name)
        colleague_folder = os.path.join(self.base_folder, safe_name)
        
        # Create the folder structure if it doesn't exist
        self._ensure_folder_exists(colleague_folder)
        
        return colleague_folder
    
    def get_photo_path(self, colleague_name: str) -> str:
        """
        Get the path where the colleague's profile photo should be saved.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Full path to the profile photo file
        """
        colleague_folder = self.get_colleague_folder(colleague_name)
        return os.path.join(colleague_folder, "profile_photo.jpg")
    
    def get_perspective_folder(self, colleague_name: str) -> str:
        """
        Get the path where the colleague's perspective should be saved.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Full path to the perspective folder
        """
        colleague_folder = self.get_colleague_folder(colleague_name)
        safe_name = self._sanitize_folder_name(colleague_name)
        perspective_folder = os.path.join(colleague_folder, f"{safe_name}.ofocus-perspective")
        
        # Create the perspective folder
        self._ensure_folder_exists(perspective_folder)
        
        return perspective_folder
    
    def get_perspective_plist_path(self, colleague_name: str) -> str:
        """
        Get the full path to the colleague's perspective plist file.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Full path to the Info-v3.plist file
        """
        perspective_folder = self.get_perspective_folder(colleague_name)
        return os.path.join(perspective_folder, "Info-v3.plist")
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize a name for use as a folder name.
        
        Args:
            name: Original name
            
        Returns:
            Sanitized folder name
        """
        # Replace spaces and special characters with underscores
        safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        return safe_name.strip('_')
    
    def _ensure_folder_exists(self, folder_path: str) -> None:
        """
        Ensure a folder exists, creating it if necessary.
        
        Args:
            folder_path: Path to the folder
        """
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.logger.debug(f"Ensured folder exists: {folder_path}")
        except Exception as e:
            self.logger.error(f"Failed to create folder {folder_path}: {e}")
            raise
    
    def list_colleagues(self) -> list:
        """
        List all colleagues that have folders in the output directory.
        
        Returns:
            List of colleague folder names
        """
        try:
            if not os.path.exists(self.base_folder):
                return []
            
            colleagues = []
            for item in os.listdir(self.base_folder):
                item_path = os.path.join(self.base_folder, item)
                if os.path.isdir(item_path):
                    colleagues.append(item)
            
            return sorted(colleagues)
            
        except Exception as e:
            self.logger.warning(f"Failed to list colleagues: {e}")
            return []
    
    def get_colleague_files(self, colleague_name: str) -> Dict[str, str]:
        """
        Get paths to all files for a colleague.
        
        Args:
            colleague_name: Full name of the colleague
            
        Returns:
            Dictionary with file types and their paths
        """
        colleague_folder = self.get_colleague_folder(colleague_name)
        
        files = {
            'folder': colleague_folder,
            'photo': self.get_photo_path(colleague_name),
            'perspective_folder': self.get_perspective_folder(colleague_name),
            'perspective_plist': self.get_perspective_plist_path(colleague_name)
        }
        
        # Check which files actually exist
        for file_type, file_path in files.items():
            if file_type != 'folder' and os.path.exists(file_path):
                files[f'{file_type}_exists'] = True
            else:
                files[f'{file_type}_exists'] = False
        
        return files
