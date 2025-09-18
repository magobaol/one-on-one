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
from typing import Dict, Any, Optional

from lib.onepassword import OnePasswordClient
from lib.slack import SlackClient
from lib.photo_manager import PhotoManager
from lib.omnifocus import OmniFocusClient
from lib.output_manager import OutputManager
from lib.obsidian import ObsidianClient
from lib.keyboard_maestro import KeyboardMaestroClient
from lib.stream_deck import StreamDeckClient


class OneOnOneSetup:
    """Main class for handling one-on-one meeting setup automation."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the setup with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # Initialize service clients
        self.onepassword_client = OnePasswordClient()
        self.output_manager = OutputManager(self.config)
        self.photo_manager = PhotoManager(self.config, self.output_manager)
        self.omnifocus_client = OmniFocusClient(self.config, self.output_manager)
        self.obsidian_client = self._initialize_obsidian_client()
        self.keyboard_maestro_client = self._initialize_keyboard_maestro_client()
        self.stream_deck_client = self._initialize_stream_deck_client()
    
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
    
    def _initialize_obsidian_client(self) -> Optional['ObsidianClient']:
        """Initialize Obsidian client if configuration is available."""
        try:
            if 'obsidian' not in self.config or not self.config['obsidian'].get('vault_path'):
                self.logger.info("Obsidian integration disabled (no vault_path configured)")
                return None
            
            return ObsidianClient(self.config, self.output_manager)
        except Exception as e:
            self.logger.warning(f"Obsidian integration disabled due to configuration error: {e}")
            return None
    
    def _initialize_keyboard_maestro_client(self) -> Optional['KeyboardMaestroClient']:
        """Initialize Keyboard Maestro client if configuration is available."""
        try:
            if 'keyboard_maestro' not in self.config:
                self.logger.info("Keyboard Maestro integration disabled (no configuration)")
                return None
            
            return KeyboardMaestroClient(self.config, self.output_manager)
        except Exception as e:
            self.logger.warning(f"Keyboard Maestro integration disabled due to configuration error: {e}")
            return None
    
    def _initialize_stream_deck_client(self) -> Optional['StreamDeckClient']:
        """Initialize Stream Deck client with fixed template and position."""
        try:
            # Stream Deck client uses fixed template and grid position for standardization
            # No configuration required - works out of the box
            return StreamDeckClient(self.config, self.output_manager)
        except Exception as e:
            self.logger.warning(f"Stream Deck integration disabled due to template file error: {e}")
            return None
    
    
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
        success = self.photo_manager.download_from_slack(slack_client, name, slack_handle)
        
        # Open the colleague folder in Finder right after it's created
        if success:
            self._open_colleague_folder(name)
        
        return success
    
    def _create_omnifocus_tag(self, name: str, slack_handle: str) -> bool:
        """
        Create an OmniFocus tag for the colleague.
        
        Args:
            name: Colleague's full name
            slack_handle: Slack username (without @)
            
        Returns:
            True if tag was created successfully, False otherwise
        """
        return self.omnifocus_client.create_colleague_tag(name, slack_handle)
    
    def _create_omnifocus_perspective(self, name: str) -> bool:
        """
        Create an OmniFocus perspective for the colleague.
        
        Args:
            name: Colleague's full name
            
        Returns:
            True if perspective was created successfully, False otherwise
        """
        return self.omnifocus_client.create_colleague_perspective(name)
    
    def _create_obsidian_note(self, name: str, slack_handle: str) -> bool:
        """
        Create an Obsidian note for the colleague.
        
        Args:
            name: Colleague's full name
            slack_handle: Colleague's Slack username
            
        Returns:
            True if note was created successfully, False otherwise
        """
        if not self.obsidian_client:
            self.logger.info("Obsidian integration disabled - skipping note creation")
            return True
            
        return self.obsidian_client.create_colleague_note(name, slack_handle)
    
    def _create_keyboard_maestro_macro(self, name: str, slack_handle: str) -> tuple[bool, str]:
        """
        Create a Keyboard Maestro macro for the colleague.
        
        Args:
            name: Colleague's full name
            slack_handle: Colleague's Slack username
            
        Returns:
            Tuple of (success_status, macro_uuid):
            - success_status: True if macro was created successfully, False otherwise
            - macro_uuid: The generated macro UUID if successful, None if failed
        """
        if not self.keyboard_maestro_client:
            self.logger.info("Keyboard Maestro integration disabled - skipping macro creation")
            return (True, None)
            
        return self.keyboard_maestro_client.create_colleague_macro(name, slack_handle)
    
    def _create_stream_deck_action(self, name: str, km_macro_uuid: str) -> bool:
        """
        Create a Stream Deck action for the colleague that links to their Keyboard Maestro macro.
        
        Args:
            name: Colleague's full name
            km_macro_uuid: UUID of the colleague's Keyboard Maestro macro
            
        Returns:
            True if action was created successfully, False otherwise
        """
        if not self.stream_deck_client:
            self.logger.info("Stream Deck integration disabled - skipping action creation")
            return True
        
        if not km_macro_uuid:
            self.logger.info("No Keyboard Maestro UUID available - skipping Stream Deck action creation")
            return True
            
        return self.stream_deck_client.create_colleague_action(name, km_macro_uuid)
    
    def _open_colleague_folder(self, name: str) -> None:
        """
        Open the colleague's folder in Finder.
        
        Args:
            name: Colleague's full name
        """
        try:
            import subprocess
            colleague_folder = self.output_manager.get_colleague_folder(name)
            subprocess.run(['open', colleague_folder], timeout=5)
            self.logger.info(f"📂 Opened colleague folder in Finder: {name}")
        except Exception as e:
            self.logger.debug(f"Could not open folder automatically: {e}")
    
    
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
            
            # Step 3: Create OmniFocus tag
            if dry_run:
                tag_info = self.omnifocus_client.get_tag_info(name)
                self.logger.info(f"[DRY-RUN] Would create OmniFocus tag: {tag_info['tag_name']}")
                omnifocus_tag_success = True
            else:
                omnifocus_tag_success = self._create_omnifocus_tag(name, slack_handle)
                if not omnifocus_tag_success:
                    self.logger.warning("Failed to create OmniFocus tag, continuing anyway...")
            
            # Step 4: Create OmniFocus perspective
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would create OmniFocus perspective: {name}")
                omnifocus_perspective_success = True
            else:
                omnifocus_perspective_success = self._create_omnifocus_perspective(name)
                if not omnifocus_perspective_success:
                    self.logger.warning("Failed to create OmniFocus perspective, continuing anyway...")
            
            # Step 5: Create Obsidian note
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would create Obsidian note: {name}")
                obsidian_success = True
            else:
                obsidian_success = self._create_obsidian_note(name, slack_handle)
                if not obsidian_success:
                    self.logger.warning("Failed to create Obsidian note, continuing anyway...")
            
            # Step 6: Create Keyboard Maestro macro
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would create Keyboard Maestro macro: One-to-One - {name}")
                keyboard_maestro_success = True
                km_macro_uuid = "DRY-RUN-UUID-123"
            else:
                keyboard_maestro_success, km_macro_uuid = self._create_keyboard_maestro_macro(name, slack_handle)
                if not keyboard_maestro_success:
                    self.logger.warning("Failed to create Keyboard Maestro macro, continuing anyway...")
                    km_macro_uuid = None
            
            # Step 7: Create Stream Deck action
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would create Stream Deck action: One-to-One - {name}")
                stream_deck_success = True
            else:
                stream_deck_success = self._create_stream_deck_action(name, km_macro_uuid)
                if not stream_deck_success:
                    self.logger.warning("Failed to create Stream Deck action, continuing anyway...")
            
            # Step 8: Import and open OmniFocus perspective (final step)
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would import and open OmniFocus perspective: {name}")
            else:
                # Only import and open if we successfully created the perspective
                if omnifocus_perspective_success:
                    self.omnifocus_client.import_and_open_perspective(name)
                else:
                    self.logger.info("Skipping perspective import - perspective was not created successfully")
            
            # Step 9: Import and open Keyboard Maestro macro (final step)
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would import and open Keyboard Maestro macro: One-to-One - {name}")
            else:
                # Only import and open if we successfully created the macro
                if keyboard_maestro_success and self.keyboard_maestro_client:
                    self.keyboard_maestro_client.import_and_open_macro(name)
                else:
                    self.logger.info("Skipping macro import - macro was not created successfully")
            
            # Step 10: Import and open Stream Deck action (final step)
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would import and open Stream Deck action: One-to-One - {name}")
            else:
                # Only import and open if we successfully created the action
                if stream_deck_success and self.stream_deck_client:
                    self.stream_deck_client.import_and_open_action(name)
                else:
                    self.logger.info("Skipping Stream Deck import - action was not created successfully")
            
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