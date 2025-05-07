#!/usr/bin/env python3
"""
Test script for API key authentication.
"""

import psycopg2
import json
import sys
import logging
import hashlib
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    try:
        # Connect to the database
        logger.info("Connecting to the database...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="accountdb",
            user="ps_user",
            password="BALLS123"
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Generate a test API key
        api_key = "test_api_key_123"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Insert API key
        logger.info("Inserting API key...")
        cursor.execute(
            """
            INSERT INTO api_keys (
                user_id, key_name, api_key, api_key_prefix, scopes, key_type
            )
            VALUES (
                %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                1,
                "Test API Key",
                api_key_hash,
                api_key[:8],
                ["read", "write"],
                "test"
            )
        )
        
        # Get the inserted API key ID
        api_key_id = cursor.fetchone()[0]
        
        # Commit the transaction
        conn.commit()
        
        logger.info(f"API key inserted successfully with ID: {api_key_id}")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        # Test the API key
        logger.info("Testing API key...")
        base_url = "http://localhost:8080"
        
        # Create a log entry
        log_data = {
            "message": "Test log entry from test_api_key.py",
            "level": "INFO",
            "category": "system",
            "source": "test_script",
            "details": {
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Try with API key in query parameter
        logger.info("Trying with API key in query parameter...")
        response = requests.post(
            f"{base_url}/logs?api_key={api_key}",
            json=log_data,
            headers={
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response text: {response.text}")
        
        # Try with API key in header
        logger.info("Trying with API key in header...")
        response = requests.post(
            f"{base_url}/logs",
            json=log_data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key
            }
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response text: {response.text}")
        
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
