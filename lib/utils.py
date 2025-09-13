"""
Utility Functions

This module provides common utility functions used across the project.
"""

import re
import os
from pathlib import Path
from typing import Optional, Dict, Any


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing problematic characters.
    
    Args:
        filename: The original filename
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^\w\-_.]', '_', filename)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure we don't have an empty filename
    if not sanitized:
        sanitized = "untitled"
    
    return sanitized


def generate_photo_filename(name: str, handle: str, extension: str = "jpg") -> str:
    """
    Generate a standardized photo filename from name and handle.
    
    Args:
        name: Full name of the person
        handle: Slack handle/username
        extension: File extension (without dot)
        
    Returns:
        Standardized filename
    """
    # Sanitize both components
    clean_name = sanitize_filename(name.replace(' ', '_').lower())
    clean_handle = sanitize_filename(handle.lower())
    
    return f"{clean_name}_{clean_handle}.{extension}"


def ensure_directory_exists(directory_path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_config_path(path: str, base_path: Optional[str] = None) -> Path:
    """
    Resolve a configuration path, handling relative and absolute paths.
    
    Args:
        path: The path from configuration
        base_path: Base path for relative paths (defaults to current working directory)
        
    Returns:
        Resolved Path object
    """
    if not path:
        raise ValueError("Path cannot be empty")
    
    path_obj = Path(path)
    
    if path_obj.is_absolute():
        return path_obj
    else:
        # Relative path
        if base_path:
            return Path(base_path) / path_obj
        else:
            return Path.cwd() / path_obj


def validate_config_section(config: Dict[str, Any], section: str, required_keys: list) -> bool:
    """
    Validate that a configuration section has all required keys.
    
    Args:
        config: Configuration dictionary
        section: Section name to validate
        required_keys: List of required key names
        
    Returns:
        True if valid, False otherwise
    """
    if section not in config:
        return False
    
    section_config = config[section]
    return all(key in section_config for key in required_keys)


def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return 0
