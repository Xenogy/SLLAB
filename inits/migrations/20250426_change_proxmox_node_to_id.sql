-- Migration script to change proxmox_node column in vms table from node name to node ID

-- First, create a temporary column to store the node ID
ALTER TABLE public.vms ADD COLUMN proxmox_node_id INTEGER;

-- Update the temporary column with the corresponding node ID
UPDATE public.vms v
SET proxmox_node_id = pn.id
FROM public.proxmox_nodes pn
WHERE v.proxmox_node = pn.name;

-- Drop the foreign key constraint on the proxmox_node column
ALTER TABLE public.vms DROP CONSTRAINT IF EXISTS vms_proxmox_node_fkey;

-- Drop the proxmox_node column
ALTER TABLE public.vms DROP COLUMN proxmox_node;

-- Rename the temporary column to proxmox_node_id
ALTER TABLE public.vms RENAME COLUMN proxmox_node_id TO proxmox_node_id;

-- Add a foreign key constraint to the proxmox_node_id column
ALTER TABLE public.vms ADD CONSTRAINT vms_proxmox_node_id_fkey FOREIGN KEY (proxmox_node_id) REFERENCES public.proxmox_nodes(id);

-- Create an index on the proxmox_node_id column
CREATE INDEX idx_vms_proxmox_node_id ON public.vms (proxmox_node_id);

-- Add a comment to the proxmox_node_id column
COMMENT ON COLUMN public.vms.proxmox_node_id IS 'Proxmox node ID';

-- Grant permissions on the proxmox_node_id column
GRANT ALL(proxmox_node_id) ON public.vms TO acc_user;
