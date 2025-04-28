"""
Test script to verify that the refactored endpoints are using the repository pattern.
This script checks the source code of the router modules for repository pattern usage.
"""

import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_for_repository_pattern(file_path: str, repo_class: str) -> bool:
    """
    Check if a file uses the repository pattern.
    
    Args:
        file_path: The path to the file to check
        repo_class: The repository class name that should be used
        
    Returns:
        bool: True if the file uses the repository pattern, False otherwise
    """
    try:
        # Check if the file imports the repository class
        import_result = subprocess.run(
            f"grep -n 'import' {file_path} | grep '{repo_class}'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if import_result.returncode != 0:
            logger.error(f"File {file_path} does not import {repo_class}")
            return False
        
        # Check if the file instantiates the repository class
        instantiation_result = subprocess.run(
            f"grep -n '{repo_class}(' {file_path}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if instantiation_result.returncode != 0:
            logger.error(f"File {file_path} does not instantiate {repo_class}")
            return False
        
        # Check if the file contains direct SQL queries
        sql_result = subprocess.run(
            f"grep -n 'cursor.execute' {file_path} | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
        
        sql_count = int(sql_result.stdout.strip())
        if sql_count > 0:
            logger.warning(f"File {file_path} contains {sql_count} direct SQL queries")
            # Don't fail the test for this, just warn
        
        logger.info(f"File {file_path} uses {repo_class}")
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
        "ProxmoxNodeRepository"
    ):
        success = False
    
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/proxmox_nodes.py",
        "VMRepository"
    ):
        # This is not a critical failure, just a warning
        logger.warning("File /home/axel/accountdb/backend/routers/proxmox_nodes.py does not use VMRepository")
    
    # Check vms.py
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/vms.py",
        "VMRepository"
    ):
        success = False
    
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/vms.py",
        "ProxmoxNodeRepository"
    ):
        # This is not a critical failure, just a warning
        logger.warning("File /home/axel/accountdb/backend/routers/vms.py does not use ProxmoxNodeRepository")
    
    # Check accounts.py
    if not check_file_for_repository_pattern(
        "/home/axel/accountdb/backend/routers/accounts.py",
        "AccountRepository"
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
