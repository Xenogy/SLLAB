# Database Schema

## Overview

The AccountDB system uses a PostgreSQL database to store information about users, accounts, hardware profiles, cards, and account status. This document describes the database schema, including tables, columns, constraints, and relationships.

## Tables

The database consists of the following tables:

- `users`: Stores information about users of the system.
- `accounts`: Stores information about Steam accounts.
- `hardware`: Stores information about hardware profiles associated with accounts.
- `cards`: Stores information about Steam gift cards.
- `account_status`: Stores information about the status of accounts.
- `vms`: Stores information about virtual machines managed through Proxmox.

### Users Table

The `users` table stores information about users of the system.

#### Columns

| Column Name    | Data Type | Nullable | Description                                |
|----------------|-----------|----------|--------------------------------------------|
| id             | SERIAL    | No       | Primary key                                |
| username       | TEXT      | No       | Username (unique)                          |
| email          | TEXT      | No       | Email address (unique)                     |
| password_hash  | TEXT      | No       | Hashed password                            |
| role           | TEXT      | No       | Role (e.g., "user", "admin")               |
| is_active      | BOOLEAN   | No       | Whether the user is active                 |
| created_at     | TIMESTAMP | No       | Timestamp when the user was created        |

#### Constraints

- Primary Key: `id`
- Unique: `username`
- Unique: `email`
- Check: `role IN ('user', 'admin')`
- Check: `is_active IN (TRUE, FALSE)`

### Accounts Table

The `accounts` table stores information about Steam accounts.

#### Columns

| Column Name        | Data Type | Nullable | Description                                |
|--------------------|-----------|----------|--------------------------------------------|
| acc_id             | TEXT      | No       | Primary key                                |
| acc_username       | TEXT      | No       | Steam account username                     |
| acc_password       | TEXT      | No       | Steam account password                     |
| acc_email_address  | TEXT      | No       | Email address associated with the account  |
| acc_email_password | TEXT      | No       | Password for the email account             |
| acc_created_at     | TIMESTAMP | No       | Timestamp when the account was created     |
| prime              | BOOLEAN   | No       | Whether the account has Prime status       |
| lock               | BOOLEAN   | No       | Whether the account is locked              |
| perm_lock          | BOOLEAN   | No       | Whether the account is permanently locked  |
| owner_id           | INTEGER   | No       | ID of the user who owns the account        |

#### Constraints

- Primary Key: `acc_id`
- Foreign Key: `owner_id` references `users(id)`
- Check: `prime IN (TRUE, FALSE)`
- Check: `lock IN (TRUE, FALSE)`
- Check: `perm_lock IN (TRUE, FALSE)`

### Hardware Table

The `hardware` table stores information about hardware profiles associated with accounts.

#### Columns

| Column Name   | Data Type | Nullable | Description                                |
|---------------|-----------|----------|--------------------------------------------|
| id            | SERIAL    | No       | Primary key                                |
| acc_id        | TEXT      | No       | ID of the account                          |
| hw_id         | TEXT      | No       | Hardware ID                                |
| hw_name       | TEXT      | No       | Name of the hardware                       |
| hw_type       | TEXT      | No       | Type of hardware                           |
| hw_created_at | TIMESTAMP | No       | Timestamp when the hardware was created    |

#### Constraints

- Primary Key: `id`
- Foreign Key: `acc_id` references `accounts(acc_id)`
- Unique: `hw_id`

### Cards Table

The `cards` table stores information about Steam gift cards.

#### Columns

| Column Name     | Data Type | Nullable | Description                                |
|-----------------|-----------|----------|--------------------------------------------|
| id              | SERIAL    | No       | Primary key                                |
| acc_id          | TEXT      | No       | ID of the account                          |
| card_id         | TEXT      | No       | Card ID                                    |
| card_name       | TEXT      | No       | Name of the card                           |
| card_type       | TEXT      | No       | Type of card                               |
| card_created_at | TIMESTAMP | No       | Timestamp when the card was created        |
| owner_id        | INTEGER   | No       | ID of the user who owns the card           |

#### Constraints

- Primary Key: `id`
- Foreign Key: `acc_id` references `accounts(acc_id)`
- Foreign Key: `owner_id` references `users(id)`
- Unique: `card_id`

### Account Status Table

The `account_status` table stores information about the status of accounts.

#### Columns

| Column Name  | Data Type | Nullable | Description                                |
|--------------|-----------|----------|--------------------------------------------|
| id           | SERIAL    | No       | Primary key                                |
| acc_id       | TEXT      | No       | ID of the account                          |
| status       | TEXT      | No       | Status of the account                      |
| last_updated | TIMESTAMP | No       | Timestamp when the status was last updated |

#### Constraints

- Primary Key: `id`
- Foreign Key: `acc_id` references `accounts(acc_id)`
- Check: `status IN ('active', 'inactive', 'suspended')`

### Virtual Machines Table

