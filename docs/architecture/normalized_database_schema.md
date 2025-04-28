# Normalized Database Schema

## Overview

The database schema has been normalized to improve data integrity, reduce redundancy, and make the database more maintainable. This document describes the normalized database schema.

## Tables

### users

Stores user information for authentication and authorization.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    avatar_url TEXT
);
```

### email_accounts

Stores email account information.

```sql
CREATE TABLE email_accounts (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id)
);
```

### vault_accounts

Stores vault account information.

```sql
CREATE TABLE vault_accounts (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id)
);
```

### steamguard_data

Stores Steam Guard data.

```sql
CREATE TABLE steamguard_data (
    id SERIAL PRIMARY KEY,
    account_name TEXT,
    device_id TEXT,
    identity_secret TEXT,
    shared_secret TEXT,
    revocation_code TEXT,
    uri TEXT,
    token_gid TEXT,
    secret_1 TEXT,
    serial_number TEXT,
    server_time BIGINT,
    status INTEGER,
    confirm_type INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id)
);
```

### accounts_normalized

Stores account information with references to related tables.

```sql
CREATE TABLE accounts_normalized (
    id SERIAL PRIMARY KEY,
    account_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email_id INTEGER REFERENCES email_accounts(id),
    vault_id INTEGER REFERENCES vault_accounts(id),
    steamguard_id INTEGER REFERENCES steamguard_data(id),
    created_at BIGINT NOT NULL,
    session_start BIGINT NOT NULL,
    prime BOOLEAN NOT NULL DEFAULT FALSE,
    lock BOOLEAN NOT NULL DEFAULT FALSE,
    perm_lock BOOLEAN NOT NULL DEFAULT FALSE,
    farmlabs_upload UUID,
    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id)
);
```

### hardware_normalized

Stores hardware information with references to related tables.

```sql
CREATE TABLE hardware_normalized (
    id SERIAL PRIMARY KEY,
    account_id TEXT REFERENCES accounts_normalized(account_id),
    bios_vendor TEXT,
    bios_version VARCHAR(50),
    disk_serial VARCHAR(100),
    disk_model VARCHAR(100),
    smbios_uuid UUID,
    motherboard_manufacturer TEXT,
    motherboard_product TEXT,
    motherboard_version VARCHAR(50),
    motherboard_serial VARCHAR(100),
    mac_address VARCHAR(17),
    vm_id INTEGER,
    pc_name VARCHAR(100),
    machine_guid UUID,
    hardware_profile_guid UUID,
    product_id VARCHAR(32),
    device_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id)
);
```

### cards_normalized

Stores card information with references to related tables.

```sql
CREATE TABLE cards_normalized (
    id SERIAL PRIMARY KEY,
    code1 TEXT NOT NULL,
    code2 TEXT,
    redeemed BOOLEAN NOT NULL DEFAULT FALSE,
    failed TEXT DEFAULT '',
    lock BOOLEAN NOT NULL DEFAULT FALSE,
    perm_lock BOOLEAN NOT NULL DEFAULT FALSE,
    account_id TEXT REFERENCES accounts_normalized(account_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id)
);
```

## Relationships

### users to other tables

- A user can have multiple email accounts, vault accounts, steamguard data, accounts, hardware, and cards.
- Each email account, vault account, steamguard data, account, hardware, and card belongs to exactly one user.

### accounts_normalized to other tables

- An account can have one email account, one vault account, and one steamguard data.
- An account can have multiple hardware and cards.
- Each hardware and card belongs to at most one account.

## Row-Level Security (RLS)

All tables have Row-Level Security (RLS) enabled to ensure that users can only access their own data. The RLS policies are defined as follows:

- Users can only access rows where the `owner_id` column matches their user ID.
- Administrators can access all rows.

## Views

For each table, there is a corresponding view with the suffix `_with_rls` that applies the RLS policies. These views should be used instead of the tables directly to ensure that RLS is applied correctly.

## Indexes

Each table has appropriate indexes to improve query performance:

- Primary key columns
- Foreign key columns
- Columns used in WHERE clauses
- Columns used in JOIN conditions
- Columns used in ORDER BY clauses

## Constraints

Each table has appropriate constraints to ensure data integrity:

- Primary key constraints
- Foreign key constraints
- Unique constraints
- Check constraints
- Not null constraints

## Timestamps

Each table has `created_at` and `updated_at` columns to track when rows were created and last updated. The `updated_at` column is automatically updated by a trigger when a row is updated.

## Migration

The migration from the old schema to the normalized schema is handled by a series of SQL scripts:

1. `004_normalize_schema.sql` - Creates the new tables and migrates data from the accounts table
2. `005_normalize_hardware.sql` - Creates the new hardware table and migrates data from the old hardware table
3. `006_normalize_cards.sql` - Creates the new cards table and migrates data from the old cards table
4. `007_update_rls_views.sql` - Updates the RLS views to include the new tables

## Usage

To use the normalized schema, update your code to use the new tables and views:

- Use `accounts_normalized` instead of `accounts`
- Use `hardware_normalized` instead of `hardware`
- Use `cards_normalized` instead of `cards`
- Use the corresponding `_with_rls` views to ensure RLS is applied correctly

## Benefits

The normalized schema provides several benefits:

1. **Improved Data Integrity**: Foreign key constraints ensure that related data is consistent.
2. **Reduced Redundancy**: Data is stored in separate tables to avoid duplication.
3. **Better Performance**: Appropriate indexes improve query performance.
4. **Easier Maintenance**: The schema is more organized and easier to understand.
5. **Better Security**: RLS is consistently applied to all tables.
6. **Better Tracking**: Timestamps track when data was created and updated.
7. **Better Constraints**: Check constraints ensure that data meets specific criteria.
8. **Better Naming**: Column names are more consistent and descriptive.
9. **Better Documentation**: Each table and column has a comment describing its purpose.
10. **Better Relationships**: Relationships between tables are clearly defined.
