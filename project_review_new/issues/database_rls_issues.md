# Database and RLS Issues

## High Priority Issues

### 1. Inconsistent RLS Implementation

**Description:**  
Row-Level Security (RLS) is implemented inconsistently across endpoints. Some endpoints properly use RLS context while others don't.

**Impact:**  
Users might be able to access data they shouldn't have access to, creating a security vulnerability.

**Examples:**
- In `backend/routers/proxmox_nodes.py`, the `get_agent_vms` endpoint uses a direct database connection without RLS context.
- Some endpoints manually check ownership instead of relying on RLS.

**Code Example:**
```python
# Direct database connection bypassing RLS
conn = psycopg2.connect(
    host=os.environ.get("PG_HOST", "postgres"),
    port=os.environ.get("PG_PORT", "5432"),
    dbname=os.environ.get("DB_NAME", "accountdb"),
    user=os.environ.get("SU_USER", "postgres"),
    password=os.environ.get("SU_PASSWORD", "CHANGEME_ULTRASECURE")
)
```

**Recommended Fix:**
- Create a standardized pattern for database access with RLS
- Implement a database access layer that enforces RLS
- Refactor all endpoints to use this layer

### 2. Direct Database Access Bypassing RLS

**Description:**  
Some endpoints use direct database connections that bypass Row-Level Security (RLS).

**Impact:**  
This creates a security vulnerability where users might be able to access data they shouldn't have access to.

**Examples:**
- The `/proxmox-nodes/agent-vms/{node_id}` endpoint uses a direct database connection.
- The `/proxmox-nodes/agent-whitelist/{node_id}` endpoint uses a direct database connection.

**Code Example:**
```python
# Direct database connection bypassing RLS
conn = psycopg2.connect(
    host=os.environ.get("PG_HOST", "postgres"),
    port=os.environ.get("PG_PORT", "5432"),
    dbname=os.environ.get("DB_NAME", "accountdb"),
    user=os.environ.get("SU_USER", "postgres"),
    password=os.environ.get("SU_PASSWORD", "CHANGEME_ULTRASECURE")
)
```

**Recommended Fix:**
- Create a secure pattern for agent endpoints that doesn't bypass RLS
- Implement proper authentication and authorization for agent endpoints
- Use a dedicated database role with limited permissions for agent access

### 3. Inconsistent Database Connection Patterns

**Description:**  
Different patterns are used for database connections throughout the codebase.

**Impact:**  
This makes the code harder to maintain and increases the risk of security issues.

**Examples:**
- Some endpoints use `get_db_connection()` while others use `get_user_db_connection()`
- Some endpoints create direct database connections
- Some endpoints use context managers while others don't

**Code Example:**
```python
# Using get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    # ...

# Using get_user_db_connection
with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
    cursor = conn.cursor()
    # ...

# Direct connection
conn = psycopg2.connect(...)
cursor = conn.cursor()
# ...
```

**Recommended Fix:**
- Standardize database connection patterns
- Create clear guidelines for when to use each pattern
- Refactor all endpoints to follow these guidelines

## Medium Priority Issues

### 1. Missing RLS Policies for Some Operations

**Description:**  
Some database operations don't have proper RLS policies.

**Impact:**  
This can lead to security issues in specific scenarios where users might be able to access or modify data they shouldn't have access to.

**Examples:**
- Some INSERT operations don't check ownership
- Some UPDATE operations don't verify ownership before updating

**Code Example:**
```sql
-- Missing RLS policy for INSERT
CREATE POLICY accounts_user_policy ON public.accounts
    FOR ALL
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
-- This policy doesn't restrict INSERT operations based on ownership
```

**Recommended Fix:**
- Review all RLS policies to ensure they cover all operations
- Add specific policies for INSERT, UPDATE, DELETE operations where needed
- Test all policies to ensure they work as expected

### 2. No Database Migration System

**Description:**  
The project doesn't use a database migration system for managing schema changes.

**Impact:**  
This makes it difficult to track and apply schema changes, especially in a team environment or when deploying to different environments.

**Examples:**
- Schema changes are applied directly in SQL files
- No versioning for database schema
- No way to roll back schema changes

**Recommended Fix:**
- Implement a database migration system (e.g., Alembic)
- Convert existing schema into migrations
- Document the migration process

## Low Priority Issues

### 1. Inefficient Database Queries

**Description:**  
Some database queries are not optimized for performance.

**Impact:**  
This can lead to performance issues, especially with large datasets.

**Examples:**
- Some queries retrieve more columns than needed
- Some queries don't use appropriate indexes
- Some queries could be optimized with JOINs

**Code Example:**
```python
# Inefficient query retrieving all columns
query = "SELECT * FROM proxmox_nodes WHERE id = %s"
cursor.execute(query, (node_id,))

# More efficient query retrieving only needed columns
query = "SELECT id, name, hostname FROM proxmox_nodes WHERE id = %s"
cursor.execute(query, (node_id,))
```

**Recommended Fix:**
- Review and optimize database queries
- Add appropriate indexes
- Use query profiling to identify slow queries
