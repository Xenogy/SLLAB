"""
JSON utility functions for the AccountDB application.

This module provides utility functions for JSON manipulation and validation.
"""

import json
from typing import Optional, Dict, List, Any, Union

def parse_json(json_str: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Parse a JSON string into a Python object.
    
    Args:
        json_str: The JSON string to parse
        
    Returns:
        Optional[Union[Dict[str, Any], List[Any]]]: The parsed JSON object, or None if parsing fails
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

def serialize_json(obj: Union[Dict[str, Any], List[Any]], pretty: bool = False) -> str:
    """
    Serialize a Python object to a JSON string.
    
    Args:
        obj: The object to serialize
        pretty: Whether to format the JSON string with indentation
        
    Returns:
        str: The JSON string
    """
    try:
        if pretty:
            return json.dumps(obj, indent=2, sort_keys=True)
        else:
            return json.dumps(obj)
    except (TypeError, OverflowError, ValueError):
        return "{}"

def is_valid_json(json_str: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        json_str: The string to check
        
    Returns:
        bool: True if the string is valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def json_to_dict(json_str: str) -> Dict[str, Any]:
    """
    Parse a JSON string into a dictionary.
    
    Args:
        json_str: The JSON string to parse
        
    Returns:
        Dict[str, Any]: The parsed dictionary, or an empty dictionary if parsing fails
    """
    try:
        obj = json.loads(json_str)
        if isinstance(obj, dict):
            return obj
        else:
            return {}
    except (json.JSONDecodeError, TypeError):
        return {}

def dict_to_json(obj: Dict[str, Any], pretty: bool = False) -> str:
    """
    Serialize a dictionary to a JSON string.
    
    Args:
        obj: The dictionary to serialize
        pretty: Whether to format the JSON string with indentation
        
    Returns:
        str: The JSON string
    """
    try:
        if pretty:
            return json.dumps(obj, indent=2, sort_keys=True)
        else:
            return json.dumps(obj)
    except (TypeError, OverflowError, ValueError):
        return "{}"

def merge_json(json1: Union[Dict[str, Any], str], json2: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Merge two JSON objects or strings.
    
    Args:
        json1: The first JSON object or string
        json2: The second JSON object or string
        
    Returns:
        Dict[str, Any]: The merged JSON object
    """
    # Convert strings to dictionaries
    if isinstance(json1, str):
        json1 = json_to_dict(json1)
    if isinstance(json2, str):
        json2 = json_to_dict(json2)
    
    # Ensure both are dictionaries
    if not isinstance(json1, dict) or not isinstance(json2, dict):
        return {}
    
    # Merge the dictionaries
    result = json1.copy()
    result.update(json2)
    
    return result

def extract_json_path(obj: Union[Dict[str, Any], List[Any]], path: str, default: Any = None) -> Any:
    """
    Extract a value from a JSON object using a path.
    
    Args:
        obj: The JSON object
        path: The path to the value (e.g., "user.name" or "items[0].id")
        default: The default value to return if the path doesn't exist
        
    Returns:
        Any: The value at the path, or the default value if the path doesn't exist
    """
    if not obj:
        return default
    
    # Split the path into parts
    parts = []
    current_part = ""
    in_brackets = False
    
    for char in path:
        if char == '.' and not in_brackets:
            if current_part:
                parts.append(current_part)
                current_part = ""
        elif char == '[':
            if current_part:
                parts.append(current_part)
                current_part = ""
            in_brackets = True
        elif char == ']':
            if in_brackets:
                parts.append(int(current_part) if current_part.isdigit() else current_part)
                current_part = ""
                in_brackets = False
        else:
            current_part += char
    
    if current_part:
        parts.append(current_part)
    
    # Traverse the object using the path
    current = obj
    
    for part in parts:
        try:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and isinstance(part, int) and 0 <= part < len(current):
                current = current[part]
            else:
                return default
        except (TypeError, KeyError, IndexError):
            return default
    
    return current
