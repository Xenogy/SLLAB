"""
File utility functions for the AccountDB application.

This module provides utility functions for file operations and validation.
"""

import os
import re
import mimetypes
from typing import Optional, Dict, List, Any, Union

# File type constants
ALLOWED_FILE_TYPES = {
    'json': ['application/json'],
    'csv': ['text/csv', 'application/csv', 'application/vnd.ms-excel'],
    'image': ['image/jpeg', 'image/png', 'image/gif'],
    'text': ['text/plain'],
}

# File size constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def get_file_extension(filename: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        filename: The name of the file
        
    Returns:
        str: The file extension (without the dot)
    """
    if not isinstance(filename, str):
        return ""
    
    _, ext = os.path.splitext(filename)
    return ext.lstrip('.').lower()

def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: The path to the file
        
    Returns:
        Optional[int]: The file size in bytes, or None if the file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, TypeError):
        return None

def get_file_mime_type(filename: str) -> str:
    """
    Get the MIME type of a file based on its extension.
    
    Args:
        filename: The name of the file
        
    Returns:
        str: The MIME type of the file
    """
    if not isinstance(filename, str):
        return ""
    
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or ""

def is_valid_file_type(filename: str, allowed_types: List[str]) -> bool:
    """
    Check if a file has an allowed type.
    
    Args:
        filename: The name of the file
        allowed_types: A list of allowed file types (e.g., ['json', 'csv'])
        
    Returns:
        bool: True if the file has an allowed type, False otherwise
    """
    if not isinstance(filename, str) or not filename:
        return False
    
    ext = get_file_extension(filename)
    return ext in allowed_types

def is_valid_file_size(size: int, max_size: int = MAX_FILE_SIZE) -> bool:
    """
    Check if a file size is within the allowed limit.
    
    Args:
        size: The size of the file in bytes
        max_size: The maximum allowed size in bytes
        
    Returns:
        bool: True if the file size is within the allowed limit, False otherwise
    """
    try:
        return 0 <= int(size) <= max_size
    except (ValueError, TypeError):
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing potentially dangerous characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: The sanitized filename
    """
    if not isinstance(filename, str):
        return ""
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\.-]', '_', filename)
    
    # Ensure the filename is not empty
    if not filename:
        filename = "file"
    
    return filename
