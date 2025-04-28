-- Fix permissions for acc_user

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO acc_user;

-- Grant create on public schema
GRANT CREATE ON SCHEMA public TO acc_user;

-- Grant execute on all functions in public schema
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO acc_user;

-- Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO acc_user;

-- Grant all privileges on all sequences in public schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO acc_user;

-- Grant all privileges on schema public
GRANT ALL PRIVILEGES ON SCHEMA public TO acc_user;

-- Make acc_user the owner of the RLS functions
ALTER FUNCTION set_rls_context(integer, text) OWNER TO acc_user;
ALTER FUNCTION clear_rls_context() OWNER TO acc_user;

-- Test if acc_user can now use the RLS functions
SET ROLE acc_user;
SELECT set_rls_context(1, 'user');
SELECT clear_rls_context();
RESET ROLE;

-- Verify permissions
SELECT 
    n.nspname as schema,
    c.relname as name,
    CASE c.relkind 
        WHEN 'r' THEN 'table'
        WHEN 'v' THEN 'view'
        WHEN 'm' THEN 'materialized view'
        WHEN 'i' THEN 'index'
        WHEN 'S' THEN 'sequence'
        WHEN 's' THEN 'special'
        WHEN 'f' THEN 'foreign table'
        WHEN 'p' THEN 'partitioned table'
        WHEN 'I' THEN 'partitioned index'
    END as type,
    pg_catalog.array_to_string(c.relacl, E'\n') as access_privileges
FROM 
    pg_catalog.pg_class c
    LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE 
    c.relkind IN ('r', 'v', 'm', 'S', 'f', 'p')
    AND n.nspname = 'public'
ORDER BY 
    1, 2;
