"""
Monitor factory for the Windows VM Agent.

This module creates monitor instances based on configuration.
"""
import logging
from typing import Dict, Any, List, Callable

from monitors.base_monitor import BaseMonitor
from monitors.log_file_monitor import LogFileMonitor

logger = logging.getLogger(__name__)

class MonitorFactory:
    """Factory class for creating monitor instances."""

    @staticmethod
    def create_monitors(config: Dict[str, Any], event_callback: Callable) -> List[BaseMonitor]:
        """
        Create monitor instances based on configuration.

        Args:
            config: The full agent configuration.
            event_callback: Callback function to call when an event is triggered.

        Returns:
            List of monitor instances.
        """
        monitors = []

        for monitor_config in config.get('EventMonitors', []):
            monitor_type = monitor_config.get('Type')
            monitor_name = monitor_config.get('Name', 'UnnamedMonitor')

            try:
                if monitor_type == 'LogFileTail':
                    monitor = LogFileMonitor(monitor_config, event_callback)
                    monitors.append(monitor)
                else:
                    logger.warning(f"Unknown monitor type '{monitor_type}' for monitor '{monitor_name}'")
            except Exception as e:
                logger.error(f"Failed to create monitor '{monitor_name}': {str(e)}")

        return monitors
