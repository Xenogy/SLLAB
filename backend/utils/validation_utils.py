"""
Validation utility functions for the AccountDB application.

This module provides utility functions for data validation.
"""

import re
from typing import Optional, Dict, List, Any, Union, Type, Callable

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, List[str]]:
    """
    Validate that required fields are present in the data.
    
    Args:
        data: The data to validate
        required_fields: The list of required field names
        
    Returns:
        Dict[str, List[str]]: A dictionary of field names and error messages
    """
    errors = {}
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = [f"{field} is required"]
    
    return errors

def validate_field_type(data: Dict[str, Any], field: str, expected_type: Type) -> Optional[str]:
    """
    Validate that a field has the expected type.
    
    Args:
        data: The data to validate
        field: The field name
        expected_type: The expected type
        
    Returns:
        Optional[str]: An error message if validation fails, or None if validation succeeds
    """
    if field not in data:
        return None
    
    value = data[field]
    
    if value is None:
        return None
    
    if not isinstance(value, expected_type):
        return f"{field} must be of type {expected_type.__name__}"
    
    return None

def validate_field_length(data: Dict[str, Any], field: str, min_length: Optional[int] = None, max_length: Optional[int] = None) -> Optional[str]:
    """
    Validate that a field has a length within the specified range.
    
    Args:
        data: The data to validate
        field: The field name
        min_length: The minimum length, or None for no minimum
        max_length: The maximum length, or None for no maximum
        
    Returns:
        Optional[str]: An error message if validation fails, or None if validation succeeds
    """
    if field not in data:
        return None
    
    value = data[field]
    
    if value is None:
        return None
    
    try:
        length = len(value)
    except (TypeError, AttributeError):
        return f"{field} must have a length"
    
    if min_length is not None and length < min_length:
        return f"{field} must be at least {min_length} characters long"
    
    if max_length is not None and length > max_length:
        return f"{field} must be at most {max_length} characters long"
    
    return None

def validate_field_pattern(data: Dict[str, Any], field: str, pattern: str) -> Optional[str]:
    """
    Validate that a field matches a regular expression pattern.
    
    Args:
        data: The data to validate
        field: The field name
        pattern: The regular expression pattern
        
    Returns:
        Optional[str]: An error message if validation fails, or None if validation succeeds
    """
    if field not in data:
        return None
    
    value = data[field]
    
    if value is None:
        return None
    
    if not isinstance(value, str):
        return f"{field} must be a string"
    
    if not re.match(pattern, value):
        return f"{field} must match pattern {pattern}"
    
    return None

def validate_field_range(data: Dict[str, Any], field: str, min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None) -> Optional[str]:
    """
    Validate that a field has a value within the specified range.
    
    Args:
        data: The data to validate
        field: The field name
        min_value: The minimum value, or None for no minimum
        max_value: The maximum value, or None for no maximum
        
    Returns:
        Optional[str]: An error message if validation fails, or None if validation succeeds
    """
    if field not in data:
        return None
    
    value = data[field]
    
    if value is None:
        return None
    
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return f"{field} must be a number"
    
    if min_value is not None and numeric_value < min_value:
        return f"{field} must be at least {min_value}"
    
    if max_value is not None and numeric_value > max_value:
        return f"{field} must be at most {max_value}"
    
    return None

def validate_field_enum(data: Dict[str, Any], field: str, allowed_values: List[Any]) -> Optional[str]:
    """
    Validate that a field has a value from a list of allowed values.
    
    Args:
        data: The data to validate
        field: The field name
        allowed_values: The list of allowed values
        
    Returns:
        Optional[str]: An error message if validation fails, or None if validation succeeds
    """
    if field not in data:
        return None
    
    value = data[field]
    
    if value is None:
        return None
    
    if value not in allowed_values:
        return f"{field} must be one of {', '.join(str(v) for v in allowed_values)}"
    
    return None
