"""
Script to create test accounts for different users to test RLS.
"""

import os
import sys
from dotenv import load_dotenv
from db import get_db_connection

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def create_test_accounts():
    """Create test accounts for different users."""
    print("Creating test accounts...")

    with get_db_connection() as db_conn:
        if db_conn is None:
            print("No database connection available")
            return

        cursor = db_conn.cursor()
        try:
            # Create test users if they don't exist
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, email, role, is_active, created_at)
                VALUES
                    (1, 'admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin@example.com', 'admin', TRUE, NOW()),
                    (2, 'user2', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'user2@example.com', 'user', TRUE, NOW()),
                    (3, 'user3', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'user3@example.com', 'user', TRUE, NOW())
                ON CONFLICT (id) DO NOTHING;
            """)
            print("Created test users")

            # Create test accounts for user 1 (admin)
            cursor.execute("""
                INSERT INTO accounts (
                    acc_id,
                    acc_username,
                    acc_password,
                    acc_email_address,
                    acc_email_password,
                    acc_vault_address,
                    acc_vault_password,
                    acc_created_at,
                    acc_session_start,
                    acc_steamguard_account_name,
                    acc_confirm_type,
                    acc_device_id,
                    acc_identity_secret,
                    acc_revocation_code,
                    acc_secret_1,
                    acc_serial_number,
                    acc_server_time,
                    acc_shared_secret,
                    acc_status,
                    acc_token_gid,
                    acc_uri,
                    prime,
                    lock,
                    perm_lock,
                    owner_id
                ) VALUES (
                    '76561199826722001',
                    'admin_account1',
                    'password123',
                    'admin_account1@example.com',
                    'email_password',
                    'vault_address',
                    'vault_password',
                    1620000000,
                    1620000000,
                    'steamguard_account_name',
                    0,
                    'device_id',
                    'identity_secret',
                    'revocation_code',
                    'secret_1',
                    'serial_number',
                    '123456789',
                    'shared_secret',
                    0,
                    'token_gid',
                    'uri',
                    FALSE,
                    FALSE,
                    FALSE,
                    1
                )
                ON CONFLICT (acc_id) DO UPDATE SET
                    owner_id = 1
                RETURNING acc_id;
            """)
            result = cursor.fetchone()
            if result:
                print(f"Created account {result[0]} owned by user 1 (admin)")

            # Create test accounts for user 2
            cursor.execute("""
                INSERT INTO accounts (
                    acc_id,
                    acc_username,
                    acc_password,
                    acc_email_address,
                    acc_email_password,
                    acc_vault_address,
                    acc_vault_password,
                    acc_created_at,
                    acc_session_start,
                    acc_steamguard_account_name,
                    acc_confirm_type,
                    acc_device_id,
                    acc_identity_secret,
                    acc_revocation_code,
                    acc_secret_1,
                    acc_serial_number,
                    acc_server_time,
                    acc_shared_secret,
                    acc_status,
                    acc_token_gid,
                    acc_uri,
                    prime,
                    lock,
                    perm_lock,
                    owner_id
                ) VALUES (
                    '76561199826722002',
                    'user2_account1',
                    'password123',
                    'user2_account1@example.com',
                    'email_password',
                    'vault_address',
                    'vault_password',
                    1620000000,
                    1620000000,
                    'steamguard_account_name',
                    0,
                    'device_id',
                    'identity_secret',
                    'revocation_code',
                    'secret_1',
                    'serial_number',
                    '123456789',
                    'shared_secret',
                    0,
                    'token_gid',
                    'uri',
                    FALSE,
                    FALSE,
                    FALSE,
                    2
                )
                ON CONFLICT (acc_id) DO UPDATE SET
                    owner_id = 2
                RETURNING acc_id;
            """)
            result = cursor.fetchone()
            if result:
                print(f"Created account {result[0]} owned by user 2")

            # Create test accounts for user 3
            cursor.execute("""
                INSERT INTO accounts (
                    acc_id,
                    acc_username,
                    acc_password,
                    acc_email_address,
                    acc_email_password,
                    acc_vault_address,
                    acc_vault_password,
                    acc_created_at,
                    acc_session_start,
                    acc_steamguard_account_name,
                    acc_confirm_type,
                    acc_device_id,
                    acc_identity_secret,
                    acc_revocation_code,
                    acc_secret_1,
                    acc_serial_number,
                    acc_server_time,
                    acc_shared_secret,
                    acc_status,
                    acc_token_gid,
                    acc_uri,
                    prime,
                    lock,
                    perm_lock,
                    owner_id
                ) VALUES (
                    '76561199826722003',
                    'user3_account1',
                    'password123',
                    'user3_account1@example.com',
                    'email_password',
                    'vault_address',
                    'vault_password',
                    1620000000,
                    1620000000,
                    'steamguard_account_name',
                    0,
                    'device_id',
                    'identity_secret',
                    'revocation_code',
                    'secret_1',
                    'serial_number',
                    '123456789',
                    'shared_secret',
                    0,
                    'token_gid',
                    'uri',
                    FALSE,
                    FALSE,
                    FALSE,
                    3
                )
                ON CONFLICT (acc_id) DO UPDATE SET
                    owner_id = 3
                RETURNING acc_id;
            """)
            result = cursor.fetchone()
            if result:
                print(f"Created account {result[0]} owned by user 3")

            # Verify account ownership
            cursor.execute("""
                SELECT acc_id, owner_id FROM accounts
            """)
            accounts = cursor.fetchall()
            print("\nAccount ownership:")
            for account in accounts:
                print(f"  Account ID: {account[0]}, Owner ID: {account[1]}")

            db_conn.commit()
            print("Test accounts created successfully!")

        except Exception as e:
            db_conn.rollback()
            print(f"Error creating test accounts: {e}")
        finally:
            cursor.close()

if __name__ == "__main__":
    create_test_accounts()
