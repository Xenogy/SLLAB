"""
Script to apply RLS to all relevant tables in the database.
"""

import os
import sys
from dotenv import load_dotenv
from db import get_db_connection

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def apply_rls_to_all_tables():
    """Apply RLS to all relevant tables in the database."""
    print("Applying RLS to all tables...")
    
    with get_db_connection() as db_conn:
        if db_conn is None:
            print("No database connection available")
            return
        
        cursor = db_conn.cursor()
        try:
            # Check if hardware_profiles table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hardware_profiles'
                );
            """)
            hardware_profiles_exists = cursor.fetchone()[0]
            
            # Check if cards table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'cards'
                );
            """)
            cards_exists = cursor.fetchone()[0]
            
            # Apply RLS to hardware_profiles table if it exists
            if hardware_profiles_exists:
                print("Applying RLS to hardware_profiles table...")
                
                # Check if owner_id column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'hardware_profiles' 
                        AND column_name = 'owner_id'
                    );
                """)
                owner_id_exists = cursor.fetchone()[0]
                
                if not owner_id_exists:
                    print("Adding owner_id column to hardware_profiles table...")
                    cursor.execute("""
                        ALTER TABLE hardware_profiles 
                        ADD COLUMN owner_id INTEGER REFERENCES users(id);
                    """)
                
                # Enable RLS on hardware_profiles table
                cursor.execute("""
                    ALTER TABLE hardware_profiles ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE hardware_profiles FORCE ROW LEVEL SECURITY;
                """)
                
                # Drop existing policies
                cursor.execute("""
                    DROP POLICY IF EXISTS hardware_profiles_user_policy ON hardware_profiles;
                    DROP POLICY IF EXISTS hardware_profiles_admin_policy ON hardware_profiles;
                """)
                
                # Create new policies
                cursor.execute("""
                    -- Create admin policy
                    CREATE POLICY hardware_profiles_admin_policy ON hardware_profiles
                        FOR ALL
                        TO PUBLIC
                        USING (current_setting('app.current_user_role', TRUE) = 'admin');
                        
                    -- Create user policy
                    CREATE POLICY hardware_profiles_user_policy ON hardware_profiles
                        FOR ALL
                        TO PUBLIC
                        USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
                """)
                
                # Create RLS view
                cursor.execute("""
                    CREATE OR REPLACE VIEW hardware_profiles_with_rls AS
                    SELECT * FROM hardware_profiles
                    WHERE 
                        current_setting('app.current_user_role', TRUE) = 'admin'
                        OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;
                """)
                
                print("RLS applied to hardware_profiles table")
            else:
                print("hardware_profiles table does not exist")
            
            # Apply RLS to cards table if it exists
            if cards_exists:
                print("Applying RLS to cards table...")
                
                # Check if owner_id column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'cards' 
                        AND column_name = 'owner_id'
                    );
                """)
                owner_id_exists = cursor.fetchone()[0]
                
                if not owner_id_exists:
                    print("Adding owner_id column to cards table...")
                    cursor.execute("""
                        ALTER TABLE cards 
                        ADD COLUMN owner_id INTEGER REFERENCES users(id);
                    """)
                
                # Enable RLS on cards table
                cursor.execute("""
                    ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE cards FORCE ROW LEVEL SECURITY;
                """)
                
                # Drop existing policies
                cursor.execute("""
                    DROP POLICY IF EXISTS cards_user_policy ON cards;
                    DROP POLICY IF EXISTS cards_admin_policy ON cards;
                """)
                
                # Create new policies
                cursor.execute("""
                    -- Create admin policy
                    CREATE POLICY cards_admin_policy ON cards
                        FOR ALL
                        TO PUBLIC
                        USING (current_setting('app.current_user_role', TRUE) = 'admin');
                        
                    -- Create user policy
                    CREATE POLICY cards_user_policy ON cards
                        FOR ALL
                        TO PUBLIC
                        USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
                """)
                
                # Create RLS view
                cursor.execute("""
                    CREATE OR REPLACE VIEW cards_with_rls AS
                    SELECT * FROM cards
                    WHERE 
                        current_setting('app.current_user_role', TRUE) = 'admin'
                        OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;
                """)
                
                print("RLS applied to cards table")
            else:
                print("cards table does not exist")
            
            db_conn.commit()
            print("RLS applied to all tables successfully!")
            
        except Exception as e:
            db_conn.rollback()
            print(f"Error applying RLS to tables: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    apply_rls_to_all_tables()
