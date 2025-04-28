# Database Migrations

This directory contains SQL migration files for the AccountDB database.

## Migration Files

- `001_normalize_schema.sql` - Normalizes the database schema
- `002_normalize_hardware.sql` - Normalizes the hardware table
- `003_normalize_cards.sql` - Normalizes the cards table
- `004_performance_indexes.sql` - Adds performance indexes to the database

## Note on Row-Level Security (RLS)

Row-Level Security (RLS) is now implemented during database initialization rather than through the migration system. The RLS setup is handled by:

1. Initialization scripts in the `inits/` directory:
   - `08-user_ownership.sql` - Adds owner_id columns and basic RLS policies
   - `09-setup_rls.sql` - Sets up comprehensive RLS policies and views

2. Application startup in `init_rls.py` which applies RLS policies and views

This approach ensures that RLS is properly set up when the database is first created, rather than being applied as a migration after the fact.

## Running Migrations

Migrations are automatically run when the application starts. You can also run them manually using the migration module:

```python
from db import run_migrations

run_migrations()
```

Or using the migration script:

```bash
python -m backend.db.migrations
```
