"""
Base monitor class for the Windows VM Agent.

This module defines the base class for all event monitors.
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Callable, Pattern, Match, Optional

logger = logging.getLogger(__name__)

class EventTrigger:
    """Represents an event trigger defined in the configuration."""
    
    def __init__(self, event_name: str, regex_pattern: str, action: str):
        """
        Initialize an event trigger.
        
        Args:
            event_name: Name of the event.
            regex_pattern: Regular expression pattern to match.
            action: Name of the action to trigger.
        """
        self.event_name = event_name
        self.regex_pattern = regex_pattern
        self.action = action
        self.regex = re.compile(regex_pattern)
    
    def match(self, text: str) -> Optional[Match]:
        """
        Check if the text matches the trigger's regex pattern.
        
        Args:
            text: Text to check against the pattern.
            
        Returns:
            Match object if matched, None otherwise.
        """
        return self.regex.search(text)


class BaseMonitor(ABC):
    """Base class for all event monitors."""
    
    def __init__(self, config: Dict[str, Any], event_callback: Callable[[str, Dict[str, Any]], None]):
        """
        Initialize the base monitor.
        
        Args:
            config: Monitor configuration.
            event_callback: Callback function to call when an event is triggered.
                            Takes event name and captured data as arguments.
        """
        self.name = config.get('Name', 'UnnamedMonitor')
        self.config = config
        self.event_callback = event_callback
        self.triggers = []
        
        # Initialize triggers from config
        for trigger_config in config.get('EventTriggers', []):
            event_name = trigger_config.get('EventName')
            regex = trigger_config.get('Regex')
            action = trigger_config.get('Action')
            
            if event_name and regex and action:
                self.triggers.append(EventTrigger(event_name, regex, action))
            else:
                logger.warning(f"Skipping invalid trigger in monitor '{self.name}'")
    
    def process_line(self, line: str) -> None:
        """
        Process a line of text, checking for trigger matches.
        
        Args:
            line: Line of text to process.
        """
        for trigger in self.triggers:
            match = trigger.match(line)
            if match:
                logger.info(f"Event '{trigger.event_name}' triggered in monitor '{self.name}'")
                
                # Extract named capture groups from the regex match
                captured_data = match.groupdict()
                
                # Call the event callback with the action name and captured data
                self.event_callback(trigger.action, captured_data)
    
    @abstractmethod
    def start(self) -> None:
        """Start the monitor. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the monitor. Must be implemented by subclasses."""
        pass
