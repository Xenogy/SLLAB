"""
String utility functions for the AccountDB application.

This module provides utility functions for string manipulation and validation.
"""

import re
import uuid
from typing import Optional, Union, List, Dict, Any

# Regular expressions for validation
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,32}$'
PASSWORD_PATTERN = r'^.{8,64}$'
STEAMID_PATTERN = r'^[0-9]{17}$'

def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the string is a valid UUID, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value
    except (ValueError, AttributeError, TypeError):
        return False

def is_valid_email(value: str) -> bool:
    """
    Check if a string is a valid email address.
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the string is a valid email address, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    return bool(re.match(EMAIL_PATTERN, value))

def is_valid_username(value: str) -> bool:
    """
    Check if a string is a valid username.
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the string is a valid username, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    return bool(re.match(USERNAME_PATTERN, value))

def is_valid_password(value: str) -> bool:
    """
    Check if a string is a valid password.
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the string is a valid password, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    return bool(re.match(PASSWORD_PATTERN, value))

def is_valid_steam_id(value: str) -> bool:
    """
    Check if a string is a valid Steam ID.
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the string is a valid Steam ID, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    return bool(re.match(STEAMID_PATTERN, value))

def sanitize_string(value: str, allow_html: bool = False) -> str:
    """
    Sanitize a string by removing potentially dangerous characters.
    
    Args:
        value: The string to sanitize
        allow_html: Whether to allow HTML tags
        
    Returns:
        str: The sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    if not allow_html:
        # Remove HTML tags
        value = re.sub(r'<[^>]*>', '', value)
    
    # Remove control characters
    value = re.sub(r'[\x00-\x1F\x7F]', '', value)
    
    return value

def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        value: The string to truncate
        max_length: The maximum length of the string
        suffix: The suffix to add to the truncated string
        
    Returns:
        str: The truncated string
    """
    if not isinstance(value, str):
        return ""
    
    if len(value) <= max_length:
        return value
    
    return value[:max_length - len(suffix)] + suffix

def mask_sensitive_data(value: str, mask_char: str = "*", visible_prefix: int = 2, visible_suffix: int = 2) -> str:
    """
    Mask sensitive data in a string.
    
    Args:
        value: The string to mask
        mask_char: The character to use for masking
        visible_prefix: The number of characters to leave visible at the beginning
        visible_suffix: The number of characters to leave visible at the end
        
    Returns:
        str: The masked string
    """
    if not isinstance(value, str):
        return ""
    
    if len(value) <= visible_prefix + visible_suffix:
        return value
    
    prefix = value[:visible_prefix]
    suffix = value[-visible_suffix:] if visible_suffix > 0 else ""
    masked_length = len(value) - visible_prefix - visible_suffix
    masked = mask_char * masked_length
    
    return prefix + masked + suffix
