"""
Script to get database schema information.
"""

import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.db import get_db_connection

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

def get_db_schema():
    """Get database schema information."""
    print("Getting database schema information...")
    
    with get_db_connection() as conn:
        if conn is None:
            print("No database connection available")
            return
        
        cursor = conn.cursor()
        try:
            # Get tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print("\nTables:")
            for table in tables:
                print(f"- {table[0]}")
                
                # Get columns for each table
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table[0]}'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                print(f"  Columns for {table[0]}:")
                for column in columns:
                    print(f"  - {column[0]}, Type: {column[1]}, Nullable: {column[2]}")
                
                # Get foreign keys for each table
                cursor.execute(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = '{table[0]}';
                """)
                foreign_keys = cursor.fetchall()
                if foreign_keys:
                    print(f"  Foreign Keys for {table[0]}:")
                    for fk in foreign_keys:
                        print(f"  - {fk[0]} references {fk[1]}({fk[2]})")
            
            # Get views
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            views = cursor.fetchall()
            print("\nViews:")
            for view in views:
                print(f"- {view[0]}")
                
                # Get view definition
                cursor.execute(f"""
                    SELECT view_definition
                    FROM information_schema.views
                    WHERE table_name = '{view[0]}'
                    AND table_schema = 'public';
                """)
                view_def = cursor.fetchone()
                if view_def:
                    print(f"  Definition: {view_def[0][:100]}...")
            
            # Get RLS policies
            cursor.execute("""
                SELECT tablename, policyname, roles, cmd, qual
                FROM pg_policies
                ORDER BY tablename, policyname;
            """)
            policies = cursor.fetchall()
            print("\nRLS Policies:")
            for policy in policies:
                print(f"- Table: {policy[0]}, Policy: {policy[1]}")
                print(f"  Roles: {policy[2]}")
                print(f"  Command: {policy[3]}")
                print(f"  Using: {policy[4]}")
            
        except Exception as e:
            print(f"Error getting database schema: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    get_db_schema()
