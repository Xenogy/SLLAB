-- Migration: Add Performance Indexes
-- This migration adds indexes to improve query performance for common query patterns

-- Start a transaction
BEGIN;

-- Check if pg_trgm extension exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'
    ) THEN
        -- Create the pg_trgm extension for better text search
        CREATE EXTENSION pg_trgm;
    END IF;
END
$$;

-- Create indexes for search queries on accounts table
DO $$
BEGIN
    -- Check if the index exists before creating it
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_acc_id_trgm'
    ) THEN
        CREATE INDEX idx_accounts_acc_id_trgm ON accounts USING gin (acc_id gin_trgm_ops);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_acc_username_trgm'
    ) THEN
        CREATE INDEX idx_accounts_acc_username_trgm ON accounts USING gin (acc_username gin_trgm_ops);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_acc_email_address_trgm'
    ) THEN
        CREATE INDEX idx_accounts_acc_email_address_trgm ON accounts USING gin (acc_email_address gin_trgm_ops);
    END IF;
END
$$;

-- Create indexes for filtering on accounts table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_prime'
    ) THEN
        CREATE INDEX idx_accounts_prime ON accounts (prime);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_lock'
    ) THEN
        CREATE INDEX idx_accounts_lock ON accounts (lock);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_perm_lock'
    ) THEN
        CREATE INDEX idx_accounts_perm_lock ON accounts (perm_lock);
    END IF;

    -- Create composite index for common filter combinations
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_prime_lock_perm_lock'
    ) THEN
        CREATE INDEX idx_accounts_prime_lock_perm_lock ON accounts (prime, lock, perm_lock);
    END IF;
END
$$;

-- Create indexes for sorting on accounts table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_accounts_acc_created_at'
    ) THEN
        CREATE INDEX idx_accounts_acc_created_at ON accounts (acc_created_at);
    END IF;
END
$$;

-- Create indexes for the normalized tables if they exist
DO $$
BEGIN
    -- Check if accounts_normalized table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'accounts_normalized'
    ) THEN
        -- Create indexes for accounts_normalized table
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_accounts_normalized_username_trgm'
        ) THEN
            CREATE INDEX idx_accounts_normalized_username_trgm ON accounts_normalized USING gin (username gin_trgm_ops);
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_accounts_normalized_prime_lock_perm_lock'
        ) THEN
            CREATE INDEX idx_accounts_normalized_prime_lock_perm_lock ON accounts_normalized (prime, lock, perm_lock);
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_accounts_normalized_created_at'
        ) THEN
            CREATE INDEX idx_accounts_normalized_created_at ON accounts_normalized (created_at);
        END IF;
    END IF;

    -- Check if email_accounts table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'email_accounts'
    ) THEN
        -- Create indexes for email_accounts table
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_email_accounts_address_trgm'
        ) THEN
            CREATE INDEX idx_email_accounts_address_trgm ON email_accounts USING gin (address gin_trgm_ops);
        END IF;
    END IF;
END
$$;

-- Create function to analyze tables periodically
CREATE OR REPLACE FUNCTION analyze_tables_periodically() RETURNS VOID AS $$
BEGIN
    -- Analyze accounts table
    ANALYZE accounts;
    
    -- Analyze other tables if they exist
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'accounts_normalized'
    ) THEN
        ANALYZE accounts_normalized;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'email_accounts'
    ) THEN
        ANALYZE email_accounts;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'hardware'
    ) THEN
        ANALYZE hardware;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'cards'
    ) THEN
        ANALYZE cards;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Analyze tables now
SELECT analyze_tables_periodically();

-- Commit the transaction
COMMIT;
