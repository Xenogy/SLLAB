#!/usr/bin/env python3
"""
Simple script to directly insert a log entry into the database.
"""

import psycopg2
import json
import sys
import logging
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
        
        # Insert log entry using the add_log_entry function
        logger.info("Inserting log entry...")
        cursor.execute(
            """
            SELECT add_log_entry(
                %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
            ) as log_id
            """,
            (
                datetime.now(),
                "system",
                "backend",
                "INFO",
                "Test log entry from insert_log_simple.py",
                json.dumps({"test": True, "timestamp": datetime.now().isoformat()}),
                "test",
                "123",
                1,
                1,
                None,
                None,
                None
            )
        )
        
        # Get the inserted log ID
        log_id = cursor.fetchone()[0]
        
        # Commit the transaction
        conn.commit()
        
        logger.info(f"Log entry inserted successfully with ID: {log_id}")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
