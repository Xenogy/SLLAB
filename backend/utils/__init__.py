"""
Utilities package for the AccountDB application.

This package provides utility functions for various tasks, including
string manipulation, date handling, file operations, and more.
"""

from .string_utils import (
    is_valid_uuid, is_valid_email, is_valid_username, is_valid_password,
    is_valid_steam_id, sanitize_string, truncate_string, mask_sensitive_data
)

from .date_utils import (
    get_current_timestamp, format_timestamp, parse_timestamp,
    get_date_from_timestamp, get_timestamp_from_date, get_time_ago
)

from .file_utils import (
    get_file_extension, get_file_size, get_file_mime_type,
    is_valid_file_type, is_valid_file_size, sanitize_filename
)

from .json_utils import (
    parse_json, serialize_json, is_valid_json, json_to_dict,
    dict_to_json, merge_json, extract_json_path
)

from .crypto_utils import (
    generate_random_string, hash_password, verify_password,
    encrypt_data, decrypt_data, generate_token, verify_token
)

from .validation_utils import (
    validate_required_fields, validate_field_type, validate_field_length,
    validate_field_pattern, validate_field_range, validate_field_enum
)

from .logging_utils import (
    setup_logging, get_logger, log_exception, log_request,
    log_response, log_database_query, log_performance
)

__all__ = [
    # String utilities
    'is_valid_uuid', 'is_valid_email', 'is_valid_username', 'is_valid_password',
    'is_valid_steam_id', 'sanitize_string', 'truncate_string', 'mask_sensitive_data',
    
    # Date utilities
    'get_current_timestamp', 'format_timestamp', 'parse_timestamp',
    'get_date_from_timestamp', 'get_timestamp_from_date', 'get_time_ago',
    
    # File utilities
    'get_file_extension', 'get_file_size', 'get_file_mime_type',
    'is_valid_file_type', 'is_valid_file_size', 'sanitize_filename',
    
    # JSON utilities
    'parse_json', 'serialize_json', 'is_valid_json', 'json_to_dict',
    'dict_to_json', 'merge_json', 'extract_json_path',
    
    # Crypto utilities
    'generate_random_string', 'hash_password', 'verify_password',
    'encrypt_data', 'decrypt_data', 'generate_token', 'verify_token',
    
    # Validation utilities
    'validate_required_fields', 'validate_field_type', 'validate_field_length',
    'validate_field_pattern', 'validate_field_range', 'validate_field_enum',
    
    # Logging utilities
    'setup_logging', 'get_logger', 'log_exception', 'log_request',
    'log_response', 'log_database_query', 'log_performance'
]
