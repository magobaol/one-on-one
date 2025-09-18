"""
Photo Management Client

This module handles the downloading, storage, and management of profile photos
from Slack.
"""

import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .slack import SlackClient
from .output_manager import OutputManager
from .utils import ensure_directory_exists, get_file_size


class PhotoManager:
    """
    Client for managing profile photo downloads and storage.
    
    This class handles:
    - Downloading photos from URLs
    - File naming and organization
    - Storage path management
    - Error handling for network operations
    """
    
    def __init__(self, config: Dict[str, Any], output_manager: OutputManager):
        """
        Initialize photo manager with configuration and output manager.
        
        Args:
            config: Dictionary containing photo configuration
            output_manager: OutputManager instance for organized file storage
        """
        self.config = config
        self.output_manager = output_manager
        self.slack_config = config.get('slack', {})
        self.photo_size = self.slack_config.get('photo_size', '512')
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Photo manager initialized with organized output structure")
    
    def download_from_slack(self, slack_client: SlackClient, name: str, slack_handle: str) -> bool:
        """
        Download a colleague's profile photo from Slack.
        
        Args:
            slack_client: Initialized Slack client
            name: Colleague's full name
            slack_handle: Slack username (without @)
            
        Returns:
            True if photo was downloaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Downloading profile photo for {name} (@{slack_handle})")
            
            # Get user info from Slack
            user_info = slack_client.get_user_info(slack_handle)
            if not user_info:
                self.logger.error(f"Could not find user @{slack_handle} in Slack")
                return False
            
            # Get photo URL
            photo_url = slack_client.get_photo_url(user_info, self.photo_size)
            if not photo_url:
                self.logger.error(f"Could not get photo URL for @{slack_handle}")
                return False
            
            # Get organized save path from output manager
            save_path = Path(self.output_manager.get_photo_path(name))
            
            # Download the photo
            success = self.download_photo(photo_url, save_path)
            
            if success:
                self.logger.info(f"Profile photo for {name} saved to: {save_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error downloading photo for {name}: {e}")
            return False
    
    def download_photo(self, photo_url: str, save_path: Path) -> bool:
        """
        Download a photo from a URL and save it to disk.
        
        Args:
            photo_url: URL of the photo to download
            save_path: Path where to save the photo
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Downloading photo from URL")
            self.logger.debug(f"URL: {photo_url}")
            self.logger.debug(f"Save path: {save_path}")
            
            # Download with requests
            response = requests.get(photo_url, timeout=30)
            response.raise_for_status()
            
            # Save to file
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # Verify the file was created and has content
            file_size = get_file_size(str(save_path))
            if file_size == 0:
                self.logger.error("Downloaded file is empty")
                return False
            
            self.logger.info(f"Successfully saved photo to: {save_path}")
            self.logger.debug(f"File size: {file_size:,} bytes")
            
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Network error downloading photo: {e}")
            return False
        except IOError as e:
            self.logger.error(f"File system error saving photo: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error downloading photo: {e}")
            return False
    
    def get_photo_path(self, name: str, slack_handle: str) -> Path:
        """
        Get the expected path for a colleague's photo.
        
        Args:
            name: Colleague's full name
            slack_handle: Slack username (without @)
            
        Returns:
            Path where the photo would be/is stored
        """
        return Path(self.output_manager.get_photo_path(name))
    
    def photo_exists(self, name: str, slack_handle: str) -> bool:
        """
        Check if a colleague's photo already exists.
        
        Args:
            name: Colleague's full name
            slack_handle: Slack username (without @)
            
        Returns:
            True if photo file exists and has content, False otherwise
        """
        photo_path = self.get_photo_path(name, slack_handle)
        return photo_path.exists() and get_file_size(str(photo_path)) > 0
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about photo storage.
        
        Returns:
            Dictionary containing storage information
        """
        return {
            'storage_path': str(self.storage_path),
            'photo_size': self.photo_size,
            'exists': self.storage_path.exists(),
            'is_directory': self.storage_path.is_dir() if self.storage_path.exists() else False
        }
