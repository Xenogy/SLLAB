-- Settings Table for AccountDB
-- This script creates a table to store user-specific settings

CREATE TABLE IF NOT EXISTS public.user_settings
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    user_id INTEGER NOT NULL REFERENCES public.users(id),            -- User ID (Foreign Key)
    theme VARCHAR(20) DEFAULT 'light',                               -- UI Theme (light, dark, system)
    language VARCHAR(10) DEFAULT 'en',                               -- UI Language
    timezone VARCHAR(50) DEFAULT 'UTC',                              -- User's timezone
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',                    -- Date format preference
    time_format VARCHAR(20) DEFAULT '24h',                           -- Time format preference (12h, 24h)
    notifications_enabled BOOLEAN DEFAULT TRUE,                      -- Whether notifications are enabled
    email_notifications BOOLEAN DEFAULT TRUE,                        -- Whether email notifications are enabled
    auto_refresh_interval INTEGER DEFAULT 60,                        -- Auto-refresh interval in seconds
    items_per_page INTEGER DEFAULT 10,                               -- Number of items per page in lists
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    CONSTRAINT user_settings_user_id_unique UNIQUE (user_id)         -- Each user can have only one settings record
);

-- Create API keys table for user authentication
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
GRANT ALL ON TABLE public.user_settings TO acc_user;
GRANT ALL ON TABLE public.user_settings TO ps_user;
GRANT ALL ON TABLE public.api_keys TO acc_user;
GRANT ALL ON TABLE public.api_keys TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE user_settings_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE user_settings_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE api_keys_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE api_keys_id_seq TO ps_user;

-- Enable Row-Level Security
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user_settings
CREATE POLICY user_settings_user_policy ON public.user_settings
    USING (user_id = current_setting('app.current_user_id')::INTEGER OR
           current_setting('app.current_user_role')::TEXT = 'admin');

-- Create RLS policies for api_keys
CREATE POLICY api_keys_user_policy ON public.api_keys
    USING (user_id = current_setting('app.current_user_id')::INTEGER OR
           current_setting('app.current_user_role')::TEXT = 'admin');

-- Create indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type ON public.api_keys (key_type);
CREATE INDEX IF NOT EXISTS idx_api_keys_resource_id ON public.api_keys (resource_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type_resource_id ON public.api_keys (key_type, resource_id);

-- Insert default settings for existing users
INSERT INTO public.user_settings (user_id, theme, language, timezone)
SELECT id, 'light', 'en', 'UTC' FROM public.users
WHERE NOT EXISTS (
    SELECT 1 FROM public.user_settings WHERE user_settings.user_id = users.id
);
