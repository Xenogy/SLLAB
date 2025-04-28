# Phase 1: Database and RLS Improvements

## Overview

This phase focuses on improving the database structure and Row-Level Security (RLS) implementation to ensure data security and integrity. The goal is to create a standardized pattern for database access with RLS and refactor all endpoints to use this pattern.

## Objectives

1. Standardize database access patterns
2. Improve RLS implementation
3. Refactor direct SQL queries
4. Implement a database migration system
5. Optimize database queries

## Detailed Tasks

### 1. Standardize Database Access Patterns

#### 1.1 Create a Database Access Layer

Create a database access layer that enforces RLS and provides a consistent interface for database operations.

```python
# db/access.py
from typing import Optional, Dict, Any, List, Tuple
from db.connection import get_db_connection, get_user_db_connection

class DatabaseAccess:
    """Base class for database access with RLS support."""
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        self.user_id = user_id
        self.user_role = user_role
    
    def get_connection(self):
        """Get a database connection with or without RLS context."""
        if self.user_id and self.user_role:
            return get_user_db_connection(user_id=self.user_id, user_role=self.user_role)
        else:
            return get_db_connection()
    
    def execute_query(self, query: str, params: Tuple = None, with_rls: bool = True) -> List[Dict[str, Any]]:
        """Execute a query and return the results as a list of dictionaries."""
        conn = self.get_connection() if with_rls else get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
        finally:
            conn.close()
    
    def execute_command(self, query: str, params: Tuple = None, with_rls: bool = True) -> int:
        """Execute a command and return the number of affected rows."""
        conn = self.get_connection() if with_rls else get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                return cursor.rowcount
        finally:
            conn.close()
```

#### 1.2 Create Repository Classes for Each Entity

Create repository classes for each entity that use the database access layer.

```python
# db/repositories/proxmox_nodes.py
from typing import List, Dict, Any, Optional
from db.access import DatabaseAccess

class ProxmoxNodeRepository(DatabaseAccess):
    """Repository for Proxmox nodes."""
    
    def get_nodes(self, limit: int = 10, offset: int = 0, search: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get a list of Proxmox nodes with pagination and filtering."""
        query = """
            SELECT
                id, name, hostname, port, status, api_key, last_seen,
                created_at, updated_at, owner_id
            FROM proxmox_nodes
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (name ILIKE %s OR hostname ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        # Count total records
        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS filtered_nodes"
        count_result = self.execute_query(count_query, tuple(params))
        total = count_result[0]['total'] if count_result else 0
        
        # Add pagination
        query += " ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute the query
        nodes = self.execute_query(query, tuple(params))
        
        return {
            "nodes": nodes,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_node_by_id(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific Proxmox node by ID."""
        query = """
            SELECT
                id, name, hostname, port, status, api_key, last_seen,
                created_at, updated_at, owner_id
            FROM proxmox_nodes
            WHERE id = %s
        """
        results = self.execute_query(query, (node_id,))
        return results[0] if results else None
```

#### 1.3 Create Guidelines for Database Access

Create clear guidelines for when to use each database access pattern.

```markdown
# Database Access Guidelines

## General Guidelines

- Use the `DatabaseAccess` class for all database operations
- Create repository classes for each entity
- Use the repository classes in the API endpoints
- Always use parameterized queries to prevent SQL injection

## RLS Guidelines

- Always use RLS for user-facing endpoints
- Use `with_rls=True` for operations that should respect RLS
- Use `with_rls=False` only for system operations that need to bypass RLS
- Document any bypass of RLS with a clear explanation

## Repository Guidelines

- Create a repository class for each entity
- Implement CRUD operations for each entity
- Use consistent naming conventions
- Document all methods with clear docstrings
```

### 2. Improve RLS Implementation

#### 2.1 Review and Update RLS Policies

Review all RLS policies to ensure they cover all operations and are properly implemented.

```sql
-- Example of improved RLS policy for accounts table
CREATE POLICY accounts_admin_policy ON public.accounts
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY accounts_user_select_policy ON public.accounts
    FOR SELECT
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

CREATE POLICY accounts_user_insert_policy ON public.accounts
    FOR INSERT
    TO PUBLIC
    WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

CREATE POLICY accounts_user_update_policy ON public.accounts
    FOR UPDATE
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER)
    WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

CREATE POLICY accounts_user_delete_policy ON public.accounts
    FOR DELETE
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
```

