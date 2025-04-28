# Database Schema and RLS Implementation

## Overview

The database schema is designed to store account information, hardware profiles, and user data with proper security controls. PostgreSQL's Row-Level Security (RLS) is used to enforce data isolation between users.

## Tables

### users

Stores user information for authentication and authorization.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP,
    avatar_url VARCHAR(255)
);
```

### accounts

Stores account information with owner reference for RLS.

```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    acc_id VARCHAR(50) UNIQUE NOT NULL,
    acc_username VARCHAR(50) NOT NULL,
    acc_password VARCHAR(100) NOT NULL,
    acc_email_address VARCHAR(100),
    acc_email_password VARCHAR(100),
    acc_vault_address VARCHAR(100),
    acc_vault_password VARCHAR(100),
    acc_created_at BIGINT,
    acc_session_start BIGINT,
    acc_steamguard_account_name VARCHAR(100),
    acc_confirm_type INTEGER,
    acc_device_id VARCHAR(100),
    acc_identity_secret VARCHAR(100),
    acc_revocation_code VARCHAR(100),
    acc_secret_1 VARCHAR(100),
    acc_serial_number VARCHAR(100),
    acc_server_time VARCHAR(100),
    acc_shared_secret VARCHAR(100),
    acc_status INTEGER,
    acc_token_gid VARCHAR(100),
    acc_uri VARCHAR(255),
    prime BOOLEAN DEFAULT FALSE,
    lock BOOLEAN DEFAULT FALSE,
    perm_lock BOOLEAN DEFAULT FALSE,
    farmlabs_upload BOOLEAN DEFAULT FALSE,
    owner_id INTEGER REFERENCES users(id) NOT NULL
);
```

### hardware

Stores hardware profile information with owner reference for RLS.

```sql
CREATE TABLE hardware (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cpu VARCHAR(100) NOT NULL,
    gpu VARCHAR(100) NOT NULL,
    ram VARCHAR(50) NOT NULL,
    storage VARCHAR(100) NOT NULL,
    os VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    owner_id INTEGER REFERENCES users(id) NOT NULL
);
```

### cards

Stores Steam gift card information with owner reference for RLS.

```sql
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    card_number VARCHAR(30) NOT NULL,
    card_holder VARCHAR(100) NOT NULL,
    expiry_date VARCHAR(10) NOT NULL,
    cvv VARCHAR(5) NOT NULL,
    billing_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    owner_id INTEGER REFERENCES users(id) NOT NULL
);
```

## Row-Level Security (RLS) Implementation

### Session Variables

Two session variables are used to control RLS:

1. `app.current_user_id`: The ID of the currently authenticated user
2. `app.current_user_role`: The role of the currently authenticated user (admin or user)

### RLS Policies

#### accounts Table

```sql
-- Enable RLS on accounts table
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;

-- User policy: Users can only see their own accounts
CREATE POLICY accounts_user_policy ON public.accounts
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

-- Admin policy: Admins can see all accounts
CREATE POLICY accounts_admin_policy ON public.accounts
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');
```

#### hardware Table

```sql
-- Enable RLS on hardware table
ALTER TABLE public.hardware ENABLE ROW LEVEL SECURITY;

-- User policy: Users can only see their own hardware profiles
CREATE POLICY hardware_user_policy ON public.hardware
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

-- Admin policy: Admins can see all hardware profiles
CREATE POLICY hardware_admin_policy ON public.hardware
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');
```

#### cards Table

```sql
-- Enable RLS on cards table
ALTER TABLE public.cards ENABLE ROW LEVEL SECURITY;

-- User policy: Users can only see their own cards
CREATE POLICY cards_user_policy ON public.cards
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

-- Admin policy: Admins can see all cards
CREATE POLICY cards_admin_policy ON public.cards
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');
```

## Database Connection Management

### User-Specific Connection

A context manager is used to create database connections with the appropriate RLS context:

```python
@contextmanager
def get_user_db_connection(user_id=None, user_role=None):
    conn = get_connection()
    try:
        if conn and user_id is not None and user_role is not None:
            # Set session variables for RLS
            cursor = conn.cursor()
            cursor.execute("SET app.current_user_id = %s", (str(user_id),))
            cursor.execute("SET app.current_user_role = %s", (str(user_role),))
            cursor.close()
        yield conn
    finally:
        if conn:
            return_connection(conn)
```

## Current Issues and Improvement Areas

1. **Inconsistent Connection Usage**
   - Some endpoints use the global `conn` variable instead of `get_user_db_connection`
   - This bypasses RLS and allows users to see data they shouldn't have access to

2. **Missing Owner IDs**
   - Some records may not have an `owner_id` set
   - Default assignment to admin user may not be appropriate

3. **RLS Testing**
   - Lack of comprehensive testing for RLS policies
   - No automated verification that RLS is working correctly

## Recommended Database Improvements

1. **Consistent Connection Usage**
   - Replace all uses of the global `conn` variable with `get_user_db_connection`
   - Ensure all database operations set the appropriate RLS context

2. **Data Ownership**
   - Add a data migration to ensure all records have a valid `owner_id`
   - Implement triggers to prevent records from being created without an `owner_id`

3. **Enhanced RLS Policies**
   - Consider more granular policies (e.g., separate policies for SELECT, INSERT, UPDATE, DELETE)
   - Add policies for new tables as they are created

4. **Connection Pooling**
   - Optimize connection pooling settings for better performance
   - Implement connection monitoring and logging
