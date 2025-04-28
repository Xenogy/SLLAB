"""Add indexes to improve performance

Revision ID: 002
Revises: 001
Create Date: 2023-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes to accounts table
    op.create_index('idx_accounts_owner_id', 'accounts', ['owner_id'], unique=False)
    op.create_index('idx_accounts_acc_username', 'accounts', ['acc_username'], unique=False)
    op.create_index('idx_accounts_acc_email_address', 'accounts', ['acc_email_address'], unique=False)
    op.create_index('idx_accounts_prime', 'accounts', ['prime'], unique=False)
    op.create_index('idx_accounts_lock', 'accounts', ['lock'], unique=False)
    op.create_index('idx_accounts_perm_lock', 'accounts', ['perm_lock'], unique=False)
    
    # Add indexes to hardware table
    op.create_index('idx_hardware_owner_id', 'hardware', ['owner_id'], unique=False)
    op.create_index('idx_hardware_account_id', 'hardware', ['account_id'], unique=False)
    op.create_index('idx_hardware_type', 'hardware', ['type'], unique=False)
    
    # Add indexes to vms table
    op.create_index('idx_vms_owner_id', 'vms', ['owner_id'], unique=False)
    op.create_index('idx_vms_proxmox_node_id', 'vms', ['proxmox_node_id'], unique=False)
    op.create_index('idx_vms_vmid', 'vms', ['vmid'], unique=False)
    op.create_index('idx_vms_status', 'vms', ['status'], unique=False)
    
    # Add indexes to proxmox_nodes table
    op.create_index('idx_proxmox_nodes_owner_id', 'proxmox_nodes', ['owner_id'], unique=False)
    op.create_index('idx_proxmox_nodes_status', 'proxmox_nodes', ['status'], unique=False)
    
    # Add indexes to whitelist table
    op.create_index('idx_whitelist_vm_id', 'whitelist', ['vm_id'], unique=False)
    op.create_index('idx_whitelist_user_id', 'whitelist', ['user_id'], unique=False)
    
    # Add indexes to users table
    op.create_index('idx_users_username', 'users', ['username'], unique=False)
    op.create_index('idx_users_email', 'users', ['email'], unique=False)
    op.create_index('idx_users_is_admin', 'users', ['is_admin'], unique=False)
    
    # Add indexes to cards table
    op.create_index('idx_cards_owner_id', 'cards', ['owner_id'], unique=False)
    op.create_index('idx_cards_account_id', 'cards', ['account_id'], unique=False)


def downgrade() -> None:
    # Drop indexes from accounts table
    op.drop_index('idx_accounts_owner_id', table_name='accounts')
    op.drop_index('idx_accounts_acc_username', table_name='accounts')
    op.drop_index('idx_accounts_acc_email_address', table_name='accounts')
    op.drop_index('idx_accounts_prime', table_name='accounts')
    op.drop_index('idx_accounts_lock', table_name='accounts')
    op.drop_index('idx_accounts_perm_lock', table_name='accounts')
    
    # Drop indexes from hardware table
    op.drop_index('idx_hardware_owner_id', table_name='hardware')
    op.drop_index('idx_hardware_account_id', table_name='hardware')
    op.drop_index('idx_hardware_type', table_name='hardware')
    
    # Drop indexes from vms table
    op.drop_index('idx_vms_owner_id', table_name='vms')
    op.drop_index('idx_vms_proxmox_node_id', table_name='vms')
    op.drop_index('idx_vms_vmid', table_name='vms')
    op.drop_index('idx_vms_status', table_name='vms')
    
    # Drop indexes from proxmox_nodes table
    op.drop_index('idx_proxmox_nodes_owner_id', table_name='proxmox_nodes')
    op.drop_index('idx_proxmox_nodes_status', table_name='proxmox_nodes')
    
    # Drop indexes from whitelist table
    op.drop_index('idx_whitelist_vm_id', table_name='whitelist')
    op.drop_index('idx_whitelist_user_id', table_name='whitelist')
    
    # Drop indexes from users table
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_is_admin', table_name='users')
    
    # Drop indexes from cards table
    op.drop_index('idx_cards_owner_id', table_name='cards')
    op.drop_index('idx_cards_account_id', table_name='cards')
