CREATE TABLE IF NOT EXISTS public.vms
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    vmid INTEGER NOT NULL,                                           -- Proxmox VMID
    name VARCHAR(100) NOT NULL,                                      -- VM name
    ip_address VARCHAR(45),                                          -- IP address (supports IPv4 and IPv6)
    status VARCHAR(20) DEFAULT 'stopped',                            -- Status (running, stopped, error)
    cpu_cores INTEGER DEFAULT 0,                                     -- Number of CPU cores
    cpu_usage_percent NUMERIC(5,1) DEFAULT 0,                        -- CPU usage percentage
    memory_mb INTEGER DEFAULT 0,                                     -- Memory in MB
    disk_gb INTEGER DEFAULT 0,                                       -- Disk size in GB
    uptime_seconds BIGINT DEFAULT 0,                                 -- Uptime in seconds
    proxmox_node_id INTEGER REFERENCES public."proxmox_nodes"(id),   -- Proxmox node ID
    template_id INTEGER DEFAULT 0,                                   -- Template ID if created from template
    notes TEXT DEFAULT '',                                           -- Additional notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    owner_id INTEGER REFERENCES public.users(id)                     -- Owner ID for RLS
);

COMMENT ON COLUMN public.vms.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.vms.vmid IS 'Proxmox VMID';
COMMENT ON COLUMN public.vms.name IS 'VM name';
COMMENT ON COLUMN public.vms.ip_address IS 'IP address (supports IPv4 and IPv6)';
COMMENT ON COLUMN public.vms.status IS 'Status (running, stopped, error)';
COMMENT ON COLUMN public.vms.cpu_cores IS 'Number of CPU cores';
COMMENT ON COLUMN public.vms.cpu_usage_percent IS 'CPU usage percentage';
COMMENT ON COLUMN public.vms.memory_mb IS 'Memory in MB';
COMMENT ON COLUMN public.vms.disk_gb IS 'Disk size in GB';
COMMENT ON COLUMN public.vms.uptime_seconds IS 'Uptime in seconds';
COMMENT ON COLUMN public.vms.proxmox_node_id IS 'Proxmox node ID';
COMMENT ON COLUMN public.vms.template_id IS 'Template ID if created from template';
COMMENT ON COLUMN public.vms.notes IS 'Additional notes';
COMMENT ON COLUMN public.vms.created_at IS 'Creation timestamp';
COMMENT ON COLUMN public.vms.updated_at IS 'Update timestamp';
COMMENT ON COLUMN public.vms.owner_id IS 'Owner ID for RLS';

-- Create indexes for better performance
CREATE INDEX idx_vms_vmid ON public.vms (vmid);
CREATE INDEX idx_vms_name ON public.vms (name);
CREATE INDEX idx_vms_ip_address ON public.vms (ip_address);
CREATE INDEX idx_vms_status ON public.vms (status);
CREATE INDEX idx_vms_owner_id ON public.vms (owner_id);
CREATE INDEX idx_vms_proxmox_node_id ON public.vms (proxmox_node_id);

-- Set default owner to admin user (id=1) for existing records
UPDATE public.vms SET owner_id = 1 WHERE owner_id IS NULL;

-- Make owner_id NOT NULL after setting default values
ALTER TABLE public.vms ALTER COLUMN owner_id SET NOT NULL;

-- Set table ownership
ALTER TABLE IF EXISTS public.vms
    OWNER to ps_user;

-- Grant permissions
GRANT ALL ON TABLE public.vms TO acc_user;
GRANT ALL ON TABLE public.vms TO ps_user;

-- Grant column-level permissions
GRANT ALL(id) ON public.vms TO acc_user;
GRANT ALL(vmid) ON public.vms TO acc_user;
GRANT ALL(name) ON public.vms TO acc_user;
GRANT ALL(ip_address) ON public.vms TO acc_user;
GRANT ALL(status) ON public.vms TO acc_user;
GRANT ALL(cpu_cores) ON public.vms TO acc_user;
GRANT ALL(memory_mb) ON public.vms TO acc_user;
GRANT ALL(disk_gb) ON public.vms TO acc_user;
GRANT ALL(proxmox_node_id) ON public.vms TO acc_user;
GRANT ALL(template_id) ON public.vms TO acc_user;
GRANT ALL(notes) ON public.vms TO acc_user;
GRANT ALL(created_at) ON public.vms TO acc_user;
GRANT ALL(updated_at) ON public.vms TO acc_user;
GRANT ALL(owner_id) ON public.vms TO acc_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE vms_id_seq TO acc_user;
