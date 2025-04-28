-- Standardized RLS View Definitions
-- This file contains all RLS view definitions for the AccountDB project.

-- Function to create an RLS view for a table
CREATE OR REPLACE FUNCTION create_rls_view_for_table(table_name TEXT) RETURNS VOID AS $$
BEGIN
    -- Create or replace the RLS view
    EXECUTE format('
        CREATE OR REPLACE VIEW public.%I_with_rls AS
        SELECT * FROM public.%I
        WHERE
            current_setting(''app.current_user_role'', TRUE) = ''admin''
            OR owner_id = current_setting(''app.current_user_id'', TRUE)::INTEGER
    ', table_name, table_name);

    -- Grant permissions on the view
    EXECUTE format('
        GRANT SELECT ON public.%I_with_rls TO acc_user
    ', table_name);
END;
$$ LANGUAGE plpgsql;

-- Main function to create RLS views for all tables
DO $$
DECLARE
    tables TEXT[] := ARRAY['accounts', 'hardware', 'cards', 'vms'];
    table_name TEXT;
BEGIN
    -- Loop through tables and create RLS views
    FOREACH table_name IN ARRAY tables
    LOOP
        -- Check if table exists
        DECLARE
            table_exists boolean;
            table_name_var text := table_name::text;
        BEGIN
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND information_schema.tables.table_name = table_name_var
            ) INTO table_exists;

            IF table_exists THEN
                -- Create RLS view
                PERFORM create_rls_view_for_table(table_name);
            END IF;
        END;
    END LOOP;

    -- Handle special case for hardware_profiles (if it exists)
    DECLARE
        hw_table_exists boolean;
        hw_table_name text := 'hardware_profiles';
    BEGIN
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND information_schema.tables.table_name = hw_table_name
        ) INTO hw_table_exists;

        IF hw_table_exists THEN
            -- Create RLS view for hardware_profiles
            EXECUTE '
                CREATE OR REPLACE VIEW public.hardware_profiles_with_rls AS
                SELECT * FROM public.hardware_profiles
                WHERE
                    current_setting(''app.current_user_role'', TRUE) = ''admin''
                    OR owner_id = current_setting(''app.current_user_id'', TRUE)::INTEGER
            ';

            -- Grant permissions on the view
            EXECUTE '
                GRANT SELECT ON public.hardware_profiles_with_rls TO acc_user
            ';
        END IF;
    END;
END;
$$;
