-- Table: public.cards

-- DROP TABLE IF EXISTS public.cards;

CREATE TABLE IF NOT EXISTS public.cards
(
    id serial NOT NULL,
    code1 text COLLATE pg_catalog."default" NOT NULL,
    code2 text COLLATE pg_catalog."default",
    redeemed boolean NOT NULL DEFAULT false,
    failed text COLLATE pg_catalog."default" DEFAULT ''::text,
    lock boolean NOT NULL DEFAULT false,
    perm_lock boolean NOT NULL DEFAULT false,
    CONSTRAINT cards_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.cards
    OWNER to ps_user;

GRANT ALL ON TABLE public.cards TO acc_user;

GRANT ALL ON TABLE public.cards TO ps_user;

GRANT ALL(id) ON public.cards TO acc_user;

GRANT ALL(code1) ON public.cards TO acc_user;

GRANT ALL(code2) ON public.cards TO acc_user;

GRANT ALL(redeemed) ON public.cards TO acc_user;

GRANT ALL(failed) ON public.cards TO acc_user;
