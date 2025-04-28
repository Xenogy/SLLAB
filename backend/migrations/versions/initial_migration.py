"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2023-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create accounts table
    op.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        acc_id VARCHAR(255) NOT NULL UNIQUE,
        acc_username VARCHAR(255) NOT NULL,
        acc_password VARCHAR(255) NOT NULL,
        acc_email_address VARCHAR(255) NOT NULL,
        acc_email_password VARCHAR(255) NOT NULL,
        acc_vault_address VARCHAR(255),
        acc_vault_password VARCHAR(255),
        acc_created_at BIGINT,
        acc_session_start BIGINT,
        acc_steamguard_account_name VARCHAR(255),
        acc_confirm_type INTEGER,
        acc_device_id VARCHAR(255),
        acc_identity_secret VARCHAR(255),
        acc_revocation_code VARCHAR(255),
        acc_secret_1 VARCHAR(255),
        acc_serial_number VARCHAR(255),
        acc_server_time VARCHAR(255),
        acc_shared_secret VARCHAR(255),
        acc_status INTEGER,
        acc_token_gid VARCHAR(255),
        acc_uri VARCHAR(255),
        prime BOOLEAN DEFAULT FALSE,
        lock BOOLEAN DEFAULT FALSE,
        perm_lock BOOLEAN DEFAULT FALSE,
        farmlabs_upload BOOLEAN DEFAULT FALSE,
        owner_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create hardware table
    op.execute("""
    CREATE TABLE IF NOT EXISTS hardware (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        type VARCHAR(255) NOT NULL,
        specs TEXT,
        account_id INTEGER REFERENCES accounts(id),
        owner_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create proxmox_nodes table
    op.execute("""
    CREATE TABLE IF NOT EXISTS proxmox_nodes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        hostname VARCHAR(255) NOT NULL,
        port INTEGER DEFAULT 8006,
        status VARCHAR(50) DEFAULT 'offline',
        api_key VARCHAR(255),
        last_seen TIMESTAMP,
        owner_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create vms table
    op.execute("""
    CREATE TABLE IF NOT EXISTS vms (
        id SERIAL PRIMARY KEY,
        vmid VARCHAR(50) NOT NULL,
        name VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'stopped',
        cpu_cores INTEGER,
        memory_mb INTEGER,
        disk_gb INTEGER,
        ip_address VARCHAR(50),
        proxmox_node_id INTEGER REFERENCES proxmox_nodes(id),
        owner_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create whitelist table
    op.execute("""
    CREATE TABLE IF NOT EXISTS whitelist (
        id SERIAL PRIMARY KEY,
        vm_id INTEGER REFERENCES vms(id),
        user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(vm_id, user_id)
    );
    """)
    
    # Create cards table
    op.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id SERIAL PRIMARY KEY,
        card_number VARCHAR(255) NOT NULL,
        card_holder VARCHAR(255) NOT NULL,
        expiry_date VARCHAR(10) NOT NULL,
        cvv VARCHAR(10) NOT NULL,
        account_id INTEGER REFERENCES accounts(id),
        owner_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create RLS function
    op.execute("""
    CREATE OR REPLACE FUNCTION set_rls_context(user_id INTEGER, user_role TEXT)
    RETURNS VOID AS $$
    BEGIN
        PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
        PERFORM set_config('app.current_user_role', user_role, FALSE);
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Enable RLS on tables
    tables = ["accounts", "hardware", "cards", "vms", "proxmox_nodes", "whitelist"]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        
        # Create admin policy
        op.execute(f"""
        CREATE POLICY {table}_admin_policy ON {table}
        FOR ALL
        TO PUBLIC
        USING (current_setting('app.current_user_role', TRUE) = 'admin');
        """)
        
        # Create user SELECT policy
        op.execute(f"""
        CREATE POLICY {table}_user_select_policy ON {table}
        FOR SELECT
        TO PUBLIC
        USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        
        # Create user INSERT policy
        op.execute(f"""
        CREATE POLICY {table}_user_insert_policy ON {table}
        FOR INSERT
        TO PUBLIC
        WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        
        # Create user UPDATE policy
        op.execute(f"""
        CREATE POLICY {table}_user_update_policy ON {table}
        FOR UPDATE
        TO PUBLIC
        USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER)
        WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        
        # Create user DELETE policy
        op.execute(f"""
        CREATE POLICY {table}_user_delete_policy ON {table}
        FOR DELETE
        TO PUBLIC
        USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
    
    # Special policy for whitelist table to allow users to see VMs they have access to
    op.execute("""
    CREATE POLICY whitelist_vm_access_policy ON vms
    FOR SELECT
    TO PUBLIC
    USING (id IN (
        SELECT vm_id FROM whitelist
        WHERE user_id = current_setting('app.current_user_id', TRUE)::INTEGER
    ));
    """)


def downgrade() -> None:
    # Drop policies
    tables = ["accounts", "hardware", "cards", "vms", "proxmox_nodes", "whitelist"]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_admin_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_select_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_insert_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_update_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_delete_policy ON {table};")
    
    # Drop special policy for whitelist
    op.execute("DROP POLICY IF EXISTS whitelist_vm_access_policy ON vms;")
    
    # Drop RLS function
    op.execute("DROP FUNCTION IF EXISTS set_rls_context(INTEGER, TEXT);")
    
    # Drop tables in reverse order
    op.execute("DROP TABLE IF EXISTS whitelist;")
    op.execute("DROP TABLE IF EXISTS cards;")
    op.execute("DROP TABLE IF EXISTS vms;")
    op.execute("DROP TABLE IF EXISTS proxmox_nodes;")
    op.execute("DROP TABLE IF EXISTS hardware;")
    op.execute("DROP TABLE IF EXISTS accounts;")
    op.execute("DROP TABLE IF EXISTS users;")
