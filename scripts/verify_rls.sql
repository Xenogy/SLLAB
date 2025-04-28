-- Script to verify Row-Level Security (RLS) is working correctly
-- Run this script as the acc_user role: psql -U acc_user -d accountdb -f verify_rls.sql

-- Test RLS with different users
DO $$
DECLARE
    user_ids INTEGER[] := ARRAY[1, 2, 3];  -- Test with user IDs 1, 2, and 3
    user_id INTEGER;
    account_count INTEGER;
BEGIN
    RAISE NOTICE '=== Row-Level Security Verification ===';
    RAISE NOTICE '';
    
    -- Test with each user
    FOREACH user_id IN ARRAY user_ids
    LOOP
        -- Set RLS context for this user with 'user' role
        PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
        PERFORM set_config('app.current_user_role', 'user', FALSE);
        
        -- Count accounts visible to this user
        EXECUTE 'SELECT COUNT(*) FROM accounts' INTO account_count;
        
        -- Output results
        RAISE NOTICE 'User ID % (role: user) can see % accounts', user_id, account_count;
        
        -- Show the actual accounts visible to this user
        RAISE NOTICE 'Accounts visible to user %:', user_id;
        FOR i IN 1..account_count LOOP
            DECLARE
                acc_record RECORD;
            BEGIN
                EXECUTE 'SELECT acc_id, acc_username, owner_id FROM accounts LIMIT 1 OFFSET ' || (i-1) INTO acc_record;
                RAISE NOTICE '  Account: %, Username: %, Owner: %', acc_record.acc_id, acc_record.acc_username, acc_record.owner_id;
            END;
        END LOOP;
        
        RAISE NOTICE '';
        
        -- Clear RLS context
        PERFORM set_config('app.current_user_id', NULL, FALSE);
        PERFORM set_config('app.current_user_role', NULL, FALSE);
    END LOOP;
    
    -- Test with admin role
    PERFORM set_config('app.current_user_id', '1', FALSE);
    PERFORM set_config('app.current_user_role', 'admin', FALSE);
    
    -- Count accounts visible to admin
    EXECUTE 'SELECT COUNT(*) FROM accounts' INTO account_count;
    
    -- Output results
    RAISE NOTICE 'User ID 1 (role: admin) can see % accounts', account_count;
    
    -- Show the actual accounts visible to admin
    RAISE NOTICE 'Accounts visible to admin:';
    FOR i IN 1..account_count LOOP
        DECLARE
            acc_record RECORD;
        BEGIN
            EXECUTE 'SELECT acc_id, acc_username, owner_id FROM accounts LIMIT 1 OFFSET ' || (i-1) INTO acc_record;
            RAISE NOTICE '  Account: %, Username: %, Owner: %', acc_record.acc_id, acc_record.acc_username, acc_record.owner_id;
        END;
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE 'RLS Verification Result:';
    
    -- Determine if RLS is working correctly
    IF account_count > 1 THEN
        RAISE NOTICE 'Admin can see all accounts: PASS';
    ELSE
        RAISE NOTICE 'Admin can see all accounts: FAIL';
    END IF;
    
    -- Clear RLS context
    PERFORM set_config('app.current_user_id', NULL, FALSE);
    PERFORM set_config('app.current_user_role', NULL, FALSE);
    
    -- Test if regular users can only see their own accounts
    DECLARE
        user_accounts_correct BOOLEAN := TRUE;
    BEGIN
        FOR user_id IN 1..3 LOOP
            PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
            PERFORM set_config('app.current_user_role', 'user', FALSE);
            
            EXECUTE 'SELECT COUNT(*) = (SELECT COUNT(*) FROM accounts WHERE owner_id = ' || user_id || ')' INTO user_accounts_correct;
            
            IF NOT user_accounts_correct THEN
                EXIT;
            END IF;
            
            PERFORM set_config('app.current_user_id', NULL, FALSE);
            PERFORM set_config('app.current_user_role', NULL, FALSE);
        END LOOP;
        
        IF user_accounts_correct THEN
            RAISE NOTICE 'Users can only see their own accounts: PASS';
        ELSE
            RAISE NOTICE 'Users can only see their own accounts: FAIL';
        END IF;
    END;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== End of Verification ===';
END;
$$;
