# Virtual Machines Table

This document describes the `vms` table in the AccountDB database, which stores information about virtual machines managed through Proxmox.

## Table Schema

The `vms` table has the following structure:

```sql
CREATE TABLE public.vms
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    vmid INTEGER NOT NULL,                                           -- Proxmox VMID
    name VARCHAR(100) NOT NULL,                                      -- VM name
    ip_address VARCHAR(45),                                          -- IP address (supports IPv4 and IPv6)
    status VARCHAR(20) DEFAULT 'stopped',                            -- Status (running, stopped, error)
    cpu_cores INTEGER,                                               -- Number of CPU cores
    memory_mb INTEGER,                                               -- Memory in MB
    disk_gb INTEGER,                                                 -- Disk size in GB
    proxmox_node VARCHAR(100),                                       -- Proxmox node name
    template_id INTEGER,                                             -- Template ID if created from template
    notes TEXT,                                                      -- Additional notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    owner_id INTEGER REFERENCES public.users(id)                     -- Owner ID for RLS
);
```

## Row-Level Security (RLS)

The `vms` table implements Row-Level Security (RLS) to ensure that users can only access their own virtual machines. The following RLS policies are applied:

1. **Admin Policy**: Administrators can access all virtual machines.
   ```sql
   CREATE POLICY vms_admin_policy ON public.vms
       FOR ALL
       TO PUBLIC
       USING (current_setting('app.current_user_role', TRUE) = 'admin');
   ```

2. **User Policy**: Regular users can only access virtual machines they own.
   ```sql
   CREATE POLICY vms_user_policy ON public.vms
       FOR ALL
       TO PUBLIC
       USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
   ```

## RLS View

An RLS view is provided for convenient access to virtual machines with RLS applied:

```sql
CREATE OR REPLACE VIEW public.vms_with_rls AS
SELECT * FROM public.vms
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;
```

## Usage

When accessing the `vms` table, always set the RLS context first:

```python
from db.rls_context import rls_context

# Using the context manager
with rls_context(conn, user_id, user_role):
    # Query the vms table or vms_with_rls view
    cursor.execute("SELECT * FROM vms_with_rls")
    vms = cursor.fetchall()
```

## Relationships

- **One-to-Many**: A user can own multiple virtual machines.
- **Many-to-One**: Multiple virtual machines can be created from the same template.