#### 2.2 Create RLS Tests

Create comprehensive tests for RLS to ensure it works as expected.

```python
# tests/test_rls.py
import pytest
import psycopg2
from db.connection import get_db_connection, get_user_db_connection

def test_rls_select():
    """Test that RLS works for SELECT operations."""
    # Create test data
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (acc_id, owner_id) VALUES ('test1', 1), ('test2', 2)")
        conn.commit()
    
    # Test user 1 can only see their own accounts
    with get_user_db_connection(user_id=1, user_role='user') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT acc_id FROM accounts")
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'test1'
    
    # Test user 2 can only see their own accounts
    with get_user_db_connection(user_id=2, user_role='user') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT acc_id FROM accounts")
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'test2'
    
    # Test admin can see all accounts
    with get_user_db_connection(user_id=1, user_role='admin') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT acc_id FROM accounts")
        results = cursor.fetchall()
        assert len(results) == 2
```

#### 2.3 Document RLS Implementation

Create comprehensive documentation for the RLS implementation.

```markdown
# Row-Level Security (RLS) Implementation

## Overview

Row-Level Security (RLS) is a security feature that restricts which rows a user can access in a database table. In AccountDB, RLS is used to ensure that users can only access their own data.

## How RLS Works in AccountDB

1. Each table has an `owner_id` column that references the `users` table
2. RLS policies are created for each table to restrict access based on the `owner_id`
3. The `app.current_user_id` and `app.current_user_role` session variables are set when a user logs in
4. These session variables are used in the RLS policies to determine which rows a user can access

## RLS Policies

### Admin Policy

Admins can access all rows in all tables:

```sql
CREATE POLICY {table}_admin_policy ON public.{table}
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');
```

### User Policies

Regular users can only access rows they own:

```sql
CREATE POLICY {table}_user_select_policy ON public.{table}
    FOR SELECT
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

CREATE POLICY {table}_user_insert_policy ON public.{table}
    FOR INSERT
    TO PUBLIC
    WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

CREATE POLICY {table}_user_update_policy ON public.{table}
    FOR UPDATE
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER)
    WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

