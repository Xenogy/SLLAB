#!/usr/bin/env python3
"""
Script to directly insert a log entry into the database.
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
        
        # Get category ID
        logger.info("Getting category ID...")
        cursor.execute("SELECT id FROM logs_categories WHERE name = 'system'")
        category_id = cursor.fetchone()[0]
        
        # Get source ID
        logger.info("Getting source ID...")
        cursor.execute("SELECT id FROM logs_sources WHERE name = 'backend'")
        source_id = cursor.fetchone()[0]
        
        # Get level ID
        logger.info("Getting level ID...")
        cursor.execute("SELECT id FROM logs_levels WHERE name = 'INFO'")
        level_id = cursor.fetchone()[0]
        
        # Insert log entry
        logger.info("Inserting log entry...")
        cursor.execute(
            """
            INSERT INTO logs (
                timestamp, category_id, source_id, level_id, message, details,
                entity_type, entity_id, user_id, owner_id, created_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                datetime.now(),
                category_id,
                source_id,
                level_id,
                "Test log entry from insert_log.py",
                json.dumps({"test": True, "timestamp": datetime.now().isoformat()}),
                "test",
                "123",
                1,
                1,
                datetime.now()
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