The `vms` table stores information about virtual machines managed through Proxmox.

#### Columns

| Column Name   | Data Type | Nullable | Description                                |
|---------------|-----------|----------|--------------------------------------------|
| id            | SERIAL    | No       | Primary key                                |
| vmid          | INTEGER   | No       | Proxmox VMID                               |
| name          | VARCHAR   | No       | VM name                                    |
| ip_address    | VARCHAR   | Yes      | IP address (supports IPv4 and IPv6)        |
| status        | VARCHAR   | No       | Status (running, stopped, error)           |
| cpu_cores     | INTEGER   | Yes      | Number of CPU cores                        |
| memory_mb     | INTEGER   | Yes      | Memory in MB                               |
| disk_gb       | INTEGER   | Yes      | Disk size in GB                            |
| proxmox_node  | VARCHAR   | Yes      | Proxmox node name                          |
| template_id   | INTEGER   | Yes      | Template ID if created from template       |
| notes         | TEXT      | Yes      | Additional notes                           |
| created_at    | TIMESTAMP | No       | Creation timestamp                         |
| updated_at    | TIMESTAMP | No       | Update timestamp                           |
| owner_id      | INTEGER   | No       | ID of the user who owns the VM             |

#### Constraints

- Primary Key: `id`
- Foreign Key: `owner_id` references `users(id)`
- Check: `status IN ('running', 'stopped', 'error')`

## Relationships

The database has the following relationships:

- One-to-Many: A user can own multiple accounts.
- One-to-Many: A user can own multiple cards.
- One-to-Many: A user can own multiple virtual machines.
- One-to-Many: An account can have multiple hardware profiles.
- One-to-Many: An account can have multiple cards.
- One-to-One: An account can have one account status.

## Row-Level Security (RLS)

The database uses PostgreSQL's Row-Level Security (RLS) feature to ensure that users can only access their own data. RLS policies are defined for each table, ensuring that users can only access rows that they own.

### Accounts Table RLS Policy

```sql
CREATE POLICY accounts_user_policy ON accounts
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR current_setting('app.current_user_role') = 'admin');
```

This policy ensures that users can only access accounts they own, while administrators can access all accounts.

### Hardware Table RLS Policy

```sql
CREATE POLICY hardware_user_policy ON hardware
    USING (acc_id IN (SELECT acc_id FROM accounts WHERE owner_id = current_setting('app.current_user_id')::INTEGER) OR current_setting('app.current_user_role') = 'admin');
```

This policy ensures that users can only access hardware profiles associated with accounts they own, while administrators can access all hardware profiles.

### Cards Table RLS Policy

```sql
CREATE POLICY cards_user_policy ON cards
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR current_setting('app.current_user_role') = 'admin');
```

This policy ensures that users can only access cards they own, while administrators can access all cards.

### Account Status Table RLS Policy

```sql
CREATE POLICY account_status_user_policy ON account_status
    USING (acc_id IN (SELECT acc_id FROM accounts WHERE owner_id = current_setting('app.current_user_id')::INTEGER) OR current_setting('app.current_user_role') = 'admin');
```

This policy ensures that users can only access account status information for accounts they own, while administrators can access all account status information.

### Virtual Machines Table RLS Policy

```sql
CREATE POLICY vms_user_policy ON vms
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR current_setting('app.current_user_role') = 'admin');
```

This policy ensures that users can only access virtual machines they own, while administrators can access all virtual machines.

## Indexes

The database uses indexes to improve query performance. The following indexes are defined:

- `users_username_idx`: Index on `users(username)` for faster user lookup by username.
- `users_email_idx`: Index on `users(email)` for faster user lookup by email.
- `accounts_owner_id_idx`: Index on `accounts(owner_id)` for faster account lookup by owner.
- `hardware_acc_id_idx`: Index on `hardware(acc_id)` for faster hardware lookup by account.
- `cards_acc_id_idx`: Index on `cards(acc_id)` for faster card lookup by account.
- `cards_owner_id_idx`: Index on `cards(owner_id)` for faster card lookup by owner.
- `account_status_acc_id_idx`: Index on `account_status(acc_id)` for faster account status lookup by account.
- `vms_vmid_idx`: Index on `vms(vmid)` for faster VM lookup by Proxmox VMID.
- `vms_name_idx`: Index on `vms(name)` for faster VM lookup by name.
- `vms_ip_address_idx`: Index on `vms(ip_address)` for faster VM lookup by IP address.
- `vms_status_idx`: Index on `vms(status)` for faster VM lookup by status.
- `vms_owner_id_idx`: Index on `vms(owner_id)` for faster VM lookup by owner.

## Conclusion

The AccountDB database schema is designed to ensure data integrity, security, and performance. It uses constraints, relationships, and indexes to maintain data quality and improve query performance, while Row-Level Security ensures that users can only access their own data.

For more detailed information about the database, please refer to the SQL initialization scripts in the `sql` directory.
