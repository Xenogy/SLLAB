-- Migration script to update the api_keys table to support different types of API keys

-- Add type column to api_keys table
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS key_type VARCHAR(20) DEFAULT 'user';

-- Add resource_id column to api_keys table
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS resource_id INTEGER;

-- Add foreign key constraints based on key_type
-- Note: We can't use a direct foreign key with a condition, so we'll use triggers to enforce this

-- Create a function to validate the resource_id based on key_type
CREATE OR REPLACE FUNCTION validate_api_key_resource()
RETURNS TRIGGER AS $$
BEGIN
    -- For user type, resource_id should be NULL
    IF NEW.key_type = 'user' AND NEW.resource_id IS NOT NULL THEN
        RAISE EXCEPTION 'User API keys should not have a resource_id';
    END IF;
    
    -- For proxmox_node type, resource_id should exist in proxmox_nodes table
    IF NEW.key_type = 'proxmox_node' THEN
        IF NEW.resource_id IS NULL THEN
            RAISE EXCEPTION 'Proxmox node API keys must have a resource_id';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM public.proxmox_nodes WHERE id = NEW.resource_id) THEN
            RAISE EXCEPTION 'Resource ID % does not exist in proxmox_nodes table', NEW.resource_id;
        END IF;
    END IF;
    
    -- For windows_vm type, resource_id should exist in vms table
    IF NEW.key_type = 'windows_vm' THEN
        IF NEW.resource_id IS NULL THEN
            RAISE EXCEPTION 'Windows VM API keys must have a resource_id';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM public.vms WHERE id = NEW.resource_id) THEN
            RAISE EXCEPTION 'Resource ID % does not exist in vms table', NEW.resource_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to validate resource_id on insert or update
DROP TRIGGER IF EXISTS validate_api_key_resource_trigger ON public.api_keys;
CREATE TRIGGER validate_api_key_resource_trigger
BEFORE INSERT OR UPDATE ON public.api_keys
FOR EACH ROW
EXECUTE FUNCTION validate_api_key_resource();

-- Update the RLS policy for api_keys to handle the new columns
DROP POLICY IF EXISTS api_keys_user_policy ON public.api_keys;
CREATE POLICY api_keys_user_policy ON public.api_keys
    USING (
        (user_id = current_setting('app.current_user_id')::INTEGER) OR 
        (current_setting('app.current_user_role')::TEXT = 'admin')
    );

-- Add an index on key_type and resource_id for better performance
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type ON public.api_keys (key_type);
CREATE INDEX IF NOT EXISTS idx_api_keys_resource_id ON public.api_keys (resource_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type_resource_id ON public.api_keys (key_type, resource_id);

-- Comment on new columns
COMMENT ON COLUMN public.api_keys.key_type IS 'Type of API key (user, proxmox_node, windows_vm)';
COMMENT ON COLUMN public.api_keys.resource_id IS 'ID of the associated resource (proxmox node ID or VM ID)';
