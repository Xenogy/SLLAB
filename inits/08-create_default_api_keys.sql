-- Create default API keys for existing Proxmox nodes and Windows VMs

-- Install the pgcrypto extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Function to create default API keys
CREATE OR REPLACE FUNCTION create_default_api_keys()
RETURNS VOID AS $$
DECLARE
    node_record RECORD;
    vm_record RECORD;
    api_key_value TEXT;
    api_key_hash TEXT;
    api_key_prefix TEXT;
BEGIN
    -- Create API keys for Proxmox nodes
    FOR node_record IN SELECT id, name, owner_id FROM proxmox_nodes
    LOOP
        -- Generate a random API key
        api_key_value := encode(gen_random_bytes(32), 'base64');
        api_key_value := replace(api_key_value, '/', '_');
        api_key_value := replace(api_key_value, '+', '-');
        api_key_value := replace(api_key_value, '=', '');

        -- Hash the API key for storage
        api_key_hash := encode(sha256(api_key_value::bytea), 'hex');

        -- Store the first 8 characters for display
        api_key_prefix := substring(api_key_value from 1 for 8);

        -- Insert the API key
        INSERT INTO api_keys (
            user_id, key_name, api_key, api_key_prefix, scopes, key_type, resource_id
        )
        VALUES (
            node_record.owner_id,
            'Proxmox Node ' || node_record.name,
            api_key_hash,
            api_key_prefix,
            ARRAY['read', 'write'],
            'proxmox_node',
            node_record.id
        )
        ON CONFLICT DO NOTHING;

        -- Log the API key for the node (in a real system, this would be sent to the node)
        RAISE NOTICE 'Created API key for Proxmox node %: %', node_record.name, api_key_value;
    END LOOP;

    -- Create API keys for Windows VMs
    FOR vm_record IN SELECT id, name, owner_id FROM vms
    LOOP
        -- Generate a random API key
        api_key_value := encode(gen_random_bytes(32), 'base64');
        api_key_value := replace(api_key_value, '/', '_');
        api_key_value := replace(api_key_value, '+', '-');
        api_key_value := replace(api_key_value, '=', '');

        -- Hash the API key for storage
        api_key_hash := encode(sha256(api_key_value::bytea), 'hex');

        -- Store the first 8 characters for display
        api_key_prefix := substring(api_key_value from 1 for 8);

        -- Insert the API key
        INSERT INTO api_keys (
            user_id, key_name, api_key, api_key_prefix, scopes, key_type, resource_id
        )
        VALUES (
            vm_record.owner_id,
            'Windows VM ' || vm_record.name,
            api_key_hash,
            api_key_prefix,
            ARRAY['read', 'write'],
            'windows_vm',
            vm_record.id
        )
        ON CONFLICT DO NOTHING;

        -- Log the API key for the VM (in a real system, this would be sent to the VM)
        RAISE NOTICE 'Created API key for Windows VM %: %', vm_record.name, api_key_value;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute the function to create default API keys
SELECT create_default_api_keys();

-- Drop the function after use
DROP FUNCTION create_default_api_keys();
