# Database Access Layer

This directory contains the database access layer for the AccountDB application.

## Directory Structure

- `__init__.py`: Package initialization file
- `access.py`: Base class for database access with RLS support
- `connection.py`: Database connection management
- `user_connection.py`: User-specific database connection management
- `rls_context.py`: Row-Level Security (RLS) context management
- `migration_manager.py`: Database migration management
- `add_indexes.py`: Script to add indexes to improve database performance
- `standardize_rls_policies.py`: Script to standardize RLS policies across all tables
- `check_database.py`: Script to check database status and report any issues
- `improve_database.py`: Script to run all database improvements in one go
- `startup_improvements.py`: Script to run database improvements during application startup
- `repositories/`: Directory containing repository classes for database access

## Database Access Pattern

The database access layer follows the repository pattern, which provides a clean separation between the database and the business logic. The repository pattern ensures that Row-Level Security (RLS) is applied to all database operations.

### DatabaseAccess Class

The `DatabaseAccess` class provides a base class for database access with RLS support. It includes methods for executing queries and commands with RLS context.

```python
from db.access import DatabaseAccess

# Create a DatabaseAccess instance without RLS context
db_access = DatabaseAccess()

# Create a DatabaseAccess instance with RLS context
db_access = DatabaseAccess(user_id=1, user_role="admin")

# Execute a query
results = db_access.execute_query("SELECT * FROM accounts WHERE acc_id = %s", ("acc123",))

# Execute a command
affected_rows = db_access.execute_command("UPDATE accounts SET acc_username = %s WHERE acc_id = %s", ("new_username", "acc123"))
```

### Repository Classes

Repository classes extend the `DatabaseAccess` class and provide entity-specific methods for database access. Each repository class is responsible for a specific entity in the database.

```python
from db.repositories.accounts import AccountRepository

# Create a repository instance with RLS context
account_repo = AccountRepository(user_id=1, user_role="admin")

# Get an account by ID
account = account_repo.get_account_by_id("acc123")
```

See the [repositories README](./repositories/README.md) for more information on using repository classes.

## Row-Level Security (RLS)

Row-Level Security (RLS) is a security feature that restricts which rows a user can see or modify in a database table. The database access layer ensures that RLS is applied to all database operations.

### RLS Context

The RLS context is set using the `set_rls_context` function in the `rls_context.py` file. This function sets the `app.current_user_id` and `app.current_user_role` session variables in the database.

```python
from db.rls_context import set_rls_context

# Set RLS context
cursor = conn.cursor()
set_rls_context(cursor, user_id=1, user_role="admin")
```

### User-Specific Database Connection

The `get_user_db_connection` function in the `user_connection.py` file provides a context manager for database connections with user context. This function sets the RLS context when the connection is acquired and clears it when the connection is released.

```python
from db.user_connection import get_user_db_connection

# Get a database connection with user context
with get_user_db_connection(user_id=1, user_role="admin") as conn:
    # Use the connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts")
    results = cursor.fetchall()
```

## Database Migrations

The database migration system uses Alembic to manage database schema changes. See the [migrations README](../migrations/README.md) for more information on using migrations.

```bash
# Check migration status
python -m db.migration_manager status

# Create a new migration
python -m db.migration_manager create "migration_name"

# Upgrade to the latest migration
python -m db.migration_manager upgrade

# Upgrade to a specific revision
python -m db.migration_manager upgrade revision_id

# Downgrade to a specific revision
python -m db.migration_manager downgrade revision_id
```

## Database Performance

The `add_indexes.py` script adds indexes to improve database performance. This script adds indexes to tables to improve query performance.

```bash
cd backend
python -m db.add_indexes
```

## Standardizing RLS Policies

The `standardize_rls_policies.py` script standardizes RLS policies across all tables. This script creates or updates RLS policies for all tables that should have RLS.

```bash
cd backend
python -m db.standardize_rls_policies

# Drop existing policies and create new ones
python -m db.standardize_rls_policies --drop-existing
```

## Checking Database Status

The `check_database.py` script checks the database status and reports any issues. It checks database connection, migration status, RLS policies, and indexes.

```bash
# Check database status
python -m db.check_database

# Output in JSON format
python -m db.check_database --format json

# Save output to a file
python -m db.check_database --output report.txt
```

## Improving Database

The `improve_database.py` script runs all the database improvements in one go. It upgrades the database to the latest migration, adds indexes, and standardizes RLS policies.

```bash
# Run all improvements
python -m db.improve_database

# Skip migrations
python -m db.improve_database --skip-migrations

# Skip adding indexes
python -m db.improve_database --skip-indexes

# Skip standardizing RLS policies
python -m db.improve_database --skip-rls
```

## Automatic Improvements

The `startup_improvements.py` script is designed to be run during application startup. It checks if the database needs improvements and applies them if necessary.

To enable automatic improvements, set the `AUTO_IMPROVE_DATABASE` environment variable to `true`:

```bash
export AUTO_IMPROVE_DATABASE=true
```
