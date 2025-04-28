-- Add owner_id column to accounts table
ALTER TABLE public.accounts
ADD COLUMN owner_id INTEGER REFERENCES public.users(id);

-- Set all existing accounts to be owned by the admin user (id=1)
UPDATE public.accounts SET owner_id = 1;

-- Make owner_id NOT NULL after setting default values
ALTER TABLE public.accounts ALTER COLUMN owner_id SET NOT NULL;

-- Add index for performance
CREATE INDEX idx_accounts_owner_id ON public.accounts(owner_id);

-- Add owner_id column to hardware table
ALTER TABLE public.hardware
ADD COLUMN owner_id INTEGER REFERENCES public.users(id);

-- Set all existing hardware records to be owned by the admin user (id=1)
UPDATE public.hardware SET owner_id = 1;

-- Make owner_id NOT NULL after setting default values
ALTER TABLE public.hardware ALTER COLUMN owner_id SET NOT NULL;

-- Add index for performance
CREATE INDEX idx_hardware_owner_id ON public.hardware(owner_id);

-- Add owner_id column to cards table
ALTER TABLE public.cards
ADD COLUMN owner_id INTEGER REFERENCES public.users(id);

-- Set all existing cards to be owned by the admin user (id=1)
UPDATE public.cards SET owner_id = 1;

-- Make owner_id NOT NULL after setting default values
ALTER TABLE public.cards ALTER COLUMN owner_id SET NOT NULL;

-- Add index for performance
CREATE INDEX idx_cards_owner_id ON public.cards(owner_id);

-- Enable Row Level Security on tables
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hardware ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cards ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for accounts table
CREATE POLICY accounts_user_policy ON public.accounts
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY accounts_admin_policy ON public.accounts
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- Create RLS policies for hardware table
CREATE POLICY hardware_user_policy ON public.hardware
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY hardware_admin_policy ON public.hardware
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- Create RLS policies for cards table
CREATE POLICY cards_user_policy ON public.cards
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

CREATE POLICY cards_admin_policy ON public.cards
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- Grant permissions
GRANT ALL ON TABLE public.accounts TO acc_user;
GRANT ALL ON TABLE public.hardware TO acc_user;
GRANT ALL ON TABLE public.cards TO acc_user;
