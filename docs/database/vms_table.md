# Virtual Machines (VMs) Table Documentation

## Overview

The `vms` table stores information about virtual machines managed through Proxmox. This table is a key component of the Proxmox integration feature, allowing users to manage and monitor their virtual machines through the AccountDB system.

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
    proxmox_node INTEGER NOT NULL,                                   -- Proxmox node ID (foreign key)
    template_id INTEGER,                                             -- Template ID if created from template
    notes TEXT,                                                      -- Additional notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    owner_id INTEGER REFERENCES public.users(id) NOT NULL            -- Owner ID for RLS
);

-- Unique constraint for vmid and proxmox_node combination
ALTER TABLE public.vms ADD CONSTRAINT vms_vmid_node_unique UNIQUE (vmid, proxmox_node);

-- Foreign key to proxmox_nodes table
ALTER TABLE public.vms ADD CONSTRAINT vms_proxmox_node_fkey FOREIGN KEY (proxmox_node) REFERENCES public.proxmox_nodes(id);

-- Check constraint for status
ALTER TABLE public.vms ADD CONSTRAINT vms_status_check CHECK (status IN ('running', 'stopped', 'error'));
```

## Columns

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
| proxmox_node  | INTEGER   | No       | Proxmox node ID (foreign key)              |
| template_id   | INTEGER   | Yes      | Template ID if created from template       |
| notes         | TEXT      | Yes      | Additional notes                           |
| created_at    | TIMESTAMP | No       | Creation timestamp                         |
| updated_at    | TIMESTAMP | No       | Update timestamp                           |
| owner_id      | INTEGER   | No       | ID of the user who owns the VM             |

## Constraints

- Primary Key: `id`
- Foreign Key: `owner_id` references `users(id)`
- Foreign Key: `proxmox_node` references `proxmox_nodes(id)`
- Check: `status IN ('running', 'stopped', 'error')`
- Unique: `(vmid, proxmox_node)` - A VM ID must be unique within a Proxmox node

## Indexes

The following indexes are created to improve query performance:

```sql
CREATE INDEX vms_vmid_idx ON public.vms(vmid);
CREATE INDEX vms_name_idx ON public.vms(name);
CREATE INDEX vms_ip_address_idx ON public.vms(ip_address);
CREATE INDEX vms_status_idx ON public.vms(status);
CREATE INDEX vms_owner_id_idx ON public.vms(owner_id);
CREATE INDEX vms_proxmox_node_idx ON public.vms(proxmox_node);
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

- **Many-to-One**: A VM belongs to one user (owner)
- **Many-to-One**: A VM belongs to one Proxmox node
- **One-to-Many**: A VM can have multiple related records in other tables (e.g., monitoring data)

## API Integration

The `vms` table is accessed through the following API endpoints:

- `GET /vms`: Get a list of VMs (filtered by RLS)
- `GET /vms/{id}`: Get a specific VM by ID
- `POST /vms`: Create a new VM
- `PUT /vms/{id}`: Update an existing VM
- `DELETE /vms/{id}`: Delete a VM
- `GET /vms/proxmox/{node_id}`: Get VMs for a specific Proxmox node

## Proxmox Host Agent Integration

The Proxmox Host Agent synchronizes VM information from Proxmox to the `vms` table. The agent:

1. Retrieves VM information from Proxmox
2. Formats the data to match the `vms` table structure
3. Creates or updates records in the `vms` table
4. Updates VM status and resource information

## Monitoring and Statistics

The `vms` table is used for monitoring and statistics:

- VM status monitoring
- Resource usage tracking
- VM creation and deletion auditing
- Owner activity monitoring

## Security Considerations

- Access to the `vms` table is controlled by Row-Level Security
- VM operations are logged for audit purposes
- VM creation is restricted by user permissions
- Sensitive VM information is protected

## Troubleshooting

Common issues with the `vms` table:

1. **VM Not Visible**: Check that the VM's `owner_id` is correctly set to the user's ID
2. **Duplicate VM Error**: Ensure that the combination of `vmid` and `proxmox_node` is unique
3. **Status Not Updating**: Verify that the Proxmox Host Agent is running and properly configured
4. **RLS Not Working**: Check that the database connection is using the correct RLS context
