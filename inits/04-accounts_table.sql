-- Table: public.accounts

-- DROP TABLE IF EXISTS public.accounts;

CREATE TABLE IF NOT EXISTS public.accounts
(
    acc_id text COLLATE pg_catalog."default" NOT NULL,
    acc_username text COLLATE pg_catalog."default" NOT NULL,
    acc_password text COLLATE pg_catalog."default" NOT NULL,
    acc_email_address text COLLATE pg_catalog."default" NOT NULL,
    acc_email_password text COLLATE pg_catalog."default" NOT NULL,
    acc_vault_address text COLLATE pg_catalog."default" NOT NULL,
    acc_vault_password text COLLATE pg_catalog."default" NOT NULL,
    acc_created_at bigint NOT NULL,
    acc_session_start bigint NOT NULL,
    acc_steamguard_account_name text COLLATE pg_catalog."default" NOT NULL,
    acc_confirm_type integer NOT NULL,
    acc_device_id text COLLATE pg_catalog."default" NOT NULL,
    acc_identity_secret text COLLATE pg_catalog."default" NOT NULL,
    acc_revocation_code text COLLATE pg_catalog."default" NOT NULL,
    acc_secret_1 text COLLATE pg_catalog."default" NOT NULL,
    acc_serial_number text COLLATE pg_catalog."default" NOT NULL,
    acc_server_time bigint NOT NULL,
    acc_shared_secret text COLLATE pg_catalog."default" NOT NULL,
    acc_status integer NOT NULL,
    acc_token_gid text COLLATE pg_catalog."default" NOT NULL,
    acc_uri text COLLATE pg_catalog."default" NOT NULL,
    id serial NOT NULL,
    prime boolean NOT NULL DEFAULT false,
    lock boolean NOT NULL DEFAULT false,
    perm_lock boolean NOT NULL DEFAULT false,
    farmlabs_upload uuid,
    CONSTRAINT accounts_pkey PRIMARY KEY (acc_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.accounts
    OWNER to ps_user;

GRANT ALL ON TABLE public.accounts TO acc_user;

GRANT ALL ON TABLE public.accounts TO ps_user;
