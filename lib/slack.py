"""
Slack Integration Client

This module provides integration with the Slack API for retrieving user
information and profile photos.
"""

import logging
from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .onepassword import OnePasswordClient


class SlackClient:
    """
    Client for integrating with Slack API.
    
    This class handles:
    - User lookup by handle/username with pagination support
    - Profile photo URL retrieval
    - Slack API error handling
    """
    
    def __init__(self, token: str):
        """
        Initialize Slack client with API token.
        
        Args:
            token: Slack API token
        """
        self.client = WebClient(token=token)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized Slack client")
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any], onepassword_client: OnePasswordClient, dry_run: bool = False) -> 'SlackClient':
        """
        Create SlackClient from configuration with 1Password token retrieval.
        
        Args:
            config: Application configuration dictionary
            onepassword_client: OnePasswordClient for token retrieval
            dry_run: If True, use dummy token for testing
            
        Returns:
            Configured SlackClient instance
            
        Raises:
            ValueError: If Slack configuration is invalid
        """
        logger = logging.getLogger(__name__)
        
        if dry_run:
            logger.info("Using dummy token for dry-run mode")
            return cls("xoxb-dummy-token-for-testing")
        
        # Get Slack configuration
        slack_config = config.get('slack', {}).get('onepassword', {}).get('cli', {})
        if not slack_config.get('enabled', False):
            raise ValueError("Slack 1Password integration is not enabled in configuration")
        
        if not all(key in slack_config for key in ['item_name', 'field_name']):
            raise ValueError("Slack configuration missing 'item_name' or 'field_name'")
        
        # Retrieve token from 1Password
        item_name = slack_config['item_name']
        field_name = slack_config['field_name']
        token = onepassword_client.get_secret(item_name, field_name)
        
        return cls(token)
    
    def get_photo_url(self, user_info: Dict[str, Any], size: str = "512") -> Optional[str]:
        """
        Extract profile photo URL from user information.
        
        Args:
            user_info: User information dictionary from Slack API
            size: Photo size (72, 192, 512, 1024, original)
            
        Returns:
            Photo URL string, or None if not available
        """
        try:
            profile = user_info.get('profile', {})
            
            # Try to get the requested size
            photo_key = f"image_{size}"
            photo_url = profile.get(photo_key)
            
            if not photo_url:
                # Fallback to other sizes if requested size not available
                fallback_sizes = ['image_512', 'image_192', 'image_72', 'image_original']
                for fallback_key in fallback_sizes:
                    photo_url = profile.get(fallback_key)
                    if photo_url:
                        self.logger.debug(f"Using fallback photo size: {fallback_key}")
                        break
            
            if photo_url:
                is_custom = profile.get('is_custom_image', False)
                self.logger.debug(f"Photo URL found (custom: {is_custom}): {photo_url}")
                return photo_url
            else:
                self.logger.warning("No profile photo URL found in user info")
                return None
                
        except Exception as e:
            self.logger.error(f"Unexpected error getting photo URL: {e}")
            return None
    
    def get_user_info(self, slack_handle: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Slack with pagination support.
        
        Args:
            slack_handle: Slack username (without @)
            
        Returns:
            User information dictionary, or None if user not found
        """
        try:
            # Search through paginated results to find user
            cursor = None
            users_searched = 0
            max_pages = 5  # Limit to avoid excessive API calls
            
            for page in range(1, max_pages + 1):
                # Get the current page of users
                if cursor:
                    result = self.client.users_list(cursor=cursor, limit=1000)
                else:
                    result = self.client.users_list(limit=1000)
                
                users_searched += len(result['members'])
                self.logger.debug(f"Page {page}: Searching through {len(result['members'])} users (total: {users_searched}) for @{slack_handle}")
                
                # Search through users on this page
                for user in result['members']:
                    profile = user.get('profile', {})
                    name = user.get('name', '')
                    display_name = profile.get('display_name', '')
                    real_name_normalized = profile.get('real_name_normalized', '')
                    
                    # More comprehensive matching - handle both username and display name (handle)
                    if (name == slack_handle or 
                        display_name == slack_handle or
                        real_name_normalized.lower() == slack_handle.lower() or
                        name.lower() == slack_handle.lower() or
                        display_name.lower() == slack_handle.lower()):
                        
                        self.logger.info(f"Found user @{slack_handle}: {profile.get('real_name', 'Unknown')} (found on page {page})")
                        self.logger.debug(f"  Matched on field: name={name}, display={display_name}")
                        return user
                
                # Check if there's a next page
                if 'response_metadata' in result and result['response_metadata'].get('next_cursor'):
                    cursor = result['response_metadata']['next_cursor']
                    self.logger.debug(f"Moving to page {page + 1} with cursor: {cursor[:20]}...")
                else:
                    self.logger.debug(f"No more pages after page {page}")
                    break  # No more pages
            
            self.logger.warning(f"User @{slack_handle} not found in Slack workspace (searched {users_searched} users across {page} pages)")
            return None
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error looking up user: {e.response['error']}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error looking up user: {e}")
            return None