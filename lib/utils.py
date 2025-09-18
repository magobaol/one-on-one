"""
Utility Functions

This module provides common utility functions used across the project.
"""

import os


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
