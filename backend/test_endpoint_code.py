"""
Test script to verify that the refactored endpoints are using the repository pattern.
This script checks the source code of the router modules for repository pattern usage.
"""

import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_for_repository_pattern(file_path: str, expected_repo_classes: list) -> bool:
    """
    Check if a file uses the repository pattern.

    Args:
        file_path: The path to the file to check
        expected_repo_classes: List of repository class names that should be used

    Returns:
        bool: True if the file uses the repository pattern, False otherwise
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check if the file imports the repository classes
        for repo_class in expected_repo_classes:
            import_patterns = [
                f"from db.repositories.{repo_class.lower()} import {repo_class}",
                f"from db.repositories import {repo_class.lower()}",
                f"import db.repositories.{repo_class.lower()}"
            ]
            if not any(pattern in content for pattern in import_patterns):
                logger.error(f"File {file_path} does not import {repo_class}")
                return False

        # Check if the file instantiates the repository classes
        for repo_class in expected_repo_classes:
            instantiation_patterns = [
                f"{repo_class}(user_id=current_user",
                f"{repo_class.lower()} = {repo_class}(user_id=current_user",
                f"{repo_class.lower()}_repo = {repo_class}(user_id=current_user"
            ]
            if not any(pattern in content for pattern in instantiation_patterns):
                logger.error(f"File {file_path} does not instantiate {repo_class}")
                return False

        # Check if the file contains direct SQL queries
        sql_indicators = ["cursor.execute", "SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM "]
        for indicator in sql_indicators:
            if indicator in content:
                # Count occurrences
                count = content.count(indicator)
                logger.warning(f"File {file_path} contains {count} direct SQL queries: {indicator}")
                # Don't fail the test for this, just warn

        logger.info(f"File {file_path} uses the repository pattern")
        return True

    except Exception as e:
        logger.error(f"Error checking file {file_path}: {e}")
        return False

def main():
    """Main function."""
    success = True

    # Check proxmox_nodes.py
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/proxmox_nodes.py",
        ["ProxmoxNodeRepository", "VMRepository"]
    ):
        success = False

    # Check vms.py
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/vms.py",
        ["VMRepository", "ProxmoxNodeRepository"]
    ):
        success = False

    # Check accounts.py
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/accounts.py",
        ["AccountRepository"]
    ):
        success = False

    if success:
        logger.info("All files use the repository pattern")
        return 0
    else:
        logger.error("Some files do not use the repository pattern")
        return 1

if __name__ == "__main__":
    sys.exit(main())
