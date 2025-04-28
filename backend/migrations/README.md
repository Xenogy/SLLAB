# Database Migrations

This directory contains database migration scripts using Alembic.

## Migration Structure

- `alembic.ini`: Alembic configuration file
- `env.py`: Alembic environment configuration
- `script.py.mako`: Template for migration scripts
- `versions/`: Directory containing migration versions

## Available Migrations

### Initial Migration (001)

The initial migration creates the database schema with the following tables:

- `users`: User accounts
- `accounts`: Steam accounts
- `hardware`: Hardware profiles
- `proxmox_nodes`: Proxmox nodes
- `vms`: Virtual machines
- `whitelist`: VM access whitelist
- `cards`: Steam gift cards

It also sets up Row-Level Security (RLS) for all tables.

### Add Indexes Migration (002)

The add indexes migration adds indexes to improve query performance for all tables:

- `accounts`: Indexes for `owner_id`, `acc_username`, `acc_email_address`, `prime`, `lock`, `perm_lock`
- `hardware`: Indexes for `owner_id`, `account_id`, `type`
- `vms`: Indexes for `owner_id`, `proxmox_node_id`, `vmid`, `status`
- `proxmox_nodes`: Indexes for `owner_id`, `status`
- `whitelist`: Indexes for `vm_id`, `user_id`
- `users`: Indexes for `username`, `email`, `is_admin`
- `cards`: Indexes for `owner_id`, `account_id`

## Using Migrations

### Running Migrations

To upgrade the database to the latest version:

```bash
cd backend
python -m db.migration_manager upgrade
```

Or using the Alembic CLI:

```bash
cd backend
alembic -c migrations/alembic.ini upgrade head
```

### Creating a New Migration

To create a new migration:

```bash
cd backend
python -m db.migration_manager create "description_of_changes"
```

Or using the Alembic CLI:

```bash
cd backend
alembic -c migrations/alembic.ini revision -m "description_of_changes"
```

### Getting Migration Status

To check the current migration status:

```bash
cd backend
python -m db.migration_manager status
```

Or using the Alembic CLI:

```bash
cd backend
alembic -c migrations/alembic.ini current
```

### Upgrading to a Specific Revision

To upgrade the database to a specific revision:

```bash
cd backend
python -m db.migration_manager upgrade revision_id
```

### Downgrading to a Specific Revision

To downgrade the database to a specific revision:

```bash
cd backend
python -m db.migration_manager downgrade revision_id
```

### Automatic Migrations

The database can be automatically upgraded to the latest migration during application startup. To enable automatic migrations, set the `AUTO_IMPROVE_DATABASE` environment variable to `true`:

```bash
export AUTO_IMPROVE_DATABASE=true
```

## Migration Best Practices

1. **Always test migrations**: Before applying migrations to production, test them in a development or staging environment.

2. **Keep migrations small**: Small, focused migrations are easier to understand, test, and roll back if necessary.

3. **Include both upgrade and downgrade paths**: Always implement both the `upgrade()` and `downgrade()` functions to allow for rollbacks.

4. **Use transactions**: Migrations should be wrapped in transactions to ensure atomicity.

5. **Document complex migrations**: Add comments to explain complex migration logic.

6. **Avoid data loss**: Be careful with migrations that modify or delete data. Consider adding backup steps.

7. **Version control**: Always commit migration scripts to version control.
