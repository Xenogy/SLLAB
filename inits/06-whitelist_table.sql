-- Create whitelist table for VM access control
CREATE TABLE IF NOT EXISTS public.whitelist
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    vm_id INTEGER NOT NULL REFERENCES public.vms(id),                -- VM ID
    user_id INTEGER NOT NULL REFERENCES public.users(id),            -- User ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    UNIQUE(vm_id, user_id)                                           -- Ensure each VM-user pair is unique
);

COMMENT ON COLUMN public.whitelist.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.whitelist.vm_id IS 'VM ID';
COMMENT ON COLUMN public.whitelist.user_id IS 'User ID';
COMMENT ON COLUMN public.whitelist.created_at IS 'Creation timestamp';

-- Create indexes for better performance
CREATE INDEX idx_whitelist_vm_id ON public.whitelist (vm_id);
CREATE INDEX idx_whitelist_user_id ON public.whitelist (user_id);

-- Set table ownership
ALTER TABLE IF EXISTS public.whitelist
    OWNER to ps_user;

-- Grant permissions
GRANT ALL ON TABLE public.whitelist TO acc_user;
GRANT ALL ON TABLE public.whitelist TO ps_user;

-- Grant column-level permissions
GRANT ALL(id) ON public.whitelist TO acc_user;
GRANT ALL(vm_id) ON public.whitelist TO acc_user;
GRANT ALL(user_id) ON public.whitelist TO acc_user;
GRANT ALL(created_at) ON public.whitelist TO acc_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE whitelist_id_seq TO acc_user;

-- Enable RLS on whitelist table
ALTER TABLE public.whitelist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.whitelist FORCE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS whitelist_user_policy ON public.whitelist;
DROP POLICY IF EXISTS whitelist_admin_policy ON public.whitelist;

-- Create RLS policies for whitelist table
CREATE POLICY whitelist_admin_policy ON public.whitelist
    FOR ALL
    TO PUBLIC
    USING (current_setting('app.current_user_role', TRUE) = 'admin');

CREATE POLICY whitelist_user_policy ON public.whitelist
    FOR ALL
    TO PUBLIC
    USING (user_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Create RLS view for whitelist table
CREATE OR REPLACE VIEW public.whitelist_with_rls AS
SELECT * FROM public.whitelist
WHERE
    current_setting('app.current_user_role', TRUE) = 'admin'
    OR user_id = current_setting('app.current_user_id', TRUE)::INTEGER;

-- Grant permissions on view
GRANT SELECT ON public.whitelist_with_rls TO acc_user;
