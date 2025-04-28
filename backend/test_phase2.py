"""
Test script to verify that our Phase 2 code changes are syntactically correct.
This script doesn't require database access.
"""

import importlib
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import_module(module_name):
    """Test importing a module."""
    try:
        module = importlib.import_module(module_name)
        logger.info(f"Successfully imported {module_name}")
        return True
    except Exception as e:
        logger.error(f"Error importing {module_name}: {e}")
        return False

def main():
    """Main function."""
    modules_to_test = [
        # Repository modules
        "db.repositories.base",
        "db.repositories.accounts",
        "db.repositories.proxmox_nodes",
        "db.repositories.vms",
        "db.repositories.hardware",
        "db.repositories.users",
        
        # Router modules
        "routers.proxmox_nodes",
        "routers.vms",
        "routers.accounts",
        "routers.hardware",
        "routers.cards",
        "routers.auth"
    ]
    
    success = True
    for module_name in modules_to_test:
        if not test_import_module(module_name):
            success = False
    
    if success:
        logger.info("All modules imported successfully")
        return 0
    else:
        logger.error("Some modules failed to import")
        return 1

if __name__ == "__main__":
    sys.exit(main())
