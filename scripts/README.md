# AccountDB Utility Scripts

This directory contains utility scripts for the AccountDB application.

## Database Scripts

- `verify_rls.sql` - Verifies that Row-Level Security is working correctly
- `check_db_connection.sql` - Checks database connection settings and RLS functionality
- `fix_permissions.sql` - Fixes permissions for the acc_user role

## Python Utility Scripts

- `get_db_schema.py` - Retrieves and displays the database schema information

## Usage

### SQL Scripts

To run SQL scripts:

```bash
docker compose exec postgres psql -U acc_user -d accountdb -f /app/scripts/script_name.sql
```

Or from the host machine:

```bash
psql -U acc_user -h localhost -d accountdb -f scripts/script_name.sql
```

### Python Scripts

To run Python scripts:

```bash
python scripts/get_db_schema.py
```
