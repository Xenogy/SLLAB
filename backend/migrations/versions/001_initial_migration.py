"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-04-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is just a placeholder migration since we're using SQL scripts for schema
    pass


def downgrade() -> None:
    # This is just a placeholder migration since we're using SQL scripts for schema
    pass
