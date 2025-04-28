"""
Configuration utility functions for the AccountDB application.

This module provides utility functions for configuration management.
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any, Union, Type, Callable

# Configure logging
logger = logging.getLogger(__name__)

def get_env_var(
    name: str,
    default: Any = None,
    required: bool = False,
    cast_type: Type = str
) -> Any:
    """
    Get an environment variable.
    
    Args:
        name: The name of the environment variable
        default: The default value if the environment variable is not set
        required: Whether the environment variable is required
        cast_type: The type to cast the environment variable to
        
    Returns:
        Any: The environment variable value
        
    Raises:
        ValueError: If the environment variable is required but not set
    """
    value = os.environ.get(name)
    
    if value is None:
        if required:
            raise ValueError(f"Environment variable {name} is required but not set")
        return default
    
    # Cast the value to the specified type
    if cast_type == bool:
        return value.lower() in ("true", "1", "yes", "y", "t")
    elif cast_type == int:
        return int(value)
    elif cast_type == float:
        return float(value)
    elif cast_type == list:
        return value.split(",")
    elif cast_type == dict:
        return json.loads(value)
    else:
        return value

def load_config_file(file_path: str) -> Dict[str, Any]:
    """
    Load a configuration file.
    
    Args:
        file_path: The path to the configuration file
        
    Returns:
        Dict[str, Any]: The configuration
        
    Raises:
        FileNotFoundError: If the configuration file is not found
        json.JSONDecodeError: If the configuration file is not valid JSON
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {file_path}")
        raise

def save_config_file(file_path: str, config: Dict[str, Any]) -> None:
    """
    Save a configuration file.
    
    Args:
        file_path: The path to the configuration file
        config: The configuration to save
        
    Raises:
        PermissionError: If the configuration file cannot be written
    """
    try:
        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
    except PermissionError:
        logger.error(f"Permission denied when writing configuration file: {file_path}")
        raise

def merge_configs(
    base_config: Dict[str, Any],
    override_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge two configurations.
    
    Args:
        base_config: The base configuration
        override_config: The configuration to override the base configuration
        
    Returns:
        Dict[str, Any]: The merged configuration
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def get_config_value(
    config: Dict[str, Any],
    path: str,
    default: Any = None
) -> Any:
    """
    Get a value from a configuration using a path.
    
    Args:
        config: The configuration
        path: The path to the value (e.g., "database.host")
        default: The default value if the path doesn't exist
        
    Returns:
        Any: The value at the path, or the default value if the path doesn't exist
    """
    if not config:
        return default
    
    parts = path.split(".")
    current = config
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current

def set_config_value(
    config: Dict[str, Any],
    path: str,
    value: Any
) -> Dict[str, Any]:
    """
    Set a value in a configuration using a path.
    
    Args:
        config: The configuration
        path: The path to the value (e.g., "database.host")
        value: The value to set
        
    Returns:
        Dict[str, Any]: The updated configuration
    """
    if not config:
        config = {}
    
    parts = path.split(".")
    current = config
    
    for i, part in enumerate(parts[:-1]):
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    
    current[parts[-1]] = value
    
    return config
