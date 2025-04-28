CREATE TABLE IF NOT EXISTS public.cards
(
    id serial PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    code1 text NOT NULL,                                             -- First code
    code2 text,                                                      -- Second code (optional)
    redeemed boolean NOT NULL DEFAULT false,                         -- Whether the card has been redeemed
    failed text DEFAULT ''::text,                                    -- Failure message, if any
    lock boolean NOT NULL DEFAULT false,                             -- Whether the card is locked
    perm_lock boolean NOT NULL DEFAULT false                         -- Whether the card is permanently locked
);

COMMENT ON COLUMN public.cards.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.cards.code1 IS 'First code';
COMMENT ON COLUMN public.cards.code2 IS 'Second code (optional)';
COMMENT ON COLUMN public.cards.redeemed IS 'Whether the card has been redeemed';
COMMENT ON COLUMN public.cards.failed IS 'Failure message, if any';
COMMENT ON COLUMN public.cards.lock IS 'Whether the card is locked';
COMMENT ON COLUMN public.cards.perm_lock IS 'Whether the card is permanently locked';

CREATE INDEX idx_cards_code1 ON public.cards (code1);
CREATE INDEX idx_cards_code2 ON public.cards (code2);
CREATE INDEX idx_cards_redeemed ON public.cards (redeemed);

ALTER TABLE IF EXISTS public.cards
    OWNER to ps_user;

GRANT ALL ON TABLE public.cards TO acc_user;
GRANT ALL ON TABLE public.cards TO ps_user;

-- Grant column-level permissions
GRANT ALL(id) ON public.cards TO acc_user;
GRANT ALL(code1) ON public.cards TO acc_user;
GRANT ALL(code2) ON public.cards TO acc_user;
GRANT ALL(redeemed) ON public.cards TO acc_user;
GRANT ALL(failed) ON public.cards TO acc_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE cards_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE cards_id_seq TO ps_user;
