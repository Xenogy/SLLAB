-- Migration: Normalize Database Schema

-- Create a function to check if a column exists
CREATE OR REPLACE FUNCTION column_exists(p_table text, p_column text) RETURNS boolean AS $$
DECLARE
    v_exists boolean;
BEGIN
    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = p_table
        AND column_name = p_column
    ) INTO v_exists;
    
    RETURN v_exists;
END;
$$ LANGUAGE plpgsql;

-- Start a transaction
BEGIN;

-- 1. Create email_accounts table
CREATE TABLE IF NOT EXISTS public.email_accounts (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES public.users(id)
);

COMMENT ON TABLE public.email_accounts IS 'Stores email account information';
COMMENT ON COLUMN public.email_accounts.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.email_accounts.address IS 'Email address';
COMMENT ON COLUMN public.email_accounts.password IS 'Email password';
COMMENT ON COLUMN public.email_accounts.created_at IS 'When the email account was created';
COMMENT ON COLUMN public.email_accounts.updated_at IS 'When the email account was last updated';
COMMENT ON COLUMN public.email_accounts.owner_id IS 'User who owns this email account';

CREATE INDEX idx_email_accounts_address ON public.email_accounts(address);
CREATE INDEX idx_email_accounts_owner_id ON public.email_accounts(owner_id);

-- 2. Create vault_accounts table
CREATE TABLE IF NOT EXISTS public.vault_accounts (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES public.users(id)
);

COMMENT ON TABLE public.vault_accounts IS 'Stores vault account information';
COMMENT ON COLUMN public.vault_accounts.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.vault_accounts.address IS 'Vault address';
COMMENT ON COLUMN public.vault_accounts.password IS 'Vault password';
COMMENT ON COLUMN public.vault_accounts.created_at IS 'When the vault account was created';
COMMENT ON COLUMN public.vault_accounts.updated_at IS 'When the vault account was last updated';
COMMENT ON COLUMN public.vault_accounts.owner_id IS 'User who owns this vault account';

CREATE INDEX idx_vault_accounts_address ON public.vault_accounts(address);
CREATE INDEX idx_vault_accounts_owner_id ON public.vault_accounts(owner_id);

-- 3. Create steamguard_data table
CREATE TABLE IF NOT EXISTS public.steamguard_data (
    id SERIAL PRIMARY KEY,
    account_name TEXT,
    device_id TEXT,
    identity_secret TEXT,
    shared_secret TEXT,
    revocation_code TEXT,
    uri TEXT,
    token_gid TEXT,
    secret_1 TEXT,
    serial_number TEXT,
    server_time BIGINT,
    status INTEGER,
    confirm_type INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES public.users(id)
);

COMMENT ON TABLE public.steamguard_data IS 'Stores Steam Guard data';
COMMENT ON COLUMN public.steamguard_data.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.steamguard_data.account_name IS 'Steam Guard account name';
COMMENT ON COLUMN public.steamguard_data.device_id IS 'Device identifier';
COMMENT ON COLUMN public.steamguard_data.identity_secret IS 'Identity secret';
COMMENT ON COLUMN public.steamguard_data.shared_secret IS 'Shared secret';
COMMENT ON COLUMN public.steamguard_data.revocation_code IS 'Revocation code';
COMMENT ON COLUMN public.steamguard_data.uri IS 'URI';
COMMENT ON COLUMN public.steamguard_data.token_gid IS 'Token GID';
COMMENT ON COLUMN public.steamguard_data.secret_1 IS 'Secret 1';
COMMENT ON COLUMN public.steamguard_data.serial_number IS 'Serial number';
COMMENT ON COLUMN public.steamguard_data.server_time IS 'Server time';
COMMENT ON COLUMN public.steamguard_data.status IS 'Account status';
COMMENT ON COLUMN public.steamguard_data.confirm_type IS 'Confirmation type';
COMMENT ON COLUMN public.steamguard_data.created_at IS 'When the Steam Guard data was created';
COMMENT ON COLUMN public.steamguard_data.updated_at IS 'When the Steam Guard data was last updated';
COMMENT ON COLUMN public.steamguard_data.owner_id IS 'User who owns this Steam Guard data';

CREATE INDEX idx_steamguard_data_account_name ON public.steamguard_data(account_name);
CREATE INDEX idx_steamguard_data_owner_id ON public.steamguard_data(owner_id);

-- 4. Modify accounts table to add foreign keys to new tables
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS email_id INTEGER REFERENCES public.email_accounts(id);
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS vault_id INTEGER REFERENCES public.vault_accounts(id);
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS steamguard_id INTEGER REFERENCES public.steamguard_data(id);

