-- Check database connection settings

-- 1. Check database users and their roles
SELECT 
    r.rolname, 
    r.rolsuper,
    r.rolinherit,
    r.rolcreaterole,
    r.rolcreatedb,
    r.rolcanlogin,
    r.rolreplication,
    r.rolbypassrls
FROM 
    pg_roles r
WHERE 
    r.rolname IN ('postgres', 'acc_user', 'ps_user')
ORDER BY 
    r.rolname;

-- 2. Check if RLS bypass is enabled for the current session
SELECT 
    current_setting('session_authorization') AS session_user,
    current_setting('role') AS current_role,
    current_setting('app.current_user_id', TRUE) AS app_user_id,
    current_setting('app.current_user_role', TRUE) AS app_user_role;

-- 3. Test RLS with different database users
DO $$
BEGIN
    -- Test with acc_user
    EXECUTE 'SET ROLE acc_user';
    RAISE NOTICE 'Testing as acc_user:';
    
    -- Set RLS context for user 1
    PERFORM set_config('app.current_user_id', '1', FALSE);
    PERFORM set_config('app.current_user_role', 'user', FALSE);
    
    -- Check what accounts are visible
    DECLARE
        account_count INTEGER;
    BEGIN
        EXECUTE 'SELECT COUNT(*) FROM accounts' INTO account_count;
        RAISE NOTICE '  User 1 can see % accounts', account_count;
    END;
    
    -- Reset to postgres
    EXECUTE 'RESET ROLE';
END;
$$;

-- 4. Check if the RLS policies are being bypassed
DO $$
BEGIN
    -- Test with acc_user (should respect RLS)
    EXECUTE 'SET ROLE acc_user';
    RAISE NOTICE 'Testing as acc_user (should respect RLS):';
    
    -- Set RLS context for user 1
    PERFORM set_config('app.current_user_id', '1', FALSE);
    PERFORM set_config('app.current_user_role', 'user', FALSE);
    
    -- Check what accounts are visible
    DECLARE
        account_count INTEGER;
        expected_count INTEGER;
    BEGIN
        EXECUTE 'SELECT COUNT(*) FROM accounts' INTO account_count;
        EXECUTE 'SELECT COUNT(*) FROM accounts WHERE owner_id = 1' INTO expected_count;
        RAISE NOTICE '  User 1 can see % accounts (expected: %)', account_count, expected_count;
        RAISE NOTICE '  RLS working correctly: %', CASE WHEN account_count = expected_count THEN 'YES' ELSE 'NO' END;
    END;
    
    -- Reset to postgres
    EXECUTE 'RESET ROLE';
    
    -- Test with postgres (should bypass RLS)
    RAISE NOTICE 'Testing as postgres (should bypass RLS):';
    
    -- Set RLS context for user 1
    PERFORM set_config('app.current_user_id', '1', FALSE);
    PERFORM set_config('app.current_user_role', 'user', FALSE);
    
    -- Check what accounts are visible
    DECLARE
        account_count INTEGER;
        expected_count INTEGER;
    BEGIN
        EXECUTE 'SELECT COUNT(*) FROM accounts' INTO account_count;
        EXECUTE 'SELECT COUNT(*) FROM accounts WHERE owner_id = 1' INTO expected_count;
        RAISE NOTICE '  User 1 can see % accounts (expected to bypass: %)', account_count, expected_count;
        RAISE NOTICE '  RLS bypassed correctly: %', CASE WHEN account_count > expected_count THEN 'YES' ELSE 'NO' END;
    END;
END;
$$;

-- 5. Fix the issue by forcing RLS for acc_user
DO $$
BEGIN
    -- Make sure acc_user cannot bypass RLS
    EXECUTE 'ALTER ROLE acc_user NOBYPASSRLS';
    RAISE NOTICE 'Set acc_user to NOBYPASSRLS';
    
    -- Test again with acc_user
    EXECUTE 'SET ROLE acc_user';
    RAISE NOTICE 'Testing as acc_user after NOBYPASSRLS:';
    
    -- Set RLS context for user 1
    PERFORM set_config('app.current_user_id', '1', FALSE);
    PERFORM set_config('app.current_user_role', 'user', FALSE);
    
    -- Check what accounts are visible
    DECLARE
        account_count INTEGER;
        expected_count INTEGER;
    BEGIN
        EXECUTE 'SELECT COUNT(*) FROM accounts' INTO account_count;
        EXECUTE 'SELECT COUNT(*) FROM accounts WHERE owner_id = 1' INTO expected_count;
        RAISE NOTICE '  User 1 can see % accounts (expected: %)', account_count, expected_count;
        RAISE NOTICE '  RLS working correctly: %', CASE WHEN account_count = expected_count THEN 'YES' ELSE 'NO' END;
    END;
    
    -- Reset to postgres
    EXECUTE 'RESET ROLE';
END;
$$;
