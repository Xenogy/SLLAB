"""
Script to check the users table schema.
"""

import os
import sys
from dotenv import load_dotenv
from db import get_db_connection

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def check_users_schema():
    """Check the users table schema."""
    print("Checking users table schema...")
    
    with get_db_connection() as db_conn:
        if db_conn is None:
            print("No database connection available")
            return
        
        cursor = db_conn.cursor()
        try:
            # Check if users table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """)
            exists = cursor.fetchone()[0]
            if not exists:
                print("Users table does not exist")
                return
            
            # Get users table schema
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print("Users table schema:")
            for column in columns:
                print(f"  {column[0]}, Type: {column[1]}, Nullable: {column[2]}")
            
            # Get users table data
            cursor.execute("""
                SELECT * FROM users LIMIT 10;
            """)
            users = cursor.fetchall()
            print("\nUsers table data:")
            for user in users:
                print(f"  {user}")
            
        except Exception as e:
            print(f"Error checking users schema: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    check_users_schema()
