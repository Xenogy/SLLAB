-- Migration: Normalize Cards Table

-- Start a transaction
BEGIN;

-- 1. Create a new normalized cards table
CREATE TABLE IF NOT EXISTS public.cards_normalized (
    id SERIAL PRIMARY KEY,
    code1 TEXT NOT NULL,
    code2 TEXT,
    redeemed BOOLEAN NOT NULL DEFAULT FALSE,
    failed TEXT DEFAULT '',
    lock BOOLEAN NOT NULL DEFAULT FALSE,
    perm_lock BOOLEAN NOT NULL DEFAULT FALSE,
    account_id TEXT REFERENCES public.accounts_normalized(account_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES public.users(id)
);

COMMENT ON TABLE public.cards_normalized IS 'Normalized cards table';
COMMENT ON COLUMN public.cards_normalized.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.cards_normalized.code1 IS 'First code';
COMMENT ON COLUMN public.cards_normalized.code2 IS 'Second code (optional)';
COMMENT ON COLUMN public.cards_normalized.redeemed IS 'Whether the card has been redeemed';
COMMENT ON COLUMN public.cards_normalized.failed IS 'Failure message, if any';
COMMENT ON COLUMN public.cards_normalized.lock IS 'Whether the card is locked';
COMMENT ON COLUMN public.cards_normalized.perm_lock IS 'Whether the card is permanently locked';
COMMENT ON COLUMN public.cards_normalized.account_id IS 'Associated account identifier';
COMMENT ON COLUMN public.cards_normalized.created_at IS 'When the card record was created';
COMMENT ON COLUMN public.cards_normalized.updated_at IS 'When the card record was last updated';
COMMENT ON COLUMN public.cards_normalized.owner_id IS 'User who owns this card record';

-- 2. Add check constraints to the new cards table
ALTER TABLE public.cards_normalized ADD CONSTRAINT chk_cards_normalized_redeemed CHECK (redeemed IN (TRUE, FALSE));
ALTER TABLE public.cards_normalized ADD CONSTRAINT chk_cards_normalized_lock CHECK (lock IN (TRUE, FALSE));
ALTER TABLE public.cards_normalized ADD CONSTRAINT chk_cards_normalized_perm_lock CHECK (perm_lock IN (TRUE, FALSE));

-- 3. Create indexes for the new cards table
CREATE INDEX idx_cards_normalized_code1 ON public.cards_normalized(code1);
CREATE INDEX idx_cards_normalized_code2 ON public.cards_normalized(code2);
CREATE INDEX idx_cards_normalized_redeemed ON public.cards_normalized(redeemed);
CREATE INDEX idx_cards_normalized_account_id ON public.cards_normalized(account_id);
CREATE INDEX idx_cards_normalized_owner_id ON public.cards_normalized(owner_id);

-- 4. Migrate data from the old cards table to the new one
INSERT INTO public.cards_normalized (
    code1,
    code2,
    redeemed,
    failed,
    lock,
    perm_lock,
    owner_id
)
SELECT
    code1,
    code2,
    redeemed,
    failed,
    lock,
    perm_lock,
    owner_id
FROM public.cards;

-- 5. Enable RLS on the new cards table
ALTER TABLE public.cards_normalized ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policies for the new cards table
CREATE POLICY cards_normalized_user_policy ON public.cards_normalized
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY cards_normalized_admin_policy ON public.cards_normalized
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- 7. Create a view for RLS
CREATE OR REPLACE VIEW public.cards_normalized_with_rls AS
SELECT * FROM public.cards_normalized;

-- 8. Grant permissions on the new cards table and view
GRANT ALL ON TABLE public.cards_normalized TO acc_user;
GRANT ALL ON TABLE public.cards_normalized_with_rls TO acc_user;

-- 9. Create a trigger to update the timestamp
CREATE TRIGGER update_cards_normalized_timestamp
BEFORE UPDATE ON public.cards_normalized
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Commit the transaction
COMMIT;
