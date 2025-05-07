"""
Main agent class for the Windows VM Agent.

This module implements the core agent functionality.
"""
import logging
import time
import socket
import os
from typing import Dict, Any, List, Optional

from config.config_loader import ConfigLoader
from api.api_client import APIClient
from scripts.script_executor import ScriptExecutor
from agent.action_manager import ActionManager
from monitors.monitor_factory import MonitorFactory
from monitors.base_monitor import BaseMonitor

# Import LogClient if available, otherwise use a dummy class
try:
    from utils.log_client import LogClient
    HAS_LOG_CLIENT = True
except ImportError:
    HAS_LOG_CLIENT = False

    # Dummy LogClient for backward compatibility
    class LogClient:
        def __init__(self, *args, **kwargs):
            pass

        def log_info(self, *args, **kwargs):
            pass

        def log_error(self, *args, **kwargs):
            pass

        def log_warning(self, *args, **kwargs):
            pass

        def log_critical(self, *args, **kwargs):
            pass

        def shutdown(self):
            pass

logger = logging.getLogger(__name__)

class Agent:
    """Main agent class that coordinates all components."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            config_path: Path to the configuration file. If None, uses default path.
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = None
        self.api_client = None
        self.script_executor = None
        self.action_manager = None
        self.monitors = []
        self.running = False
        self.log_client = None

    def initialize(self) -> bool:
        """
        Initialize the agent components.

        Returns:
            True if initialization was successful, False otherwise.
        """
        try:
            # Load configuration
            self.config = self.config_loader.load()

            # Get VM identifier or use hostname if not specified
            vm_id = self.config['General'].get('VMIdentifier')
            if not vm_id or vm_id == "VM_HOSTNAME_OR_ID":
                vm_id = socket.gethostname()
                logger.info(f"Using hostname as VM identifier: {vm_id}")
                self.config['General']['VMIdentifier'] = vm_id

            # Initialize components
            self.api_client = APIClient(
                self.config['General']['ManagerBaseURL'],
                self.config['General']['APIKey'],
                vm_id
            )

            # Initialize log client if available
            if HAS_LOG_CLIENT and self.config['General'].get('LoggingEnabled', True):
                try:
                    logger.info("Initializing log client...")
                    self.log_client = LogClient(
                        self.config['General']['ManagerBaseURL'],
                        self.config['General']['APIKey'],
                        vm_id
                    )
                    logger.info("Log client initialized successfully")

                    # Log agent initialization
                    self.log_client.log_info(
                        "Agent initialization started",
                        "system",
                        {
                            "vm_id": vm_id,
                            "manager_url": self.config['General']['ManagerBaseURL'],
                            "scripts_path": self.config['General']['ScriptsPath']
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize log client: {e}")
                    # Continue without log client

            # Test the API key
            logger.info("Testing API key...")
            if not self.api_client.test_api_key():
                error_msg = "API key test failed. The agent may not be able to communicate with the server."
                logger.error(error_msg)
                logger.error("Please check the API key in the configuration file.")
                logger.error(f"Current API key: {self.config['General']['APIKey']}")
                logger.error(f"Current VM ID: {vm_id}")
                logger.error(f"Current Manager URL: {self.config['General']['ManagerBaseURL']}")

                # Log authentication failure
                if self.log_client:
                    self.log_client.log_error(
                        error_msg,
                        "security",
                        {
                            "vm_id": vm_id,
                            "manager_url": self.config['General']['ManagerBaseURL']
                        }
                    )

                # Continue initialization but warn the user
                logger.warning("Continuing with initialization despite API key test failure")
            else:
                success_msg = "API key test passed successfully"
                logger.info(success_msg)

                # Log authentication success
                if self.log_client:
                    self.log_client.log_info(
                        success_msg,
                        "security",
                        {
                            "vm_id": vm_id,
                            "manager_url": self.config['General']['ManagerBaseURL']
                        }
                    )

            self.script_executor = ScriptExecutor(
                self.config['General']['ScriptsPath']
            )

            self.action_manager = ActionManager(
                self.config,
                self.api_client,
                self.script_executor
            )

            # Create monitors
            self.monitors = MonitorFactory.create_monitors(
                self.config,
                self._handle_event
            )

            if not self.monitors:
                warning_msg = "No monitors were created from configuration"
                logger.warning(warning_msg)

                # Log warning
                if self.log_client:
                    self.log_client.log_warning(warning_msg, "system")

            success_msg = "Agent initialization completed successfully"
            logger.info(success_msg)

            # Log successful initialization
            if self.log_client:
                self.log_client.log_info(success_msg, "system", {
                    "monitors_count": len(self.monitors)
                })

            return True

        except Exception as e:
            error_msg = f"Failed to initialize agent: {str(e)}"
            logger.error(error_msg)

            # Log error
            if self.log_client:
                self.log_client.log_critical(error_msg, "system", exception=e)

            return False

    def start(self) -> None:
        """Start the agent and all monitors."""
        if self.running:
            logger.warning("Agent is already running")
            return

        if not self.config:
            if not self.initialize():
                logger.error("Failed to initialize agent, cannot start")
                return

        logger.info("Starting agent")
        self.running = True

        # Start all monitors
        for monitor in self.monitors:
            monitor.start()

        logger.info(f"Agent started with {len(self.monitors)} monitors")

    def stop(self) -> None:
        """Stop the agent and all monitors."""
        if not self.running:
            logger.warning("Agent is not running")
            return

        logger.info("Stopping agent")
        self.running = False

        # Stop all monitors
        for monitor in self.monitors:
            monitor.stop()

        # Shutdown log client if available
        if self.log_client:
            try:
                # Log agent shutdown
                self.log_client.log_info("Agent shutting down", "system")

                # Shutdown log client
                self.log_client.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down log client: {e}")

        logger.info("Agent stopped")

    def run(self) -> None:
        """Run the agent in the foreground."""
        self.start()

        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping agent")
            self.stop()
        except Exception as e:
            logger.error(f"Error in agent main loop: {str(e)}")
            self.stop()

    def _handle_event(self, action_name: str, event_data: Dict[str, Any]) -> None:
        """
        Handle an event by executing the corresponding action.

        Args:
            action_name: Name of the action to execute.
            event_data: Data captured from the event.
        """
        if not self.action_manager:
            error_msg = "Action manager not initialized, cannot handle event"
            logger.error(error_msg)

            # Log error
            if self.log_client:
                self.log_client.log_error(error_msg, "system", {
                    "action_name": action_name,
                    "event_data": event_data
                })

            return

        # Log event handling
        if self.log_client:
            self.log_client.log_info(f"Handling event: {action_name}", "event", {
                "action_name": action_name,
                "event_data": event_data
            })

        self.action_manager.handle_event(action_name, event_data)
