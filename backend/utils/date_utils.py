"""
Date utility functions for the AccountDB application.

This module provides utility functions for date and time manipulation.
"""

import time
import datetime
from typing import Optional, Union, Dict, Any

def get_current_timestamp() -> int:
    """
    Get the current Unix timestamp.
    
    Returns:
        int: The current Unix timestamp in seconds
    """
    return int(time.time())

def format_timestamp(timestamp: Union[int, float], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a Unix timestamp as a string.
    
    Args:
        timestamp: The Unix timestamp in seconds
        format_str: The format string to use
        
    Returns:
        str: The formatted timestamp
    """
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime(format_str)
    except (ValueError, TypeError, OverflowError):
        return ""

def parse_timestamp(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[int]:
    """
    Parse a string into a Unix timestamp.
    
    Args:
        date_str: The string to parse
        format_str: The format string to use
        
    Returns:
        Optional[int]: The Unix timestamp in seconds, or None if parsing fails
    """
    try:
        dt = datetime.datetime.strptime(date_str, format_str)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return None

def get_date_from_timestamp(timestamp: Union[int, float]) -> Optional[datetime.datetime]:
    """
    Convert a Unix timestamp to a datetime object.
    
    Args:
        timestamp: The Unix timestamp in seconds
        
    Returns:
        Optional[datetime.datetime]: The datetime object, or None if conversion fails
    """
    try:
        return datetime.datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError, OverflowError):
        return None

def get_timestamp_from_date(dt: datetime.datetime) -> Optional[int]:
    """
    Convert a datetime object to a Unix timestamp.
    
    Args:
        dt: The datetime object
        
    Returns:
        Optional[int]: The Unix timestamp in seconds, or None if conversion fails
    """
    try:
        return int(dt.timestamp())
    except (ValueError, TypeError, AttributeError):
        return None

def get_time_ago(timestamp: Union[int, float]) -> str:
    """
    Get a human-readable string representing the time elapsed since a timestamp.
    
    Args:
        timestamp: The Unix timestamp in seconds
        
    Returns:
        str: A human-readable string (e.g., "2 hours ago")
    """
    try:
        now = get_current_timestamp()
        diff = now - int(timestamp)
        
        if diff < 0:
            return "in the future"
        
        if diff < 60:
            return f"{diff} seconds ago"
        
        if diff < 3600:
            minutes = diff // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        
        if diff < 86400:
            hours = diff // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        if diff < 604800:
            days = diff // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
        
        if diff < 2592000:
            weeks = diff // 604800
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        
        if diff < 31536000:
            months = diff // 2592000
            return f"{months} month{'s' if months != 1 else ''} ago"
        
        years = diff // 31536000
        return f"{years} year{'s' if years != 1 else ''} ago"
    except (ValueError, TypeError):
        return "unknown time ago"
