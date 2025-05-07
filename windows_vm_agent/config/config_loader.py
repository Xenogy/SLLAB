"""
Configuration loader for the Windows VM Agent.

This module handles loading and validating the YAML configuration file.
"""
import os
import logging
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and validates the agent configuration from a YAML file."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the configuration file. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "config.yaml"
        )
        self.config = None
    
    def load(self) -> Dict[str, Any]:
        """
        Load the configuration from the YAML file.
        
        Returns:
            Dict containing the configuration.
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the YAML file is invalid.
        """
        try:
            logger.info(f"Loading configuration from {self.config_path}")
            with open(self.config_path, 'r') as config_file:
                self.config = yaml.safe_load(config_file)
            
            self._validate_config()
            return self.config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            raise
    
    def _validate_config(self) -> None:
        """
        Validate the loaded configuration.
        
        Raises:
            ValueError: If the configuration is invalid.
        """
        if not self.config:
            raise ValueError("Empty configuration")
        
        # Validate General section
        if 'General' not in self.config:
            raise ValueError("Missing 'General' section in configuration")
        
        general = self.config['General']
        required_general_keys = ['VMIdentifier', 'APIKey', 'ManagerBaseURL', 'ScriptsPath']
        for key in required_general_keys:
            if key not in general:
                raise ValueError(f"Missing required key '{key}' in General section")
        
        # Validate EventMonitors section
        if 'EventMonitors' not in self.config:
            raise ValueError("Missing 'EventMonitors' section in configuration")
        
        if not isinstance(self.config['EventMonitors'], list):
            raise ValueError("'EventMonitors' must be a list")
        
        for i, monitor in enumerate(self.config['EventMonitors']):
            if 'Name' not in monitor:
                raise ValueError(f"Monitor at index {i} is missing 'Name'")
            if 'Type' not in monitor:
                raise ValueError(f"Monitor '{monitor.get('Name', f'at index {i}')}' is missing 'Type'")
            if 'EventTriggers' not in monitor or not isinstance(monitor['EventTriggers'], list):
                raise ValueError(f"Monitor '{monitor.get('Name')}' has invalid 'EventTriggers'")
            
            # Validate each event trigger
            for j, trigger in enumerate(monitor['EventTriggers']):
                if 'EventName' not in trigger:
                    raise ValueError(f"Trigger at index {j} in monitor '{monitor.get('Name')}' is missing 'EventName'")
                if 'Regex' not in trigger:
                    raise ValueError(f"Trigger '{trigger.get('EventName')}' is missing 'Regex'")
                if 'Action' not in trigger:
                    raise ValueError(f"Trigger '{trigger.get('EventName')}' is missing 'Action'")
        
        # Validate Actions section
        if 'Actions' not in self.config:
            raise ValueError("Missing 'Actions' section in configuration")
        
        if not isinstance(self.config['Actions'], list):
            raise ValueError("'Actions' must be a list")
        
        for i, action in enumerate(self.config['Actions']):
            if 'Name' not in action:
                raise ValueError(f"Action at index {i} is missing 'Name'")
            if 'Script' not in action:
                raise ValueError(f"Action '{action.get('Name')}' is missing 'Script'")
            
            # ParameterMapping is required
            if 'ParameterMapping' not in action:
                raise ValueError(f"Action '{action.get('Name')}' is missing 'ParameterMapping'")
        
        logger.info("Configuration validation successful")
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the loaded configuration.
        
        Returns:
            The configuration dictionary or None if not loaded.
        """
        return self.config
