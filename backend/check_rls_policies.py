"""
Script to check RLS policies in the database.
"""

import os
import sys
from dotenv import load_dotenv
from db import get_db_connection

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def check_rls_policies():
    """Check RLS policies in the database."""
    print("Checking RLS policies...")
    
    with get_db_connection() as db_conn:
        if db_conn is None:
            print("No database connection available")
            return
        
        cursor = db_conn.cursor()
        try:
            # Check if RLS is enabled on accounts table
            cursor.execute("""
                SELECT relname, relrowsecurity
                FROM pg_class
                WHERE relname = 'accounts'
            """)
            result = cursor.fetchone()
            if result:
                print(f"Table: {result[0]}, RLS enabled: {result[1]}")
            else:
                print("Accounts table not found")
            
            # Check RLS policies on accounts table
            cursor.execute("""
                SELECT schemaname, tablename, policyname, roles, cmd, qual
                FROM pg_policies
                WHERE tablename = 'accounts'
            """)
            
            policies = cursor.fetchall()
            if policies:
                print("\nRLS policies for accounts table:")
                for policy in policies:
                    print(f"  Schema: {policy[0]}")
                    print(f"  Table: {policy[1]}")
                    print(f"  Policy: {policy[2]}")
                    print(f"  Roles: {policy[3]}")
                    print(f"  Command: {policy[4]}")
                    print(f"  Using: {policy[5]}")
                    print()
            else:
                print("No RLS policies found for accounts table")
            
            # Check if app.current_user_id and app.current_user_role parameters exist
            cursor.execute("""
                SELECT name, setting
                FROM pg_settings
                WHERE name LIKE 'app.current_user%'
            """)
            
            settings = cursor.fetchall()
            if settings:
                print("\nApp settings:")
                for setting in settings:
                    print(f"  {setting[0]} = {setting[1]}")
            else:
                print("No app.current_user settings found")
            
            # Try to set and get app.current_user_id and app.current_user_role
            try:
                cursor.execute("SET app.current_user_id = '3'")
                cursor.execute("SET app.current_user_role = 'user'")
                
                cursor.execute("SELECT current_setting('app.current_user_id'), current_setting('app.current_user_role')")
                result = cursor.fetchone()
                if result:
                    print(f"\nTest setting app parameters:")
                    print(f"  app.current_user_id = {result[0]}")
                    print(f"  app.current_user_role = {result[1]}")
            except Exception as e:
                print(f"\nError setting app parameters: {e}")
            
            # Check accounts owned by user 3
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE owner_id = 3")
            count = cursor.fetchone()[0]
            print(f"\nAccounts owned by user 3: {count}")
            
            # Check all accounts
            cursor.execute("SELECT acc_id, owner_id FROM accounts")
            accounts = cursor.fetchall()
            print("\nAll accounts:")
            for account in accounts:
                print(f"  Account ID: {account[0]}, Owner ID: {account[1]}")
            
        except Exception as e:
            print(f"Error checking RLS policies: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    check_rls_policies()
