"""
Centralized validation module for the AccountDB application.

This module provides functions for validating input data to ensure it meets
the required format and constraints before being processed by the application.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ValidationError, validator, Field
from pydantic.networks import EmailStr
from datetime import datetime
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Regular expressions for validation
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,32}$'
PASSWORD_PATTERN = r'^.{8,64}$'
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
STEAMID_PATTERN = r'^[0-9]{17}$'

# File validation constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_TYPES = {
    'json': ['application/json'],
    'csv': ['text/csv', 'application/csv', 'application/vnd.ms-excel'],
    'image': ['image/jpeg', 'image/png', 'image/gif'],
    'text': ['text/plain'],
}

class ValidationResult(BaseModel):
    """Model for validation results."""
    valid: bool
    errors: List[Dict[str, Any]] = []

def validate_string(value: str, min_length: int = 1, max_length: int = 255, pattern: Optional[str] = None) -> ValidationResult:
    """
    Validate a string value.
    
    Args:
        value: The string to validate
        min_length: The minimum length of the string
        max_length: The maximum length of the string
        pattern: A regular expression pattern the string must match
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(value, str):
        errors.append({
            "field": "value",
            "message": f"Value must be a string, got {type(value).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    if len(value) < min_length:
        errors.append({
            "field": "value",
            "message": f"String must be at least {min_length} characters long"
        })
    
    if len(value) > max_length:
        errors.append({
            "field": "value",
            "message": f"String must be at most {max_length} characters long"
        })
    
    if pattern and not re.match(pattern, value):
        errors.append({
            "field": "value",
            "message": f"String must match pattern {pattern}"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_email(email: str) -> ValidationResult:
    """
    Validate an email address.
    
    Args:
        email: The email address to validate
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(email, str):
        errors.append({
            "field": "email",
            "message": f"Email must be a string, got {type(email).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    if not re.match(EMAIL_PATTERN, email):
        errors.append({
            "field": "email",
            "message": "Invalid email address format"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_uuid(value: str) -> ValidationResult:
    """
    Validate a UUID string.
    
    Args:
        value: The UUID string to validate
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(value, str):
        errors.append({
            "field": "value",
            "message": f"UUID must be a string, got {type(value).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    if not re.match(UUID_PATTERN, value):
        errors.append({
            "field": "value",
            "message": "Invalid UUID format"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> ValidationResult:
    """
    Validate an integer value.
    
    Args:
        value: The value to validate
        min_value: The minimum allowed value
        max_value: The maximum allowed value
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        errors.append({
            "field": "value",
            "message": f"Value must be an integer, got {type(value).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    if min_value is not None and int_value < min_value:
        errors.append({
            "field": "value",
            "message": f"Value must be at least {min_value}"
        })
    
    if max_value is not None and int_value > max_value:
        errors.append({
            "field": "value",
            "message": f"Value must be at most {max_value}"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_boolean(value: Any) -> ValidationResult:
    """
    Validate a boolean value.
    
    Args:
        value: The value to validate
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(value, bool):
        if isinstance(value, str):
            if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                errors.append({
                    "field": "value",
                    "message": f"Value must be a boolean, got {value}"
                })
        else:
            errors.append({
                "field": "value",
                "message": f"Value must be a boolean, got {type(value).__name__}"
            })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_date(value: str, format: str = "%Y-%m-%d") -> ValidationResult:
    """
    Validate a date string.
    
    Args:
        value: The date string to validate
        format: The expected date format
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(value, str):
        errors.append({
            "field": "value",
            "message": f"Date must be a string, got {type(value).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    try:
        datetime.strptime(value, format)
    except ValueError:
        errors.append({
            "field": "value",
            "message": f"Date must be in format {format}"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_datetime(value: str, format: str = "%Y-%m-%dT%H:%M:%S") -> ValidationResult:
    """
    Validate a datetime string.
    
    Args:
        value: The datetime string to validate
        format: The expected datetime format
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(value, str):
        errors.append({
            "field": "value",
            "message": f"Datetime must be a string, got {type(value).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    try:
        datetime.strptime(value, format)
    except ValueError:
        errors.append({
            "field": "value",
            "message": f"Datetime must be in format {format}"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_file_type(content_type: str, allowed_types: List[str]) -> ValidationResult:
    """
    Validate a file's content type.
    
    Args:
        content_type: The content type to validate
        allowed_types: A list of allowed content types
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if content_type not in allowed_types:
        errors.append({
            "field": "content_type",
            "message": f"Content type {content_type} is not allowed. Allowed types: {', '.join(allowed_types)}"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_file_size(size: int, max_size: int = MAX_FILE_SIZE) -> ValidationResult:
    """
    Validate a file's size.
    
    Args:
        size: The file size in bytes
        max_size: The maximum allowed size in bytes
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if size > max_size:
        errors.append({
            "field": "size",
            "message": f"File size {size} bytes exceeds maximum allowed size of {max_size} bytes"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_file(content_type: str, size: int, file_type: str = None, max_size: int = MAX_FILE_SIZE) -> ValidationResult:
    """
    Validate a file's content type and size.
    
    Args:
        content_type: The content type to validate
        size: The file size in bytes
        file_type: The expected file type (json, csv, image, text)
        max_size: The maximum allowed size in bytes
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate file type
    if file_type:
        if file_type not in ALLOWED_FILE_TYPES:
            errors.append({
                "field": "file_type",
                "message": f"File type {file_type} is not supported. Supported types: {', '.join(ALLOWED_FILE_TYPES.keys())}"
            })
        else:
            allowed_types = ALLOWED_FILE_TYPES[file_type]
            type_result = validate_file_type(content_type, allowed_types)
            if not type_result.valid:
                errors.extend(type_result.errors)
    
    # Validate file size
    size_result = validate_file_size(size, max_size)
    if not size_result.valid:
        errors.extend(size_result.errors)
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_username(username: str) -> ValidationResult:
    """
    Validate a username.
    
    Args:
        username: The username to validate
        
    Returns:
        ValidationResult: The validation result
    """
    return validate_string(username, min_length=3, max_length=32, pattern=USERNAME_PATTERN)

def validate_password(password: str) -> ValidationResult:
    """
    Validate a password.
    
    Args:
        password: The password to validate
        
    Returns:
        ValidationResult: The validation result
    """
    return validate_string(password, min_length=8, max_length=64, pattern=PASSWORD_PATTERN)

def validate_steam_id(steam_id: str) -> ValidationResult:
    """
    Validate a Steam ID.
    
    Args:
        steam_id: The Steam ID to validate
        
    Returns:
        ValidationResult: The validation result
    """
    return validate_string(steam_id, pattern=STEAMID_PATTERN)

# Pydantic models for validation
class UserValidator(BaseModel):
    """Validator for user data."""
    username: str
    password: str
    
    @validator('username')
    def username_must_be_valid(cls, v):
        result = validate_username(v)
        if not result.valid:
            raise ValueError(result.errors[0]['message'])
        return v
    
    @validator('password')
    def password_must_be_valid(cls, v):
        result = validate_password(v)
        if not result.valid:
            raise ValueError(result.errors[0]['message'])
        return v

class EmailValidator(BaseModel):
    """Validator for email data."""
    address: EmailStr
    password: str
    
    @validator('password')
    def password_must_be_valid(cls, v):
        result = validate_password(v)
        if not result.valid:
            raise ValueError(result.errors[0]['message'])
        return v

class VaultValidator(BaseModel):
    """Validator for vault data."""
    address: str
    password: str
    
    @validator('password')
    def password_must_be_valid(cls, v):
        result = validate_password(v)
        if not result.valid:
            raise ValueError(result.errors[0]['message'])
        return v

class SteamguardValidator(BaseModel):
    """Validator for steamguard data."""
    account_name: Optional[str] = None
    device_id: Optional[str] = None
    identity_secret: Optional[str] = None
    shared_secret: Optional[str] = None
    revocation_code: Optional[str] = None
    uri: Optional[str] = None
    token_gid: Optional[str] = None
    secret_1: Optional[str] = None
    serial_number: Optional[str] = None
    server_time: Optional[int] = None
    confirm_type: Optional[int] = None

class AccountValidator(BaseModel):
    """Validator for account data."""
    id: str
    user: UserValidator
    email: EmailValidator
    vault: VaultValidator
    steamguard: Optional[SteamguardValidator] = None
    prime: Optional[bool] = False
    lock: Optional[bool] = False
    perm_lock: Optional[bool] = False
    
    @validator('id')
    def id_must_be_valid(cls, v):
        try:
            int(v)
            return v
        except ValueError:
            raise ValueError("Account ID must be a valid integer")

def validate_account_data(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate account data.
    
    Args:
        data: The account data to validate
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    try:
        AccountValidator(**data)
    except ValidationError as e:
        for error in e.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"]
            })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_card_data(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate card data.
    
    Args:
        data: The card data to validate
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate code1
    if "code1" not in data:
        errors.append({
            "field": "code1",
            "message": "code1 is required"
        })
    elif not isinstance(data["code1"], str):
        errors.append({
            "field": "code1",
            "message": f"code1 must be a string, got {type(data['code1']).__name__}"
        })
    elif len(data["code1"]) == 0:
        errors.append({
            "field": "code1",
            "message": "code1 cannot be empty"
        })
    
    # Validate code2 (optional)
    if "code2" in data and data["code2"] is not None:
        if not isinstance(data["code2"], str):
            errors.append({
                "field": "code2",
                "message": f"code2 must be a string, got {type(data['code2']).__name__}"
            })
    
    # Validate redeemed (optional)
    if "redeemed" in data:
        redeemed_result = validate_boolean(data["redeemed"])
        if not redeemed_result.valid:
            for error in redeemed_result.errors:
                error["field"] = "redeemed"
                errors.append(error)
    
    # Validate failed (optional)
    if "failed" in data and data["failed"] is not None:
        if not isinstance(data["failed"], str):
            errors.append({
                "field": "failed",
                "message": f"failed must be a string, got {type(data['failed']).__name__}"
            })
    
    # Validate lock (optional)
    if "lock" in data:
        lock_result = validate_boolean(data["lock"])
        if not lock_result.valid:
            for error in lock_result.errors:
                error["field"] = "lock"
                errors.append(error)
    
    # Validate perm_lock (optional)
    if "perm_lock" in data:
        perm_lock_result = validate_boolean(data["perm_lock"])
        if not perm_lock_result.valid:
            for error in perm_lock_result.errors:
                error["field"] = "perm_lock"
                errors.append(error)
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_hardware_data(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate hardware data.
    
    Args:
        data: The hardware data to validate
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate acc_id
    if "acc_id" not in data:
        errors.append({
            "field": "acc_id",
            "message": "acc_id is required"
        })
    else:
        acc_id_result = validate_integer(data["acc_id"])
        if not acc_id_result.valid:
            for error in acc_id_result.errors:
                error["field"] = "acc_id"
                errors.append(error)
    
    # Validate other fields (all optional)
    optional_string_fields = [
        "bios_vendor", "bios_version", "disk_serial", "disk_model",
        "smbios_uuid", "mb_manufacturer", "mb_product", "mb_version", "mb_serial",
        "mac_address", "vmid", "pcname", "machine_guid", "hwprofile_guid"
    ]
    
    for field in optional_string_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], str):
                errors.append({
                    "field": field,
                    "message": f"{field} must be a string, got {type(data[field]).__name__}"
                })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_pagination_params(limit: Any, offset: Any) -> ValidationResult:
    """
    Validate pagination parameters.
    
    Args:
        limit: The limit parameter
        offset: The offset parameter
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate limit
    limit_result = validate_integer(limit, min_value=1, max_value=1000)
    if not limit_result.valid:
        for error in limit_result.errors:
            error["field"] = "limit"
            errors.append(error)
    
    # Validate offset
    offset_result = validate_integer(offset, min_value=0)
    if not offset_result.valid:
        for error in offset_result.errors:
            error["field"] = "offset"
            errors.append(error)
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_sort_params(sort_by: str, sort_order: str, allowed_fields: List[str]) -> ValidationResult:
    """
    Validate sorting parameters.
    
    Args:
        sort_by: The sort_by parameter
        sort_order: The sort_order parameter
        allowed_fields: A list of allowed fields to sort by
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate sort_by
    if sort_by not in allowed_fields:
        errors.append({
            "field": "sort_by",
            "message": f"sort_by must be one of {', '.join(allowed_fields)}"
        })
    
    # Validate sort_order
    if sort_order not in ["asc", "desc"]:
        errors.append({
            "field": "sort_order",
            "message": "sort_order must be 'asc' or 'desc'"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_search_param(search: str) -> ValidationResult:
    """
    Validate search parameter.
    
    Args:
        search: The search parameter
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate search
    if not isinstance(search, str):
        errors.append({
            "field": "search",
            "message": f"search must be a string, got {type(search).__name__}"
        })
    elif len(search) > 100:
        errors.append({
            "field": "search",
            "message": "search must be at most 100 characters long"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)

def validate_filter_params(params: Dict[str, Any], allowed_filters: List[str]) -> ValidationResult:
    """
    Validate filter parameters.
    
    Args:
        params: The filter parameters
        allowed_filters: A list of allowed filter names
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    for key, value in params.items():
        if key.startswith("filter_"):
            filter_name = key[7:]  # Remove "filter_" prefix
            if filter_name not in allowed_filters:
                errors.append({
                    "field": key,
                    "message": f"Unknown filter: {filter_name}. Allowed filters: {', '.join(allowed_filters)}"
                })
            else:
                # Validate filter value based on filter name
                if filter_name in ["prime", "lock", "perm_lock"]:
                    filter_result = validate_boolean(value)
                    if not filter_result.valid:
                        for error in filter_result.errors:
                            error["field"] = key
                            errors.append(error)
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)
