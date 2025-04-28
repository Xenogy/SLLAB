-- Setup Row-Level Security (RLS) for AccountDB
-- This script should be run during database initialization

-- Create app schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS app;

-- Create function to set RLS context
CREATE OR REPLACE FUNCTION set_rls_context(user_id INTEGER, user_role TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
    PERFORM set_config('app.current_user_role', user_role, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Create function to clear RLS context
CREATE OR REPLACE FUNCTION clear_rls_context()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', NULL, FALSE);
    PERFORM set_config('app.current_user_role', NULL, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Make sure acc_user cannot bypass RLS
ALTER ROLE acc_user NOBYPASSRLS;

-- Grant necessary permissions to acc_user
GRANT USAGE ON SCHEMA public TO acc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO acc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO acc_user;
GRANT EXECUTE ON FUNCTION set_rls_context(INTEGER, TEXT) TO acc_user;
GRANT EXECUTE ON FUNCTION clear_rls_context() TO acc_user;

-- Enable RLS on tables
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts FORCE ROW LEVEL SECURITY;

ALTER TABLE public.hardware ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hardware FORCE ROW LEVEL SECURITY;

ALTER TABLE public.cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cards FORCE ROW LEVEL SECURITY;

ALTER TABLE public.vms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vms FORCE ROW LEVEL SECURITY;

ALTER TABLE public.proxmox_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proxmox_nodes FORCE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS accounts_user_policy ON public.accounts;
DROP POLICY IF EXISTS accounts_admin_policy ON public.accounts;
DROP POLICY IF EXISTS hardware_user_policy ON public.hardware;
DROP POLICY IF EXISTS hardware_admin_policy ON public.hardware;
DROP POLICY IF EXISTS cards_user_policy ON public.cards;
DROP POLICY IF EXISTS cards_admin_policy ON public.cards;
DROP POLICY IF EXISTS vms_user_policy ON public.vms;
DROP POLICY IF EXISTS vms_admin_policy ON public.vms;
DROP POLICY IF EXISTS proxmox_nodes_user_policy ON public.proxmox_nodes;
DROP POLICY IF EXISTS proxmox_nodes_admin_policy ON public.proxmox_nodes;

-- Create RLS policies for accounts table
CREATE POLICY accounts_admin_policy ON public.accounts
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY accounts_user_policy ON public.accounts
    FOR ALL
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create RLS policies for hardware table
CREATE POLICY hardware_admin_policy ON public.hardware
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY hardware_user_policy ON public.hardware
    FOR ALL
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create RLS policies for cards table
CREATE POLICY cards_admin_policy ON public.cards
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY cards_user_policy ON public.cards
    FOR ALL
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create RLS policies for vms table
CREATE POLICY vms_admin_policy ON public.vms
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY vms_user_policy ON public.vms
    FOR ALL
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create RLS policies for proxmox_nodes table
CREATE POLICY proxmox_nodes_admin_policy ON public.proxmox_nodes
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY proxmox_nodes_user_policy ON public.proxmox_nodes
    FOR ALL
    TO PUBLIC
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create RLS views for accounts table
CREATE OR REPLACE VIEW public.accounts_with_rls AS
SELECT * FROM public.accounts
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;

-- Create RLS views for hardware table
CREATE OR REPLACE VIEW public.hardware_with_rls AS
SELECT * FROM public.hardware
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;

-- Create RLS views for cards table
CREATE OR REPLACE VIEW public.cards_with_rls AS
SELECT * FROM public.cards
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;

-- Create RLS views for vms table
CREATE OR REPLACE VIEW public.vms_with_rls AS
SELECT * FROM public.vms
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;

-- Create RLS views for proxmox_nodes table
CREATE OR REPLACE VIEW public.proxmox_nodes_with_rls AS
SELECT * FROM public.proxmox_nodes
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR owner_id = current_setting('app.current_user_id', TRUE)::INTEGER;

-- Grant permissions on views
GRANT SELECT ON public.accounts_with_rls TO acc_user;
GRANT SELECT ON public.hardware_with_rls TO acc_user;
GRANT SELECT ON public.cards_with_rls TO acc_user;
GRANT SELECT ON public.vms_with_rls TO acc_user;
GRANT SELECT ON public.proxmox_nodes_with_rls TO acc_user;

-- Test RLS with different users
DO $$
BEGIN
    -- Set RLS context for admin
    PERFORM set_rls_context(1, 'admin');

    -- Insert test data with different owners
    INSERT INTO public.accounts (
        acc_id, acc_username, acc_password, prime, lock, perm_lock, farmlabs_upload,
        acc_email_address, acc_email_password, acc_vault_address, acc_vault_password,
        acc_created_at, acc_session_start, acc_steamguard_account_name, acc_confirm_type,
        acc_device_id, acc_identity_secret, acc_revocation_code, acc_secret_1,
        acc_serial_number, acc_server_time, acc_shared_secret, acc_status,
        acc_token_gid, acc_uri, owner_id
    )
    VALUES (
        '76561199000000001', 'admin_account', 'password', FALSE, FALSE, FALSE, NULL,
        'admin@example.com', 'password', 'none://nope', 'password',
        EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW()), 'default_steamguard', 0,
        'default_device_id', 'default_identity_secret', 'default_revocation_code', 'default_secret_1',
        'default_serial_number', EXTRACT(EPOCH FROM NOW()), 'default_shared_secret', 0,
        'default_token_gid', 'default_uri', 1
    )
    ON CONFLICT (acc_id) DO NOTHING;

    -- Clear RLS context
    PERFORM clear_rls_context();

    RAISE NOTICE 'RLS setup completed successfully';
END;
$$;
