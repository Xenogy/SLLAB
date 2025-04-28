"""
Database migration manager.

This module provides functions for managing database migrations using Alembic.
"""

import os
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from alembic.config import Config
from alembic import command

# Configure logging
logger = logging.getLogger(__name__)

def get_alembic_config() -> Config:
    """
    Get the Alembic configuration.

    Returns:
        Config: Alembic configuration
    """
    try:
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Get the migrations directory
        migrations_dir = os.path.join(os.path.dirname(current_dir), 'migrations')

        # Log the paths for debugging
        logger.info(f"Current directory: {current_dir}")
        logger.info(f"Migrations directory: {migrations_dir}")
        logger.info(f"Alembic config file: {os.path.join(migrations_dir, 'alembic.ini')}")

        # Check if the alembic.ini file exists
        if not os.path.exists(os.path.join(migrations_dir, 'alembic.ini')):
            logger.warning(f"alembic.ini not found at {os.path.join(migrations_dir, 'alembic.ini')}")

            # Try to find alembic.ini
            for root, dirs, files in os.walk(os.path.dirname(current_dir)):
                if 'alembic.ini' in files:
                    logger.info(f"Found alembic.ini at {os.path.join(root, 'alembic.ini')}")
                    migrations_dir = root
                    break

        # Create Alembic config
        alembic_cfg = Config(os.path.join(migrations_dir, 'alembic.ini'))

        # Set the script location to the migrations directory
        alembic_cfg.set_main_option('script_location', migrations_dir)

        return alembic_cfg
    except Exception as e:
        logger.error(f"Error getting Alembic config: {e}")
        raise

def get_current_revision() -> Optional[str]:
    """
    Get the current database revision.

    Returns:
        Optional[str]: Current revision or None if no revision
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Use the Python API instead of the command-line interface
        from alembic.script import ScriptDirectory
        from alembic.runtime.environment import EnvironmentContext

        script = ScriptDirectory.from_config(alembic_cfg)

        # Create a function to get the current revision
        def get_revision(rev, context):
            return rev

        # Create an environment context
        with EnvironmentContext(
            alembic_cfg,
            script,
            fn=get_revision
        ) as env:
            # Get the current revision
            current_rev = env.get_current_revision()

        return current_rev
    except Exception as e:
        logger.error(f"Error getting current revision: {e}")
        return None

def get_available_revisions() -> List[str]:
    """
    Get a list of available revisions.

    Returns:
        List[str]: List of available revisions
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Use the Python API instead of the command-line interface
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(alembic_cfg)

        # Get all revisions
        revisions = [rev for rev in script.get_revisions()]

        # Sort revisions by date (newest first)
        revisions.sort(key=lambda x: x.revision_date, reverse=True)

        # Return revision IDs
        return [rev.revision for rev in revisions]
    except Exception as e:
        logger.error(f"Error getting available revisions: {e}")
        return []

def upgrade_to_latest() -> Tuple[bool, str]:
    """
    Upgrade the database to the latest revision.

    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Run the upgrade command
        command.upgrade(alembic_cfg, 'head')

        return True, "Database upgraded to the latest revision"
    except Exception as e:
        logger.error(f"Error upgrading database: {e}")
        return False, f"Error upgrading database: {e}"

def upgrade_to_revision(revision: str) -> Tuple[bool, str]:
    """
    Upgrade the database to a specific revision.

    Args:
        revision (str): Revision to upgrade to

    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Run the upgrade command
        command.upgrade(alembic_cfg, revision)

        return True, f"Database upgraded to revision {revision}"
    except Exception as e:
        logger.error(f"Error upgrading database to revision {revision}: {e}")
        return False, f"Error upgrading database to revision {revision}: {e}"

def downgrade_to_revision(revision: str) -> Tuple[bool, str]:
    """
    Downgrade the database to a specific revision.

    Args:
        revision (str): Revision to downgrade to

    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Run the downgrade command
        command.downgrade(alembic_cfg, revision)

        return True, f"Database downgraded to revision {revision}"
    except Exception as e:
        logger.error(f"Error downgrading database to revision {revision}: {e}")
        return False, f"Error downgrading database to revision {revision}: {e}"

def create_migration(message: str) -> Tuple[bool, str]:
    """
    Create a new migration.

    Args:
        message (str): Migration message

    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Run the revision command
        command.revision(alembic_cfg, message=message, autogenerate=False)

        return True, f"Created new migration: {message}"
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        return False, f"Error creating migration: {e}"

def create_auto_migration(message: str) -> Tuple[bool, str]:
    """
    Create a new migration with autogenerate.

    Args:
        message (str): Migration message

    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Get Alembic config
        alembic_cfg = get_alembic_config()

        # Run the revision command with autogenerate
        command.revision(alembic_cfg, message=message, autogenerate=True)

        return True, f"Created new auto-generated migration: {message}"
    except Exception as e:
        logger.error(f"Error creating auto-generated migration: {e}")
        return False, f"Error creating auto-generated migration: {e}"

def get_migration_status() -> Dict[str, Any]:
    """
    Get the status of migrations.

    Returns:
        Dict[str, Any]: Migration status
    """
    try:
        # Get current revision
        current_revision = get_current_revision()

        # Get available revisions
        available_revisions = get_available_revisions()

        # Check if database is up to date
        is_up_to_date = current_revision == available_revisions[0] if available_revisions else False

        return {
            "current_revision": current_revision,
            "available_revisions": available_revisions,
            "is_up_to_date": is_up_to_date
        }
    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        return {
            "error": str(e)
        }
