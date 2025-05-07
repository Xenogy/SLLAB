"""
Action manager for the Windows VM Agent.

This module handles mapping events to actions and executing them.
"""
import logging
from typing import Dict, Any, List, Optional

from api.api_client import APIClient
from scripts.script_executor import ScriptExecutor

logger = logging.getLogger(__name__)

class Action:
    """Represents an action defined in the configuration."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize an action.

        Args:
            config: Action configuration.
        """
        self.name = config.get('Name')
        self.script = config.get('Script')
        self.api_data_endpoint = config.get('APIDataEndpoint')
        self.parameter_mapping = config.get('ParameterMapping', {})

    def __str__(self) -> str:
        return f"Action(name={self.name}, script={self.script})"


class ActionManager:
    """Manages actions and their execution."""

    def __init__(self, config: Dict[str, Any], api_client: APIClient, script_executor: ScriptExecutor):
        """
        Initialize the action manager.

        Args:
            config: The full agent configuration.
            api_client: API client instance.
            script_executor: Script executor instance.
        """
        self.api_client = api_client
        self.script_executor = script_executor
        self.actions = {}

        # Load actions from config
        for action_config in config.get('Actions', []):
            action_name = action_config.get('Name')
            if action_name:
                self.actions[action_name] = Action(action_config)
            else:
                logger.warning("Skipping action with no name")

    def handle_event(self, action_name: str, event_data: Dict[str, Any]) -> bool:
        """
        Handle an event by executing the corresponding action.

        Args:
            action_name: Name of the action to execute.
            event_data: Data captured from the event.

        Returns:
            True if the action was executed successfully, False otherwise.
        """
        # Find the action
        action = self.actions.get(action_name)
        if not action:
            logger.error(f"Unknown action: {action_name}")
            return False

        logger.info(f"Handling event with action: {action_name}")

        try:
            # Prepare parameters for the script
            parameters = {}

            # If the action has an API endpoint, call it to get data
            api_data = None
            if action.api_data_endpoint:
                api_data = self.api_client.get_data(action.api_data_endpoint, event_data)
                if not api_data:
                    logger.error(f"Failed to get API data for action {action_name}")
                    return False

            # Map parameters from API data and/or event data
            for param_name, data_key in action.parameter_mapping.items():
                # First check if the key is in the API data
                if api_data and data_key in api_data:
                    parameters[param_name] = api_data[data_key]
                # Then check if it's in the event data
                elif data_key in event_data:
                    parameters[param_name] = event_data[data_key]
                else:
                    logger.warning(f"Parameter mapping key '{data_key}' not found in data for action {action_name}")

            # Execute the script
            success, stdout, stderr = self.script_executor.execute_script(action.script, parameters)

            if success:
                logger.info(f"Action {action_name} executed successfully")
                if stdout.strip():
                    logger.debug(f"Script output: {stdout.strip()}")
                return True
            else:
                logger.error(f"Action {action_name} failed: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Error handling event with action {action_name}: {str(e)}")
            return False