-- 5. Migrate data from accounts table to new tables
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Migrate email data
    FOR r IN SELECT DISTINCT acc_email_address, acc_email_password, owner_id FROM public.accounts 
             WHERE acc_email_address IS NOT NULL AND acc_email_password IS NOT NULL
    LOOP
        INSERT INTO public.email_accounts (address, password, owner_id)
        VALUES (r.acc_email_address, r.acc_email_password, r.owner_id)
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Migrate vault data
    FOR r IN SELECT DISTINCT acc_vault_address, acc_vault_password, owner_id FROM public.accounts
    LOOP
        INSERT INTO public.vault_accounts (address, password, owner_id)
        VALUES (r.acc_vault_address, r.acc_vault_password, r.owner_id)
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Migrate steamguard data
    FOR r IN SELECT DISTINCT 
                acc_steamguard_account_name, 
                acc_device_id, 
                acc_identity_secret, 
                acc_shared_secret, 
                acc_revocation_code, 
                acc_uri, 
                acc_token_gid, 
                acc_secret_1, 
                acc_serial_number, 
                acc_server_time, 
                acc_status, 
                acc_confirm_type, 
                owner_id 
             FROM public.accounts
    LOOP
        INSERT INTO public.steamguard_data (
            account_name, 
            device_id, 
            identity_secret, 
            shared_secret, 
            revocation_code, 
            uri, 
            token_gid, 
            secret_1, 
            serial_number, 
            server_time, 
            status, 
            confirm_type, 
            owner_id
        )
        VALUES (
            r.acc_steamguard_account_name, 
            r.acc_device_id, 
            r.acc_identity_secret, 
            r.acc_shared_secret, 
            r.acc_revocation_code, 
            r.acc_uri, 
            r.acc_token_gid, 
            r.acc_secret_1, 
            r.acc_serial_number, 
            r.acc_server_time, 
            r.acc_status, 
            r.acc_confirm_type, 
            r.owner_id
        )
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Update accounts table with foreign keys
    FOR r IN SELECT 
                a.acc_id, 
                e.id AS email_id, 
                v.id AS vault_id, 
                s.id AS steamguard_id 
             FROM public.accounts a
             LEFT JOIN public.email_accounts e ON a.acc_email_address = e.address AND a.acc_email_password = e.password
             LEFT JOIN public.vault_accounts v ON a.acc_vault_address = v.address AND a.acc_vault_password = v.password
             LEFT JOIN public.steamguard_data s ON a.acc_steamguard_account_name = s.account_name AND a.acc_device_id = s.device_id
    LOOP
        UPDATE public.accounts
        SET email_id = r.email_id,
            vault_id = r.vault_id,
            steamguard_id = r.steamguard_id
        WHERE acc_id = r.acc_id;
    END LOOP;
END $$;

-- 6. Add check constraints to accounts table
ALTER TABLE public.accounts ADD CONSTRAINT chk_accounts_prime CHECK (prime IN (TRUE, FALSE));
ALTER TABLE public.accounts ADD CONSTRAINT chk_accounts_lock CHECK (lock IN (TRUE, FALSE));
ALTER TABLE public.accounts ADD CONSTRAINT chk_accounts_perm_lock CHECK (perm_lock IN (TRUE, FALSE));

-- 7. Add check constraints to cards table
ALTER TABLE public.cards ADD CONSTRAINT chk_cards_redeemed CHECK (redeemed IN (TRUE, FALSE));
ALTER TABLE public.cards ADD CONSTRAINT chk_cards_lock CHECK (lock IN (TRUE, FALSE));
ALTER TABLE public.cards ADD CONSTRAINT chk_cards_perm_lock CHECK (perm_lock IN (TRUE, FALSE));

-- 8. Create a new normalized accounts table
CREATE TABLE IF NOT EXISTS public.accounts_normalized (
    id SERIAL PRIMARY KEY,
    account_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email_id INTEGER REFERENCES public.email_accounts(id),
    vault_id INTEGER REFERENCES public.vault_accounts(id),
    steamguard_id INTEGER REFERENCES public.steamguard_data(id),
    created_at BIGINT NOT NULL,
    session_start BIGINT NOT NULL,
    prime BOOLEAN NOT NULL DEFAULT FALSE,
    lock BOOLEAN NOT NULL DEFAULT FALSE,
    perm_lock BOOLEAN NOT NULL DEFAULT FALSE,
    farmlabs_upload UUID,
    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES public.users(id)
);

