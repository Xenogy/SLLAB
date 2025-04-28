CREATE TABLE IF NOT EXISTS public.proxmox_nodes
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    name VARCHAR(100) NOT NULL,                                      -- Node name
    hostname VARCHAR(255) NOT NULL,                                  -- Hostname or IP address
    port INTEGER NOT NULL DEFAULT 8006,                              -- Port (default: 8006 for Proxmox)
    status VARCHAR(20) DEFAULT 'disconnected',                       -- Status (connected, disconnected, error)
    api_key VARCHAR(255) NOT NULL,                                   -- API key for authentication
    whitelist INTEGER[] DEFAULT '{}',                                -- Array of VMIDs to whitelist
    last_seen TIMESTAMP WITH TIME ZONE,                              -- Last time the node was seen
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    owner_id INTEGER REFERENCES public.users(id)                     -- Owner ID for RLS
);

COMMENT ON COLUMN public.proxmox_nodes.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.proxmox_nodes.name IS 'Node name';
COMMENT ON COLUMN public.proxmox_nodes.hostname IS 'Hostname or IP address';
COMMENT ON COLUMN public.proxmox_nodes.port IS 'Port (default: 8006 for Proxmox)';
COMMENT ON COLUMN public.proxmox_nodes.status IS 'Status (connected, disconnected, error)';
COMMENT ON COLUMN public.proxmox_nodes.api_key IS 'API key for authentication';
COMMENT ON COLUMN public.proxmox_nodes.whitelist IS 'Array of VMIDs to whitelist';
COMMENT ON COLUMN public.proxmox_nodes.last_seen IS 'Last time the node was seen';
COMMENT ON COLUMN public.proxmox_nodes.created_at IS 'Creation timestamp';
COMMENT ON COLUMN public.proxmox_nodes.updated_at IS 'Update timestamp';
COMMENT ON COLUMN public.proxmox_nodes.owner_id IS 'Owner ID for RLS';

-- Create indexes for better performance
CREATE INDEX idx_proxmox_nodes_name ON public.proxmox_nodes (name);
CREATE INDEX idx_proxmox_nodes_hostname ON public.proxmox_nodes (hostname);
CREATE INDEX idx_proxmox_nodes_status ON public.proxmox_nodes (status);
CREATE INDEX idx_proxmox_nodes_owner_id ON public.proxmox_nodes (owner_id);

-- Set default owner to admin user (id=1) for existing records
UPDATE public.proxmox_nodes SET owner_id = 1 WHERE owner_id IS NULL;

-- Make owner_id NOT NULL after setting default values
ALTER TABLE public.proxmox_nodes ALTER COLUMN owner_id SET NOT NULL;

-- Set table ownership
ALTER TABLE IF EXISTS public.proxmox_nodes
    OWNER to ps_user;

-- Grant permissions
GRANT ALL ON TABLE public.proxmox_nodes TO acc_user;
GRANT ALL ON TABLE public.proxmox_nodes TO ps_user;

-- Grant column-level permissions
GRANT ALL(id) ON public.proxmox_nodes TO acc_user;
GRANT ALL(name) ON public.proxmox_nodes TO acc_user;
GRANT ALL(hostname) ON public.proxmox_nodes TO acc_user;
GRANT ALL(port) ON public.proxmox_nodes TO acc_user;
GRANT ALL(status) ON public.proxmox_nodes TO acc_user;
GRANT ALL(api_key) ON public.proxmox_nodes TO acc_user;
GRANT ALL(whitelist) ON public.proxmox_nodes TO acc_user;
GRANT ALL(last_seen) ON public.proxmox_nodes TO acc_user;
GRANT ALL(created_at) ON public.proxmox_nodes TO acc_user;
GRANT ALL(updated_at) ON public.proxmox_nodes TO acc_user;
GRANT ALL(owner_id) ON public.proxmox_nodes TO acc_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE proxmox_nodes_id_seq TO acc_user;
