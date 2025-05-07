-- Add api_key column to windows_vm_agents table
ALTER TABLE windows_vm_agents ADD COLUMN IF NOT EXISTS api_key TEXT;

-- Make api_key column NOT NULL
-- First, update any existing rows to have a default value
UPDATE windows_vm_agents SET api_key = 'temp_key_' || vm_id WHERE api_key IS NULL;

-- Then set the NOT NULL constraint
ALTER TABLE windows_vm_agents ALTER COLUMN api_key SET NOT NULL;
