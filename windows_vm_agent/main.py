"""
Main entry point for the Windows VM Agent.

This module sets up logging and starts the agent.
"""
import os
import sys
import logging
import argparse
from logging.handlers import RotatingFileHandler

from windows_vm_agent.agent.agent import Agent

def setup_logging(log_dir: str, log_level: str = "INFO") -> None:
    """
    Set up logging configuration.

    Args:
        log_dir: Directory to store log files.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Set up logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(numeric_level)
    logger.addHandler(console_handler)

    # Set up file handler (rotating log file)
    log_file = os.path.join(log_dir, 'windows_vm_agent.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(numeric_level)
    logger.addHandler(file_handler)

    # Log startup message
    logging.info(f"Logging initialized at level {log_level}")
    logging.info(f"Log file: {log_file}")

def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Windows VM Agent')

    parser.add_argument(
        '--config',
        help='Path to configuration file',
        default=None
    )

    parser.add_argument(
        '--log-dir',
        help='Directory for log files',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    )

    parser.add_argument(
        '--log-level',
        help='Logging level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
    )

    return parser.parse_args()

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()

    # Set up logging
    setup_logging(args.log_dir, args.log_level)

    # Print debug information
    print(f"Starting Windows VM Agent with log level: {args.log_level}")
    print(f"Log directory: {args.log_dir}")
    print(f"Config path: {args.config}")

    try:
        # Create and start the agent
        print("Creating agent instance...")
        agent = Agent(args.config)
        print("Initializing agent...")
        if agent.initialize():
            print("Agent initialized successfully, starting...")
            agent.run()
        else:
            logging.error("Failed to initialize agent, exiting")
            print("Failed to initialize agent, exiting")
            sys.exit(1)

    except Exception as e:
        logging.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
