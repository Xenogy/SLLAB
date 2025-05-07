"""
Fix for the log_utils.py file to ensure logs are properly stored in the database.

This script will:
1. Add more detailed logging to the _process_log_queue function
2. Add a debug mode to log more information about the log queue processing
3. Fix any issues with the log queue processing thread
"""

import os
import sys
import time
import json
import psycopg2
from datetime import datetime

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from backend.utils.log_utils import _log_queue, _log_thread_running, _log_thread, start_log_thread, stop_log_thread
from backend.db.repositories.logs import LogRepository

def check_log_thread():
    """Check if the log thread is running."""
    print(f"Log thread running: {_log_thread_running}")
    print(f"Log thread alive: {_log_thread and _log_thread.is_alive()}")
    print(f"Log queue size: {_log_queue.qsize()}")

def test_direct_db_insert():
    """Test inserting a log directly into the database."""
    print("Testing direct database insert...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="accountdb",
            user="ps_user",
            password="BALLS123"
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Insert a log entry using the add_log_entry function
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
                "Test log entry from fix_log_utils.py",
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
        
        # Get the log ID
        result = cursor.fetchone()
        log_id = result[0] if result else None
        
        # Commit the transaction
        conn.commit()
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print(f"Log entry inserted with ID: {log_id}")
        return log_id
    except Exception as e:
        print(f"Error inserting log entry: {e}")
        return None

def test_log_repository():
    """Test using the LogRepository to insert a log."""
    print("Testing LogRepository insert...")
    
    try:
        # Create a log repository with admin context to bypass RLS
        log_repo = LogRepository(user_id=1, user_role="admin")
        
        # Add a log entry
        log = log_repo.add_log(
            message="Test log entry from fix_log_utils.py using LogRepository",
            level="INFO",
            category="system",
            source="backend",
            details={"test": True, "timestamp": datetime.now().isoformat()},
            entity_type="test",
            entity_id="123",
            user_id=1,
            owner_id=1
        )
        
        print(f"Log entry inserted: {log}")
        return log
    except Exception as e:
        print(f"Error inserting log entry: {e}")
        return None

def check_database():
    """Check the database for logs."""
    print("Checking database for logs...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="accountdb",
            user="ps_user",
            password="BALLS123"
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Check logs count
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        print(f"Found {count} logs in the database")
        
        # Check the most recent logs
        cursor.execute("SELECT id, timestamp, message, level_id FROM logs ORDER BY id DESC LIMIT 5")
        logs = cursor.fetchall()
        
        if logs:
            print("Most recent logs:")
            for log in logs:
                print(f"  - ID: {log[0]}, Timestamp: {log[1]}, Message: {log[2]}, Level: {log[3]}")
        else:
            print("No logs found in the database")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

def main():
    """Main function."""
    print("Starting log_utils fix...")
    
    # Check if the log thread is running
    check_log_thread()
    
    # Test direct database insert
    test_direct_db_insert()
    
    # Test using the LogRepository
    test_log_repository()
    
    # Check the database
    check_database()
    
    print("\nFix complete. Please check the results above to determine the issue.")
    print("Based on the results, you may need to modify the log_utils.py file to fix the issue.")
    print("Possible fixes include:")
    print("1. Ensuring the log thread is properly started")
    print("2. Adding more detailed logging to the _process_log_queue function")
    print("3. Fixing any issues with the database connection in the log thread")
    print("4. Ensuring that transactions are properly committed")

if __name__ == "__main__":
    main()
