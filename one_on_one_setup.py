#!/usr/bin/env python3
"""
One-on-One Meeting Setup Automation

This script automates the workflow for managing one-on-one meetings with colleagues.
"""

import sys
import argparse
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

from lib.onepassword import OnePasswordClient
from lib.slack import SlackClient
from lib.photo_manager import PhotoManager


class OneOnOneSetup:
    """Main class for handling one-on-one meeting setup automation."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the setup with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # Initialize service clients
        self.onepassword_client = OnePasswordClient()
        self.photo_manager = PhotoManager(self.config)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _setup_logging(self):
        """Configure logging based on config settings."""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    
    def _download_colleague_photo(self, slack_client: SlackClient, name: str, slack_handle: str) -> bool:
        """
        Download colleague's profile photo from Slack.
        
        Args:
            slack_client: Initialized Slack client
            name: Colleague's full name
            slack_handle: Slack username (without @)
            
        Returns:
            True if photo was downloaded successfully, False otherwise
        """
        return self.photo_manager.download_from_slack(slack_client, name, slack_handle)
    
    def setup_colleague(self, name: str, slack_handle: str, dry_run: bool = False):
        """
        Main method to set up everything for a new colleague.
        
        Args:
            name: Colleague's full name
            slack_handle: Colleague's Slack username
            dry_run: If True, simulate operations without making changes
        """
        self.logger.info(f"Starting setup for colleague: {name} (@{slack_handle})")
        
        try:
            # Step 1: Create authenticated Slack client
            slack_client = SlackClient.create_from_config(self.config, self.onepassword_client, dry_run)
            
            # Step 2: Download Slack profile photo
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would download profile photo for {name} (@{slack_handle})")
                photo_success = True
            else:
                photo_success = self._download_colleague_photo(slack_client, name, slack_handle)
                if not photo_success:
                    self.logger.warning("Failed to download profile photo, continuing anyway...")
            
            # TODO: Additional integrations will be added in subsequent commits
            # - OmniFocus tag creation
            # - Obsidian note creation
            # - Keyboard Maestro macro setup
            
            self.logger.info("Setup completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up one-on-one meeting automation for a colleague"
    )
    parser.add_argument("name", help="Colleague's full name")
    parser.add_argument("slack_handle", help="Colleague's Slack handle (without @)")
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Simulate operations without making changes"
    )
    
    args = parser.parse_args()
    
    try:
        setup = OneOnOneSetup(args.config)
        setup.setup_colleague(args.name, args.slack_handle, dry_run=args.dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()