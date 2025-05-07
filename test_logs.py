#!/usr/bin/env python3
"""
Test script for the logs API.

This script tests the logs API by creating a log entry.
"""

import requests
import json
import sys
import logging
import hashlib
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    # API configuration
    base_url = "http://localhost:8080"

    # Try to authenticate
    logger.info("Authenticating...")
    # Try to authenticate with different credentials
    credentials = [
        {"username": "admin", "password": "admin123"},
        {"username": "user", "password": "user123"},
        {"username": "admin", "password": "password"},
        {"username": "user", "password": "password"}
    ]

    auth_response = None
    for cred in credentials:
        logger.info(f"Trying to authenticate with username: {cred['username']}")
        try:
            auth_response = requests.post(
                f"{base_url}/auth/token",
                data=cred,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            if auth_response.status_code == 200:
                logger.info(f"Authentication successful with username: {cred['username']}")
                break
            else:
                logger.info(f"Authentication failed with username: {cred['username']}, status code: {auth_response.status_code}")
        except Exception as e:
            logger.error(f"Error during authentication with username: {cred['username']}: {e}")

    if auth_response is None or auth_response.status_code != 200:
        logger.error("All authentication attempts failed")
        return 1

    if auth_response.status_code != 200:
        logger.error(f"Authentication failed: {auth_response.status_code} {auth_response.text}")
        return 1

    auth_data = auth_response.json()
    access_token = auth_data.get("access_token")

    if not access_token:
        logger.error("No access token in response")
        return 1

    logger.info(f"Authentication successful. Token: {access_token[:10]}...")

    # Create a log entry
    logger.info("Creating log entry...")
    log_data = {
        "message": "Test log entry from test_logs.py",
        "level": "INFO",
        "category": "system",
        "source": "test_script",
        "details": {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
    }

    log_response = requests.post(
        f"{base_url}/logs",
        json=log_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )

    if log_response.status_code != 200 and log_response.status_code != 201:
        logger.error(f"Failed to create log entry: {log_response.status_code} {log_response.text}")
        return 1

    logger.info(f"Log entry created successfully: {log_response.text}")

    # Check if the log entry was created
    logger.info("Checking logs...")
    logs_response = requests.get(
        f"{base_url}/logs",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if logs_response.status_code != 200:
        logger.error(f"Failed to get logs: {logs_response.status_code} {logs_response.text}")
        return 1

    logs_data = logs_response.json()
    logger.info(f"Found {logs_data.get('total', 0)} logs")

    return 0

if __name__ == "__main__":
    sys.exit(main())
