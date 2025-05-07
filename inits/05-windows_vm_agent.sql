-- Windows VM Agent and Account Proxy Settings Tables

-- Create the windows_vm_agents table
CREATE TABLE IF NOT EXISTS windows_vm_agents (
    vm_id TEXT PRIMARY KEY,
    vm_name TEXT,
    api_key TEXT NOT NULL,
    status TEXT DEFAULT 'registered',
    ip_address TEXT,
    cpu_usage_percent FLOAT,
    memory_usage_percent FLOAT,
    disk_usage_percent FLOAT,
    uptime_seconds INTEGER,
    owner_id INTEGER,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the account_proxy_settings table
CREATE TABLE IF NOT EXISTS account_proxy_settings (
    account_id TEXT PRIMARY KEY REFERENCES accounts(acc_id) ON DELETE CASCADE,
    proxy_server TEXT,
    proxy_bypass TEXT,
    additional_settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create the default_proxy_settings table
CREATE TABLE IF NOT EXISTS default_proxy_settings (
    id SERIAL PRIMARY KEY,
    proxy_server TEXT,
    proxy_bypass TEXT,
    additional_settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default proxy settings if not exists
INSERT INTO default_proxy_settings (proxy_server, proxy_bypass, additional_settings)
SELECT 'http://default-proxy.example.com:8080', 'localhost;127.0.0.1;*.local', '{"timeout": 30}'
WHERE NOT EXISTS (SELECT 1 FROM default_proxy_settings);

-- Add Row-Level Security (RLS) to windows_vm_agents table
ALTER TABLE windows_vm_agents ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for windows_vm_agents table
CREATE POLICY windows_vm_agents_user_policy ON windows_vm_agents
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR
           current_setting('app.current_user_role')::TEXT = 'admin');

-- Grant permissions to the acc_user
GRANT SELECT, INSERT, UPDATE, DELETE ON windows_vm_agents TO acc_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON account_proxy_settings TO acc_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON default_proxy_settings TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE default_proxy_settings_id_seq TO acc_user;
