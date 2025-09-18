"""
1Password Integration Client

This module provides secure integration with 1Password CLI to retrieve
secrets like Slack API tokens without storing them in configuration files.
"""

import subprocess
import logging


class OnePasswordClient:
    """
    Client for integrating with 1Password CLI to securely retrieve secrets.
    
    This class handles:
    - Checking 1Password CLI availability
    - Retrieving API tokens and secrets from 1Password items
    - Error handling and validation
    """
    
    def __init__(self):
        """
        Initialize 1Password client.
        
        Note: This is a generic client that can retrieve any secret.
        Configuration is passed per-operation for flexibility.
        """
        self.logger = logging.getLogger(__name__)
        
        if not self.is_available():
            raise RuntimeError("1Password CLI is not available or not authenticated")
        
        self.logger.info("Initialized 1Password client")
    
    def is_available(self) -> bool:
        """
        Check if 1Password CLI is available and authenticated.
        
        Returns:
            True if 1Password CLI is available and ready, False otherwise
        """
        try:
            result = subprocess.run(['op', 'account', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_secret(self, item_name: str, field_name: str) -> str:
        """
        Retrieve a secret from 1Password.
        
        Args:
            item_name: Name of the 1Password item
            field_name: Name of the field within the item
        
        Returns:
            The secret value as a string
            
        Raises:
            RuntimeError: If secret retrieval fails
        """
        self.logger.info(f"Retrieving secret from 1Password item: {item_name}")
        
        try:
            # Use 1Password CLI to get the secret (with --reveal to get sensitive content)
            cmd = ['op', 'item', 'get', item_name, '--field', field_name, '--reveal']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise RuntimeError(f"Failed to retrieve secret from 1Password: {error_msg}")
            
            secret = result.stdout.strip()
            if not secret:
                raise RuntimeError("Retrieved empty secret from 1Password")
            
            self.logger.info(f"Successfully retrieved secret from 1Password item: {item_name}")
            return secret
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout while retrieving secret from 1Password")
        except Exception as e:
            raise RuntimeError(f"Error retrieving secret from 1Password: {e}")
