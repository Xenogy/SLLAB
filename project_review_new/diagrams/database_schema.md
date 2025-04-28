# Database Schema Diagram

This diagram illustrates the database schema of the AccountDB system, showing tables, relationships, and key fields.

```mermaid
erDiagram
    USERS {
        int id PK
        string username
        string password_hash
        string email
        boolean is_admin
        timestamp created_at
        timestamp updated_at
    }
    
    ACCOUNTS {
        int id PK
        string name
        string description
        int owner_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    HARDWARE {
        int id PK
        string name
        string type
        string specs
        int account_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    VMS {
        int id PK
        string name
        string description
        int vmid
        int proxmox_node_id FK
        int account_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    PROXMOX_NODES {
        int id PK
        string name
        string ip_address
        int port
        string username
        string token_name
        string token_value
        timestamp created_at
        timestamp updated_at
    }
    
    WHITELIST {
        int id PK
        int vm_id FK
        int user_id FK
        timestamp created_at
    }
    
    USERS ||--o{ ACCOUNTS : "owns"
    ACCOUNTS ||--o{ HARDWARE : "has"
    ACCOUNTS ||--o{ VMS : "has"
    PROXMOX_NODES ||--o{ VMS : "hosts"
    VMS ||--o{ WHITELIST : "has"
    USERS ||--o{ WHITELIST : "has access to"
```

## Schema Description

The AccountDB database schema consists of the following tables:

### USERS
- Stores user information including authentication details
- Primary key: `id`
- Contains fields for username, password hash, email, and admin status
- Has timestamps for creation and updates

### ACCOUNTS
- Stores account information
- Primary key: `id`
- Foreign key: `owner_id` references USERS.id
- Contains fields for name and description
- Has timestamps for creation and updates

### HARDWARE
- Stores hardware resource information
- Primary key: `id`
- Foreign key: `account_id` references ACCOUNTS.id
- Contains fields for name, type, and specifications
- Has timestamps for creation and updates

### VMS
- Stores virtual machine information
- Primary key: `id`
- Foreign keys: `proxmox_node_id` references PROXMOX_NODES.id, `account_id` references ACCOUNTS.id
- Contains fields for name, description, and Proxmox VM ID
- Has timestamps for creation and updates

### PROXMOX_NODES
- Stores Proxmox node information
- Primary key: `id`
- Contains fields for name, IP address, port, and authentication details
- Has timestamps for creation and updates

### WHITELIST
- Stores VM access permissions
- Primary key: `id`
- Foreign keys: `vm_id` references VMS.id, `user_id` references USERS.id
- Has timestamp for creation

## Row-Level Security (RLS)

The database implements Row-Level Security (RLS) policies to ensure data isolation:

1. Users can only see accounts they own
2. Users can only see hardware associated with accounts they own
3. Users can only see VMs associated with accounts they own or VMs they have whitelist access to
4. Admin users can see all data
