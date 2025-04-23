CREATE TABLE IF NOT EXISTS public.accounts
(
    id serial NOT NULL,                                               -- Auto-incrementing ID
    acc_id text NOT NULL PRIMARY KEY,                                 -- Account identifier (Primary Key)
    acc_username text NOT NULL,                                       -- Username for the account
    acc_password text NOT NULL,                                       -- Password for the account
    prime boolean NOT NULL DEFAULT false,                             -- Whether the account is prime
    lock boolean NOT NULL DEFAULT false,                              -- Whether the account is locked
    perm_lock boolean NOT NULL DEFAULT false,                         -- Whether the account is permanently locked
    farmlabs_upload uuid,                                             -- FarmLabs upload UUID
    acc_email_address text,                                  -- Email address associated with the account
    acc_email_password text,                                 -- Password for the email account
    acc_vault_address text NOT NULL,                                  -- Vault address for the account
    acc_vault_password text NOT NULL,                                 -- Password for the vault
    acc_created_at bigint NOT NULL,                                   -- Timestamp when the account was created
    acc_session_start bigint NOT NULL,                                -- Timestamp when the session started
    acc_steamguard_account_name text NOT NULL,                        -- Steam Guard account name
    acc_confirm_type integer NOT NULL,                                -- Confirmation type
    acc_device_id text NOT NULL,                                      -- Device identifier
    acc_identity_secret text NOT NULL,                                -- Identity secret
    acc_revocation_code text NOT NULL,                                -- Revocation code
    acc_secret_1 text NOT NULL,                                       -- Secret 1
    acc_serial_number text NOT NULL,                                  -- Serial number
    acc_server_time bigint NOT NULL,                                  -- Server time
    acc_shared_secret text NOT NULL,                                  -- Shared secret
    acc_status integer NOT NULL,                                      -- Account status
    acc_token_gid text NOT NULL,                                      -- Token GID
    acc_uri text NOT NULL                                             -- URI
);

COMMENT ON COLUMN public.accounts.id IS 'Auto-incrementing ID';
COMMENT ON COLUMN public.accounts.acc_id IS 'Account identifier (Primary Key)';
COMMENT ON COLUMN public.accounts.acc_username IS 'Username for the account';
COMMENT ON COLUMN public.accounts.acc_password IS 'Password for the account';
COMMENT ON COLUMN public.accounts.acc_email_address IS 'Email address associated with the account';
COMMENT ON COLUMN public.accounts.acc_email_password IS 'Password for the email account';
COMMENT ON COLUMN public.accounts.acc_vault_address IS 'Vault address for the account';
COMMENT ON COLUMN public.accounts.acc_vault_password IS 'Password for the vault';
COMMENT ON COLUMN public.accounts.farmlabs_upload IS 'FarmLabs upload UUID';
COMMENT ON COLUMN public.accounts.acc_created_at IS 'Timestamp when the account was created';
COMMENT ON COLUMN public.accounts.acc_session_start IS 'Timestamp when the session started';
COMMENT ON COLUMN public.accounts.acc_steamguard_account_name IS 'Steam Guard account name';
COMMENT ON COLUMN public.accounts.acc_confirm_type IS 'Confirmation type';
COMMENT ON COLUMN public.accounts.acc_device_id IS 'Device identifier';
COMMENT ON COLUMN public.accounts.acc_identity_secret IS 'Identity secret';
COMMENT ON COLUMN public.accounts.acc_revocation_code IS 'Revocation code';
COMMENT ON COLUMN public.accounts.acc_secret_1 IS 'Secret 1';
COMMENT ON COLUMN public.accounts.acc_serial_number IS 'Serial number';
COMMENT ON COLUMN public.accounts.acc_server_time IS 'Server time';
COMMENT ON COLUMN public.accounts.acc_shared_secret IS 'Shared secret';
COMMENT ON COLUMN public.accounts.acc_status IS 'Account status';
COMMENT ON COLUMN public.accounts.acc_token_gid IS 'Token GID';
COMMENT ON COLUMN public.accounts.acc_uri IS 'URI';
COMMENT ON COLUMN public.accounts.prime IS 'Whether the account is prime';
COMMENT ON COLUMN public.accounts.lock IS 'Whether the account is locked';
COMMENT ON COLUMN public.accounts.perm_lock IS 'Whether the account is permanently locked';

CREATE INDEX idx_accounts_id ON public.accounts (id);
CREATE INDEX idx_accounts_username ON public.accounts (acc_username);
CREATE INDEX idx_accounts_email ON public.accounts (acc_email_address);

ALTER TABLE IF EXISTS public.accounts
    OWNER to ps_user;

GRANT ALL ON TABLE public.accounts TO acc_user;
GRANT ALL ON TABLE public.accounts TO ps_user;
