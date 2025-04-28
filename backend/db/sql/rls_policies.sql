-- Consolidated RLS Policy Definitions
-- This file contains all RLS policy definitions for the AccountDB project.

-- Function to check if a table exists
CREATE OR REPLACE FUNCTION table_exists(p_table_name TEXT) RETURNS BOOLEAN AS $$
BEGIN
    DECLARE
        table_name_var text := p_table_name;
    BEGIN
        RETURN EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND information_schema.tables.table_name = table_name_var
        );
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to check if a column exists in a table
CREATE OR REPLACE FUNCTION column_exists(p_table_name TEXT, p_column_name TEXT) RETURNS BOOLEAN AS $$
BEGIN
    DECLARE
        table_name_var text := p_table_name;
        column_name_var text := p_column_name;
    BEGIN
        RETURN EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND information_schema.columns.table_name = table_name_var
            AND information_schema.columns.column_name = column_name_var
        );
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to set RLS context
CREATE OR REPLACE FUNCTION set_rls_context(user_id INTEGER, user_role TEXT) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
    PERFORM set_config('app.current_user_role', user_role, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to enable RLS on a table
CREATE OR REPLACE FUNCTION enable_rls_on_table(table_name TEXT) RETURNS VOID AS $$
BEGIN
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', table_name);
END;
$$ LANGUAGE plpgsql;

-- Function to create RLS policies for a table
CREATE OR REPLACE FUNCTION create_rls_policies_for_table(table_name TEXT) RETURNS VOID AS $$
BEGIN
    -- Drop existing policies if they exist
    EXECUTE format('DROP POLICY IF EXISTS %I_user_policy ON public.%I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I_admin_policy ON public.%I', table_name, table_name);

    -- Create admin policy
    EXECUTE format('
        CREATE POLICY %I_admin_policy ON public.%I
            FOR ALL
            TO PUBLIC
            USING (current_setting(''app.current_user_role'', TRUE) = ''admin'')
    ', table_name, table_name);

    -- Create user policy
    EXECUTE format('
        CREATE POLICY %I_user_policy ON public.%I
            FOR ALL
            TO PUBLIC
            USING (owner_id = current_setting(''app.current_user_id'', TRUE)::INTEGER)
    ', table_name, table_name);
END;
$$ LANGUAGE plpgsql;

-- Main function to apply RLS to all tables
DO $$
DECLARE
    tables TEXT[] := ARRAY['accounts', 'hardware', 'cards', 'vms'];
    table_name TEXT;
BEGIN
    -- Create app schema if it doesn't exist
    CREATE SCHEMA IF NOT EXISTS app;

    -- Set default values for RLS context
    PERFORM set_config('app.current_user_id', '0', FALSE);
    PERFORM set_config('app.current_user_role', 'none', FALSE);

    -- Loop through tables and apply RLS
    FOREACH table_name IN ARRAY tables
    LOOP
        -- Check if table exists
        IF table_exists(table_name) THEN
            -- Check if owner_id column exists
            IF NOT column_exists(table_name, 'owner_id') THEN
                -- Add owner_id column
                EXECUTE format('
                    ALTER TABLE public.%I
                    ADD COLUMN owner_id INTEGER REFERENCES public.users(id)
                ', table_name);

                -- Set default owner_id for existing records
                EXECUTE format('
                    UPDATE public.%I SET owner_id = 1 WHERE owner_id IS NULL
                ', table_name);

                -- Make owner_id NOT NULL
                EXECUTE format('
                    ALTER TABLE public.%I ALTER COLUMN owner_id SET NOT NULL
                ', table_name);

                -- Add index for performance
                EXECUTE format('
                    CREATE INDEX IF NOT EXISTS idx_%I_owner_id ON public.%I(owner_id)
                ', table_name, table_name);
            END IF;

            -- Enable RLS on table
            PERFORM enable_rls_on_table(table_name);

            -- Create RLS policies
            PERFORM create_rls_policies_for_table(table_name);

            -- Grant permissions
            EXECUTE format('
                GRANT ALL ON TABLE public.%I TO acc_user
            ', table_name);
        END IF;
    END LOOP;
END;
$$;
