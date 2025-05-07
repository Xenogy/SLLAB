"""
Log file monitor for the Windows VM Agent.

This module implements a monitor that tails a log file and watches for events.
"""
import os
import time
import logging
import threading
from typing import Dict, Any, Optional

from monitors.base_monitor import BaseMonitor

logger = logging.getLogger(__name__)

class LogFileMonitor(BaseMonitor):
    """Monitor that watches a log file for events."""

    def __init__(self, config: Dict[str, Any], event_callback):
        """
        Initialize the log file monitor.

        Args:
            config: Monitor configuration.
            event_callback: Callback function to call when an event is triggered.
        """
        super().__init__(config, event_callback)
        self.log_file_path = config.get('LogFilePath')
        if not self.log_file_path:
            raise ValueError(f"LogFilePath not specified for monitor '{self.name}'")

        self.running = False
        self.thread = None
        self.check_interval = config.get('CheckIntervalSeconds', 1.0)

    def start(self) -> None:
        """Start the log file monitor in a separate thread."""
        if self.running:
            logger.warning(f"Monitor '{self.name}' is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started log file monitor '{self.name}' for {self.log_file_path}")

    def stop(self) -> None:
        """Stop the log file monitor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning(f"Monitor thread for '{self.name}' did not terminate cleanly")
            self.thread = None
        logger.info(f"Stopped log file monitor '{self.name}'")

    def _monitor_loop(self) -> None:
        """Main monitoring loop that tails the log file."""
        file_position = self._get_file_size()
        print(f"Starting monitor loop for {self.name} watching {self.log_file_path}")
        print(f"Initial file position: {file_position}")

        while self.running:
            try:
                # Check if file exists
                if not os.path.exists(self.log_file_path):
                    print(f"Log file {self.log_file_path} does not exist, waiting...")
                    logger.warning(f"Log file {self.log_file_path} does not exist, waiting...")
                    time.sleep(self.check_interval * 5)  # Wait longer when file doesn't exist
                    continue

                # Check if file was rotated (size decreased)
                current_size = self._get_file_size()
                print(f"Current file size: {current_size}, previous position: {file_position}")

                if current_size < file_position:
                    print(f"Log file {self.log_file_path} appears to have been rotated, resetting position")
                    logger.info(f"Log file {self.log_file_path} appears to have been rotated, resetting position")
                    file_position = 0

                # If file has new content
                if current_size > file_position:
                    print(f"New content detected in {self.log_file_path}, reading from position {file_position}")
                    with open(self.log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(file_position)
                        for line in f:
                            line = line.strip()
                            if line:
                                print(f"Processing line: {line}")
                                self.process_line(line)

                        file_position = f.tell()
                        print(f"New file position: {file_position}")

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"Error in monitor '{self.name}': {str(e)}")
                logger.error(f"Error in monitor '{self.name}': {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval * 2)  # Wait longer after an error

    def _get_file_size(self) -> int:
        """
        Get the current size of the log file.

        Returns:
            Size of the file in bytes, or 0 if the file doesn't exist.
        """
        try:
            return os.path.getsize(self.log_file_path)
        except (FileNotFoundError, OSError):
            return 0
