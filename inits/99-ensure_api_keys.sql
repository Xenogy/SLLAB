-- Final check to ensure API keys table exists and has proper data
-- This script runs last to make sure the API keys table is properly set up

-- Ensure the api_keys table exists
CREATE TABLE IF NOT EXISTS public.api_keys
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    user_id INTEGER NOT NULL REFERENCES public.users(id),            -- User ID (Foreign Key)
    key_name VARCHAR(100) NOT NULL,                                  -- Name/description of the API key
    api_key VARCHAR(64) NOT NULL,                                    -- API key (hashed)
    api_key_prefix VARCHAR(8) NOT NULL,                              -- First 8 characters of the API key (for display)
    scopes VARCHAR[] DEFAULT '{}',                                   -- Array of permission scopes
    expires_at TIMESTAMP WITH TIME ZONE,                             -- Expiration timestamp (NULL = never expires)
    last_used_at TIMESTAMP WITH TIME ZONE,                           -- When the key was last used
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    revoked BOOLEAN DEFAULT FALSE,                                   -- Whether the key has been revoked
    key_type VARCHAR(20) DEFAULT 'user',                             -- Type of API key (user, proxmox_node, windows_vm)
    resource_id INTEGER,                                             -- ID of the associated resource (proxmox node ID or VM ID)
    CONSTRAINT api_keys_api_key_unique UNIQUE (api_key)              -- Each API key must be unique
);

-- Grant permissions
GRANT ALL ON TABLE public.api_keys TO acc_user;
GRANT ALL ON TABLE public.api_keys TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE api_keys_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE api_keys_id_seq TO ps_user;

-- Enable Row-Level Security
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys FORCE ROW LEVEL SECURITY;

-- Create RLS policies for api_keys table
DROP POLICY IF EXISTS api_keys_admin_policy ON public.api_keys;
DROP POLICY IF EXISTS api_keys_user_policy ON public.api_keys;

CREATE POLICY api_keys_admin_policy ON public.api_keys
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY api_keys_user_policy ON public.api_keys
    FOR ALL
    TO PUBLIC
    USING (user_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type ON public.api_keys (key_type);
CREATE INDEX IF NOT EXISTS idx_api_keys_resource_id ON public.api_keys (resource_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type_resource_id ON public.api_keys (key_type, resource_id);

-- Install the pgcrypto extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Direct insertion of the API key for gpu1 node
DO $$
DECLARE
    node_id INTEGER;
    node_owner_id INTEGER;  -- Renamed to avoid ambiguity with column name
    api_key_value TEXT;
    api_key_hash TEXT;
    key_prefix TEXT;  -- Renamed to avoid ambiguity with column name
BEGIN
    -- Set the specific API key value
    api_key_value := 'v8akQodLgRLDqMyE9-2hDyzCFvJCsSD7a1Ry3PxNPtk';

    -- Get the node ID and owner ID for the gpu1 node
    SELECT id, owner_id INTO node_id, node_owner_id FROM proxmox_nodes WHERE name = 'gpu1';

    IF node_id IS NULL THEN
        RAISE NOTICE 'Proxmox node "gpu1" not found. No API key added.';
        RETURN;
    END IF;

    -- Hash the API key for storage
    api_key_hash := encode(sha256(api_key_value::bytea), 'hex');

    -- Store the first 8 characters for display
    key_prefix := substring(api_key_value from 1 for 8);

    -- Check if the API key already exists
    IF EXISTS (SELECT 1 FROM api_keys WHERE key_type = 'proxmox_node' AND resource_id = node_id) THEN
        -- Update the existing API key
        UPDATE api_keys
        SET api_key = api_key_hash,
            api_key_prefix = key_prefix,
            revoked = FALSE
        WHERE key_type = 'proxmox_node' AND resource_id = node_id;

        RAISE NOTICE 'Updated API key for Proxmox node gpu1: %', api_key_value;
    ELSE
        -- Insert a new API key
        INSERT INTO api_keys (
            user_id, key_name, api_key, api_key_prefix, scopes, key_type, resource_id
        )
        VALUES (
            node_owner_id,
            'Proxmox Node gpu1',
            api_key_hash,
            key_prefix,
            ARRAY['read', 'write'],
            'proxmox_node',
            node_id
        );

        RAISE NOTICE 'Added API key for Proxmox node gpu1: %', api_key_value;
    END IF;
END;
$$;