CREATE POLICY {table}_user_delete_policy ON public.{table}
    FOR DELETE
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
```

## Setting RLS Context

The RLS context is set using the `set_rls_context` function:

```sql
CREATE OR REPLACE FUNCTION set_rls_context(user_id INTEGER, user_role TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
    PERFORM set_config('app.current_user_role', user_role, FALSE);
END;
$$ LANGUAGE plpgsql;
```

This function is called when a user logs in or when a request is made with a valid JWT token.
```

### 3. Refactor Direct SQL Queries

#### 3.1 Identify Direct SQL Queries

Identify all endpoints that use direct SQL queries and prioritize them for refactoring.

```markdown
# Direct SQL Queries to Refactor

## High Priority

- `/proxmox-nodes/agent-vms/{node_id}` - Uses direct database connection
- `/proxmox-nodes/agent-whitelist/{node_id}` - Uses direct database connection
- `/vms/{vm_id}` - Contains direct SQL query

## Medium Priority

- `/proxmox-nodes/{node_id}` - Contains direct SQL query
- `/vms/` - Contains direct SQL query

## Low Priority

- `/accounts/{account_id}` - Contains direct SQL query
- `/hardware/{hardware_id}` - Contains direct SQL query
```

#### 3.2 Create Repository Methods

Create repository methods for each direct SQL query.

```python
# db/repositories/proxmox_nodes.py
def get_agent_vms(self, node_id: int, api_key: str) -> List[Dict[str, Any]]:
    """Get all VMs for a specific Proxmox node for the agent."""
    # First, verify the node and API key
    node_query = """
        SELECT id, api_key
        FROM proxmox_nodes
        WHERE id = %s
    """
    node_result = self.execute_query(node_query, (node_id,), with_rls=False)
    
    if not node_result:
        return None
    
    stored_api_key = node_result[0]['api_key']
    
    # Verify API key
    if api_key != stored_api_key:
        return None
    
    # Get all VMs for this node
    vms_query = """
        SELECT 
            id, vmid, name, status, cpu_cores, memory_mb, 
            disk_gb, ip_address, proxmox_node_id, owner_id,
            created_at, updated_at
        FROM vms
        WHERE proxmox_node_id = %s
    """
    vms = self.execute_query(vms_query, (node_id,), with_rls=False)
    
    return {
        "vms": vms,
        "count": len(vms),
        "node_id": node_id
    }
```

#### 3.3 Refactor Endpoints

Refactor endpoints to use the repository methods.

```python
# backend/routers/proxmox_nodes.py
@router.get("/agent-vms/{node_id}")
async def get_agent_vms(
    node_id: int,
    api_key: Optional[str] = Query(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Get all VMs for a specific Proxmox node for the agent.
    This endpoint is called by the Proxmox host agent to get VM information.
    """
    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    # Use API key from header or query parameter
    actual_api_key = x_api_key or api_key

    # Debug logging
    logger.info(f"Agent VMs request - node_id: {node_id}, api_key: {api_key}, x_api_key: {x_api_key}")
    logger.info(f"Using API key: {actual_api_key}")

    if not actual_api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use repository to get VMs
    repository = ProxmoxNodeRepository()
    result = repository.get_agent_vms(node_id, actual_api_key)
    
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid API key or node not found")
    
    return result
```

### 4. Implement a Database Migration System

#### 4.1 Set Up Alembic

Set up Alembic for database migrations.

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init migrations
```

#### 4.2 Create Initial Migration

Create an initial migration that represents the current database schema.

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"
```

#### 4.3 Document Migration Process

Create documentation for the migration process.

```markdown
# Database Migration Process

## Overview

AccountDB uses Alembic for database migrations. This document explains how to create and apply migrations.

## Creating a Migration

To create a new migration:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of the migration"
```

This will create a new migration file in the `migrations/versions` directory.

## Applying Migrations

To apply all pending migrations:

```bash
# Apply all pending migrations
alembic upgrade head
```

To apply a specific migration:

```bash
# Apply a specific migration
alembic upgrade <revision>
```

## Rolling Back Migrations

To roll back the most recent migration:

```bash
# Roll back the most recent migration
alembic downgrade -1
```

To roll back to a specific migration:

```bash
# Roll back to a specific migration
alembic downgrade <revision>
```

## Migration Guidelines

- Always test migrations in a development environment before applying them in production
- Make sure migrations are reversible
- Document any manual steps required for a migration
- Include data migrations when necessary
```

### 5. Optimize Database Queries

#### 5.1 Identify Inefficient Queries

Identify inefficient queries and prioritize them for optimization.

```markdown
# Inefficient Queries to Optimize

## High Priority

- Query in `/vms/` endpoint retrieves all columns even when not needed
- Query in `/proxmox-nodes/` endpoint doesn't use appropriate indexes

## Medium Priority

- Query in `/accounts/` endpoint could be optimized with JOINs
- Query in `/hardware/` endpoint retrieves more data than needed

## Low Priority

- Query in `/cards/` endpoint could be optimized
- Query in `/users/` endpoint could be optimized
```

#### 5.2 Optimize Queries

Optimize the identified queries.

```python
# Before optimization
query = """
    SELECT *
    FROM vms
    WHERE proxmox_node_id = %s
"""

# After optimization
query = """
    SELECT
        id, vmid, name, status, cpu_cores, memory_mb, 
        disk_gb, ip_address, proxmox_node_id, owner_id
    FROM vms
    WHERE proxmox_node_id = %s
"""
```

#### 5.3 Add Indexes

Add appropriate indexes to improve query performance.

```sql
-- Add indexes for better performance
CREATE INDEX idx_vms_proxmox_node_id ON public.vms (proxmox_node_id);
CREATE INDEX idx_vms_owner_id ON public.vms (owner_id);
CREATE INDEX idx_vms_status ON public.vms (status);
```

## Expected Outcomes

By implementing these improvements, we expect to achieve the following outcomes:

1. **Improved Security**: All data will be properly secured with Row-Level Security, with no security vulnerabilities.
2. **Standardized Database Access**: All endpoints will use a consistent pattern for database access.
3. **Improved Maintainability**: The codebase will be more maintainable with repository classes and consistent patterns.
4. **Better Performance**: Database queries will be optimized for better performance.
5. **Easier Schema Changes**: Database migrations will make it easier to track and apply schema changes.

## Timeline

This phase is expected to take 2 weeks to complete:

- Week 1: Standardize database access and improve RLS implementation
- Week 2: Refactor direct SQL queries, implement database migrations, and optimize queries
