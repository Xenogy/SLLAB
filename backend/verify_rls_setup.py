"""
Script to verify that RLS is set up correctly.
"""

import os
import sys
from dotenv import load_dotenv
from db import get_db_connection

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def verify_rls_setup():
    """Verify that RLS is set up correctly."""
    print("Verifying RLS setup...")
    
    with get_db_connection() as db_conn:
        if db_conn is None:
            print("No database connection available")
            return
        
        cursor = db_conn.cursor()
        try:
            # Check if app.current_user_id and app.current_user_role parameters exist
            cursor.execute("""
                SELECT name, setting
                FROM pg_settings
                WHERE name LIKE 'app.current_user%'
            """)
            
            settings = cursor.fetchall()
            if settings:
                print("App settings:")
                for setting in settings:
                    print(f"  {setting[0]} = {setting[1]}")
            else:
                print("No app.current_user settings found")
                print("Creating app.current_user settings...")
                cursor.execute("ALTER DATABASE accountdb SET app.current_user_id = '0'")
                cursor.execute("ALTER DATABASE accountdb SET app.current_user_role = 'none'")
            
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
            
            # Check if accounts_with_rls view exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name = 'accounts_with_rls'
                );
            """)
            accounts_view_exists = cursor.fetchone()[0]
            
            if accounts_view_exists:
                print("accounts_with_rls view exists")
            else:
                print("accounts_with_rls view does not exist")
            
            # Check if cards_with_rls view exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name = 'cards_with_rls'
                );
            """)
            cards_view_exists = cursor.fetchone()[0]
            
            if cards_view_exists:
                print("cards_with_rls view exists")
            else:
                print("cards_with_rls view does not exist")
            
            # Check if hardware_profiles_with_rls view exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hardware_profiles_with_rls'
                );
            """)
            hardware_profiles_view_exists = cursor.fetchone()[0]
            
            if hardware_profiles_view_exists:
                print("hardware_profiles_with_rls view exists")
            else:
                print("hardware_profiles_with_rls view does not exist")
            
            # Test RLS with different users
            print("\nTesting RLS with different users...")
            
            # Test as admin
            cursor.execute("SET app.current_user_id = '1'")
            cursor.execute("SET app.current_user_role = 'admin'")
            cursor.execute("SELECT COUNT(*) FROM accounts_with_rls")
            admin_count = cursor.fetchone()[0]
            print(f"Admin can see {admin_count} accounts")
            
            # Test as user 2
            cursor.execute("SET app.current_user_id = '2'")
            cursor.execute("SET app.current_user_role = 'user'")
            cursor.execute("SELECT COUNT(*) FROM accounts_with_rls")
            user2_count = cursor.fetchone()[0]
            print(f"User 2 can see {user2_count} accounts")
            
            # Test as user 3
            cursor.execute("SET app.current_user_id = '3'")
            cursor.execute("SET app.current_user_role = 'user'")
            cursor.execute("SELECT COUNT(*) FROM accounts_with_rls")
            user3_count = cursor.fetchone()[0]
            print(f"User 3 can see {user3_count} accounts")
            
            # Verify RLS is working correctly
            if admin_count >= user2_count and admin_count >= user3_count:
                print("\nRLS verification: Admin can see all accounts (PASS)")
            else:
                print("\nRLS verification: Admin cannot see all accounts (FAIL)")
            
            if user2_count < admin_count:
                print("RLS verification: User 2 can see fewer accounts than admin (PASS)")
            else:
                print("RLS verification: User 2 can see as many accounts as admin (FAIL)")
            
            if user3_count < admin_count:
                print("RLS verification: User 3 can see fewer accounts than admin (PASS)")
            else:
                print("RLS verification: User 3 can see as many accounts as admin (FAIL)")
            
            # Overall verification
            if (admin_count >= user2_count and admin_count >= user3_count and 
                user2_count < admin_count and user3_count < admin_count):
                print("\nRLS is set up correctly!")
            else:
                print("\nRLS may not be set up correctly. Please check the configuration.")
            
        except Exception as e:
            print(f"Error verifying RLS setup: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    verify_rls_setup()
