"""
Script to check database status and report any issues.

This script checks:
1. Database connection
2. Migration status
3. RLS policies
4. Indexes
"""

import logging
import argparse
import json
from typing import Dict, Any, List, Optional
from db.connection import get_db_connection
from db.migration_manager import get_migration_status
from db.add_indexes import get_indexes_to_add
from db.standardize_rls_policies import get_tables_with_rls

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_connection() -> Dict[str, Any]:
    """
    Check database connection.
    
    Returns:
        Dict[str, Any]: A dictionary with connection status
    """
    try:
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                cursor.close()
                
                return {
                    "connected": True,
                    "version": version
                }
            else:
                return {
                    "connected": False,
                    "error": "Could not establish database connection"
                }
    except Exception as e:
        logger.error(f"Error checking database connection: {e}")
        return {
            "connected": False,
            "error": str(e)
        }

def check_migration_status() -> Dict[str, Any]:
    """
    Check migration status.
    
    Returns:
        Dict[str, Any]: A dictionary with migration status
    """
    try:
        status = get_migration_status()
        return status
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return {
            "error": str(e)
        }

def check_rls_policies() -> Dict[str, Any]:
    """
    Check RLS policies.
    
    Returns:
        Dict[str, Any]: A dictionary with RLS policy status
    """
    results = {}
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return {"error": "Could not establish database connection"}
            
            cursor = conn.cursor()
            
            # Get tables with RLS
            tables = get_tables_with_rls()
            
            for table in tables:
                # Check if the table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    );
                """, (table,))
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    results[table] = {
                        "exists": False,
                        "rls_enabled": False,
                        "policies": []
                    }
                    continue
                
                # Check if RLS is enabled
                cursor.execute("""
                    SELECT relrowsecurity
                    FROM pg_class
                    WHERE relname = %s AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
                """, (table,))
                rls_enabled = cursor.fetchone()[0]
                
                # Get policies
                cursor.execute("""
                    SELECT polname
                    FROM pg_policy
                    WHERE polrelid = %s::regclass;
                """, (table,))
                policies = [row[0] for row in cursor.fetchall()]
                
                # Check for required policies
                required_policies = [
                    f"{table}_admin_policy",
                    f"{table}_user_select_policy",
                    f"{table}_user_insert_policy",
                    f"{table}_user_update_policy",
                    f"{table}_user_delete_policy"
                ]
                
                missing_policies = [policy for policy in required_policies if policy not in policies]
                
                results[table] = {
                    "exists": True,
                    "rls_enabled": rls_enabled,
                    "policies": policies,
                    "missing_policies": missing_policies,
                    "has_all_policies": len(missing_policies) == 0
                }
            
            cursor.close()
            
            return results
    except Exception as e:
        logger.error(f"Error checking RLS policies: {e}")
        return {"error": str(e)}

def check_indexes() -> Dict[str, Any]:
    """
    Check indexes.
    
    Returns:
        Dict[str, Any]: A dictionary with index status
    """
    results = {}
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return {"error": "Could not establish database connection"}
            
            cursor = conn.cursor()
            
            # Get indexes to add
            indexes_to_add = get_indexes_to_add()
            
            for table, indexes in indexes_to_add.items():
                # Check if the table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    );
                """, (table,))
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    results[table] = {
                        "exists": False,
                        "indexes": []
                    }
                    continue
                
                # Get existing indexes
                cursor.execute("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = %s;
                """, (table,))
                existing_indexes = [row[0] for row in cursor.fetchall()]
                
                # Check which indexes are missing
                missing_indexes = []
                for index in indexes:
                    if index["name"] not in existing_indexes:
                        missing_indexes.append(index["name"])
                
                results[table] = {
                    "exists": True,
                    "indexes": existing_indexes,
                    "missing_indexes": missing_indexes,
                    "has_all_indexes": len(missing_indexes) == 0
                }
            
            cursor.close()
            
            return results
    except Exception as e:
        logger.error(f"Error checking indexes: {e}")
        return {"error": str(e)}

def check_database(output_format: str = "text") -> Dict[str, Any]:
    """
    Check database status and report any issues.
    
    Args:
        output_format (str, optional): Output format (text or json). Defaults to "text".
        
    Returns:
        Dict[str, Any]: A dictionary with check results
    """
    results = {}
    
    # Check database connection
    connection_status = check_database_connection()
    results["connection"] = connection_status
    
    if not connection_status.get("connected", False):
        # If we can't connect to the database, we can't do any other checks
        return results
    
    # Check migration status
    migration_status = check_migration_status()
    results["migrations"] = migration_status
    
    # Check RLS policies
    rls_status = check_rls_policies()
    results["rls"] = rls_status
    
    # Check indexes
    index_status = check_indexes()
    results["indexes"] = index_status
    
    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Check database status and report any issues.')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format (text or json)')
    parser.add_argument('--output', help='Output file (if not specified, output to console)')
    args = parser.parse_args()
    
    # Check database
    results = check_database(args.format)
    
    # Format output
    if args.format == 'json':
        output = json.dumps(results, indent=2)
    else:
        output = []
        
        # Connection status
        connection = results.get("connection", {})
        if connection.get("connected", False):
            output.append(f"Database connection: OK")
            output.append(f"  Version: {connection.get('version', 'Unknown')}")
        else:
            output.append(f"Database connection: FAILED")
            output.append(f"  Error: {connection.get('error', 'Unknown error')}")
        
        # Migration status
        migrations = results.get("migrations", {})
        if "error" in migrations:
            output.append(f"Migration status: ERROR")
            output.append(f"  Error: {migrations.get('error', 'Unknown error')}")
        else:
            current_revision = migrations.get("current_revision", "None")
            is_latest = migrations.get("is_up_to_date", False)
            output.append(f"Migration status: {'OK' if is_latest else 'NEEDS UPGRADE'}")
            output.append(f"  Current revision: {current_revision}")
            output.append(f"  Is latest: {'Yes' if is_latest else 'No'}")
        
        # RLS status
        rls = results.get("rls", {})
        if "error" in rls:
            output.append(f"RLS policies: ERROR")
            output.append(f"  Error: {rls.get('error', 'Unknown error')}")
        else:
            tables_with_issues = [table for table, status in rls.items() if not status.get("has_all_policies", False)]
            if tables_with_issues:
                output.append(f"RLS policies: ISSUES FOUND")
                output.append(f"  Tables with missing policies: {len(tables_with_issues)}")
                for table in tables_with_issues:
                    status = rls.get(table, {})
                    if not status.get("exists", False):
                        output.append(f"    {table}: Table does not exist")
                    elif not status.get("rls_enabled", False):
                        output.append(f"    {table}: RLS not enabled")
                    else:
                        missing = status.get("missing_policies", [])
                        output.append(f"    {table}: Missing policies: {', '.join(missing)}")
            else:
                output.append(f"RLS policies: OK")
                output.append(f"  All tables have required policies")
        
        # Index status
        indexes = results.get("indexes", {})
        if "error" in indexes:
            output.append(f"Indexes: ERROR")
            output.append(f"  Error: {indexes.get('error', 'Unknown error')}")
        else:
            tables_with_issues = [table for table, status in indexes.items() if not status.get("has_all_indexes", False)]
            if tables_with_issues:
                output.append(f"Indexes: ISSUES FOUND")
                output.append(f"  Tables with missing indexes: {len(tables_with_issues)}")
                for table in tables_with_issues:
                    status = indexes.get(table, {})
                    if not status.get("exists", False):
                        output.append(f"    {table}: Table does not exist")
                    else:
                        missing = status.get("missing_indexes", [])
                        output.append(f"    {table}: Missing indexes: {', '.join(missing)}")
            else:
                output.append(f"Indexes: OK")
                output.append(f"  All tables have required indexes")
        
        output = "\n".join(output)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        logger.info(f"Results written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
