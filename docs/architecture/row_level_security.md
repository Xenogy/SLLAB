# Row-Level Security (RLS) Implementation

This document describes the Row-Level Security (RLS) implementation in the AccountDB system.

## Overview

Row-Level Security (RLS) is a security feature that restricts which rows a user can access in a database table. In our system, RLS ensures that:

- Admin users can see all records in the database
- Regular users can only see records they own

## Implementation Details

### Database Configuration

RLS is implemented at the database level using PostgreSQL's built-in RLS features:

1. **RLS Policies**: Each table has two policies:
   - `<table>_admin_policy`: Allows admin users to see all records
   - `<table>_user_policy`: Allows regular users to see only their own records

2. **Session Variables**: Two session variables are used to control access:
   - `app.current_user_id`: The ID of the current user
   - `app.current_user_role`: The role of the current user (admin or user)

3. **RLS Views**: For each table, we create a view that enforces RLS:
   - `<table>_with_rls`: A view that filters records based on the user's role and ID

### Centralized RLS Implementation

The RLS implementation has been centralized to ensure consistency:

1. **RLS Policies**: All RLS policies are defined in a single SQL script (`backend/db/sql/rls_policies.sql`)
2. **RLS Views**: All RLS views are defined in a single SQL script (`backend/db/sql/rls_views.sql`)
3. **RLS Context**: All RLS context setting is handled by a centralized module (`backend/db/rls_context.py`)

This centralization ensures that:
- All tables have consistent RLS policies
- All views have consistent naming and implementation
- All context setting uses the same approach

### Tables with RLS

The following tables have RLS enabled:

| Table | RLS View | Owner Column |
|-------|----------|--------------|
| accounts | accounts_with_rls | owner_id |
| cards | cards_with_rls | owner_id |
| hardware | hardware_with_rls | owner_id |
| hardware_profiles | hardware_profiles_with_rls | owner_id (if table exists) |

### API Implementation

The API uses the RLS views instead of the base tables to ensure that users can only access records they are authorized to see. For example:

```python
# Instead of this:
cursor.execute("SELECT * FROM accounts WHERE acc_id = %s", (acc_id,))

# We use this:
cursor.execute("SELECT * FROM accounts_with_rls WHERE acc_id = %s", (acc_id,))
```

### User Context

When a user makes a request, the system:

1. Authenticates the user and retrieves their ID and role
2. Sets the session variables in the database connection using the centralized RLS context module:
   ```python
   from db.rls_context import set_rls_context

   # Set RLS context
   success = set_rls_context(cursor, user_id, user_role)
   if not success:
       logger.warning(f"Failed to set RLS context for user_id={user_id}, role={user_role}")
   ```
3. Uses the RLS views for all database operations

### Context Manager

A context manager is provided for setting RLS context:

```python
from db.rls_context import rls_context

# Use RLS context
with rls_context(conn, user_id, user_role) as context:
    if context:
        # RLS context set successfully
        cursor = conn.cursor()
        try:
            # Execute queries using RLS views
            cursor.execute("SELECT * FROM accounts_with_rls")
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
    else:
        # Failed to set RLS context
        logger.warning("Failed to set RLS context")
```

## Testing

RLS can be tested using the `verify_rls_setup` function in the `db.rls_context` module:

```python
from db.rls_context import verify_rls_setup

# Verify RLS setup
results = verify_rls_setup(conn)
if results["success"]:
    logger.info("RLS setup verified successfully")
else:
    logger.warning("RLS setup verification failed")
    logger.warning(f"Results: {results}")
```

This function checks:
1. If tables exist and have RLS enabled
2. If owner_id columns exist
3. If RLS policies exist
4. If RLS views exist
5. If app schema exists
6. If set_rls_context function exists

## Troubleshooting

If RLS is not working correctly:

1. Check that the session variables are being set correctly:
   ```sql
   SELECT current_setting('app.current_user_id', TRUE), current_setting('app.current_user_role', TRUE);
   ```

2. Verify that the RLS policies are defined correctly:
   ```sql
   SELECT * FROM pg_policy WHERE polrelid = 'accounts'::regclass;
   ```

3. Ensure that all API endpoints are using the RLS views:
   ```python
   # Use RLS views
   cursor.execute("SELECT * FROM accounts_with_rls")
   ```

4. Run the `verify_rls_setup` function to diagnose issues:
   ```python
   from db.rls_context import verify_rls_setup

   # Verify RLS setup
   results = verify_rls_setup(conn)
   print(results)
   ```

## Maintenance

When adding new tables to the system:

1. Add the table name to the `tables` array in `backend/db/sql/rls_policies.sql`:
   ```sql
   tables TEXT[] := ARRAY['accounts', 'hardware', 'cards', 'new_table'];
   ```

2. Add the table name to the `tables` array in `backend/db/sql/rls_views.sql`:
   ```sql
   tables TEXT[] := ARRAY['accounts', 'hardware', 'cards', 'new_table'];
   ```

3. Add the table to the `get_user_tables_with_rls` function in `backend/db/rls_context.py`:
   ```python
   def get_user_tables_with_rls() -> list:
       return [
           {"table": "accounts", "view": "accounts_with_rls"},
           {"table": "hardware", "view": "hardware_with_rls"},
           {"table": "cards", "view": "cards_with_rls"},
           {"table": "new_table", "view": "new_table_with_rls"}
       ]
   ```

4. Run the `init_rls.py` script to apply the changes:
   ```bash
   python backend/init_rls.py
   ```