COMMENT ON TABLE public.accounts_normalized IS 'Normalized accounts table';
COMMENT ON COLUMN public.accounts_normalized.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.accounts_normalized.account_id IS 'Account identifier';
COMMENT ON COLUMN public.accounts_normalized.username IS 'Username for the account';
COMMENT ON COLUMN public.accounts_normalized.password IS 'Password for the account';
COMMENT ON COLUMN public.accounts_normalized.email_id IS 'Foreign key to email_accounts table';
COMMENT ON COLUMN public.accounts_normalized.vault_id IS 'Foreign key to vault_accounts table';
COMMENT ON COLUMN public.accounts_normalized.steamguard_id IS 'Foreign key to steamguard_data table';
COMMENT ON COLUMN public.accounts_normalized.created_at IS 'Timestamp when the account was created';
COMMENT ON COLUMN public.accounts_normalized.session_start IS 'Timestamp when the session started';
COMMENT ON COLUMN public.accounts_normalized.prime IS 'Whether the account is prime';
COMMENT ON COLUMN public.accounts_normalized.lock IS 'Whether the account is locked';
COMMENT ON COLUMN public.accounts_normalized.perm_lock IS 'Whether the account is permanently locked';
COMMENT ON COLUMN public.accounts_normalized.farmlabs_upload IS 'FarmLabs upload UUID';
COMMENT ON COLUMN public.accounts_normalized.created_timestamp IS 'When the account record was created';
COMMENT ON COLUMN public.accounts_normalized.updated_timestamp IS 'When the account record was last updated';
COMMENT ON COLUMN public.accounts_normalized.owner_id IS 'User who owns this account';

CREATE INDEX idx_accounts_normalized_account_id ON public.accounts_normalized(account_id);
CREATE INDEX idx_accounts_normalized_username ON public.accounts_normalized(username);
CREATE INDEX idx_accounts_normalized_email_id ON public.accounts_normalized(email_id);
CREATE INDEX idx_accounts_normalized_vault_id ON public.accounts_normalized(vault_id);
CREATE INDEX idx_accounts_normalized_steamguard_id ON public.accounts_normalized(steamguard_id);
CREATE INDEX idx_accounts_normalized_owner_id ON public.accounts_normalized(owner_id);
CREATE INDEX idx_accounts_normalized_prime ON public.accounts_normalized(prime);
CREATE INDEX idx_accounts_normalized_lock ON public.accounts_normalized(lock);
CREATE INDEX idx_accounts_normalized_perm_lock ON public.accounts_normalized(perm_lock);

-- 9. Migrate data to the new accounts table
INSERT INTO public.accounts_normalized (
    account_id,
    username,
    password,
    email_id,
    vault_id,
    steamguard_id,
    created_at,
    session_start,
    prime,
    lock,
    perm_lock,
    farmlabs_upload,
    owner_id
)
SELECT
    acc_id,
    acc_username,
    acc_password,
    email_id,
    vault_id,
    steamguard_id,
    acc_created_at,
    acc_session_start,
    prime,
    lock,
    perm_lock,
    farmlabs_upload,
    owner_id
FROM public.accounts;

-- 10. Enable RLS on new tables
ALTER TABLE public.email_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vault_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.steamguard_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts_normalized ENABLE ROW LEVEL SECURITY;

-- 11. Create RLS policies for new tables
CREATE POLICY email_accounts_user_policy ON public.email_accounts
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY email_accounts_admin_policy ON public.email_accounts
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

CREATE POLICY vault_accounts_user_policy ON public.vault_accounts
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY vault_accounts_admin_policy ON public.vault_accounts
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

CREATE POLICY steamguard_data_user_policy ON public.steamguard_data
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY steamguard_data_admin_policy ON public.steamguard_data
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

CREATE POLICY accounts_normalized_user_policy ON public.accounts_normalized
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY accounts_normalized_admin_policy ON public.accounts_normalized
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- 12. Create views for RLS
CREATE OR REPLACE VIEW public.email_accounts_with_rls AS
SELECT * FROM public.email_accounts;

CREATE OR REPLACE VIEW public.vault_accounts_with_rls AS
SELECT * FROM public.vault_accounts;

CREATE OR REPLACE VIEW public.steamguard_data_with_rls AS
SELECT * FROM public.steamguard_data;

CREATE OR REPLACE VIEW public.accounts_normalized_with_rls AS
SELECT * FROM public.accounts_normalized;

-- 13. Grant permissions on new tables and views
GRANT ALL ON TABLE public.email_accounts TO acc_user;
GRANT ALL ON TABLE public.vault_accounts TO acc_user;
GRANT ALL ON TABLE public.steamguard_data TO acc_user;
GRANT ALL ON TABLE public.accounts_normalized TO acc_user;

GRANT ALL ON TABLE public.email_accounts_with_rls TO acc_user;
GRANT ALL ON TABLE public.vault_accounts_with_rls TO acc_user;
GRANT ALL ON TABLE public.steamguard_data_with_rls TO acc_user;
GRANT ALL ON TABLE public.accounts_normalized_with_rls TO acc_user;

-- 14. Create a function to update timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_timestamp = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 15. Create triggers to update timestamps
CREATE TRIGGER update_email_accounts_timestamp
BEFORE UPDATE ON public.email_accounts
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_vault_accounts_timestamp
BEFORE UPDATE ON public.vault_accounts
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_steamguard_data_timestamp
BEFORE UPDATE ON public.steamguard_data
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_accounts_normalized_timestamp
BEFORE UPDATE ON public.accounts_normalized
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Commit the transaction
COMMIT;

-- Drop the temporary function
DROP FUNCTION IF EXISTS column_exists(text, text);
