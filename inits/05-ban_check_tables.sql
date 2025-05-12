-- Ban Check Tables
-- This script creates tables for storing ban check tasks and results

-- Create ban_check_tasks table
CREATE TABLE IF NOT EXISTS public.ban_check_tasks
(
    task_id TEXT PRIMARY KEY,                                        -- Task ID (UUID)
    status TEXT NOT NULL,                                            -- Task status (PENDING, PROCESSING, COMPLETED, FAILED)
    message TEXT,                                                    -- Task message
    progress FLOAT DEFAULT 0,                                        -- Task progress (0-100)
    results JSONB,                                                   -- Task results (JSON)
    proxy_stats JSONB,                                               -- Proxy statistics (JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    owner_id INTEGER NOT NULL REFERENCES public.users(id)            -- Owner ID (for RLS)
);

-- Create indexes for ban_check_tasks
CREATE INDEX IF NOT EXISTS idx_ban_check_tasks_owner_id ON public.ban_check_tasks(owner_id);
CREATE INDEX IF NOT EXISTS idx_ban_check_tasks_status ON public.ban_check_tasks(status);
CREATE INDEX IF NOT EXISTS idx_ban_check_tasks_created_at ON public.ban_check_tasks(created_at);

-- Grant permissions
GRANT ALL ON TABLE public.ban_check_tasks TO acc_user;
GRANT ALL ON TABLE public.ban_check_tasks TO ps_user;

-- Enable Row-Level Security
ALTER TABLE public.ban_check_tasks ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Admin policy (can see and modify all tasks)
CREATE POLICY ban_check_tasks_admin_policy ON public.ban_check_tasks
FOR ALL
TO PUBLIC
USING (current_setting('app.current_user_role', TRUE) = 'admin');

-- User SELECT policy (can only see their own tasks)
CREATE POLICY ban_check_tasks_user_select_policy ON public.ban_check_tasks
FOR SELECT
TO PUBLIC
USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- User INSERT policy (can only insert tasks they own)
CREATE POLICY ban_check_tasks_user_insert_policy ON public.ban_check_tasks
FOR INSERT
TO PUBLIC
WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- User UPDATE policy (can only update their own tasks)
CREATE POLICY ban_check_tasks_user_update_policy ON public.ban_check_tasks
FOR UPDATE
TO PUBLIC
USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- User DELETE policy (can only delete their own tasks)
CREATE POLICY ban_check_tasks_user_delete_policy ON public.ban_check_tasks
FOR DELETE
TO PUBLIC
USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Add trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_ban_check_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ban_check_tasks_updated_at
BEFORE UPDATE ON public.ban_check_tasks
FOR EACH ROW
EXECUTE FUNCTION update_ban_check_tasks_updated_at();

-- Add to logs_categories if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'logs_categories') THEN
        INSERT INTO public.logs_categories (name, description)
        VALUES ('ban_check', 'Steam ban check operations')
        ON CONFLICT (name) DO NOTHING;
    END IF;
END $$;

-- Add to logs_sources if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'logs_sources') THEN
        INSERT INTO public.logs_sources (name, description)
        VALUES ('ban_check', 'Steam ban check module')
        ON CONFLICT (name) DO NOTHING;
    END IF;
END $$;

-- Add to metrics_categories if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'metrics_categories') THEN
        INSERT INTO public.metrics_categories (name, description)
        VALUES ('ban_check', 'Steam ban check metrics')
        ON CONFLICT (name) DO NOTHING;

        -- Add metrics for ban check if the metrics_definitions table exists
        IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'metrics_definitions') THEN
            INSERT INTO public.metrics_definitions (category_id, name, display_name, description, unit, data_type)
            VALUES
                ((SELECT id FROM public.metrics_categories WHERE name = 'ban_check'),
                 'ban_check_tasks_count',
                 'Ban Check Tasks Count',
                 'Total number of ban check tasks',
                 'count',
                 'integer'),
                ((SELECT id FROM public.metrics_categories WHERE name = 'ban_check'),
                 'ban_check_banned_count',
                 'Banned Accounts Count',
                 'Number of banned Steam accounts detected',
                 'count',
                 'integer'),
                ((SELECT id FROM public.metrics_categories WHERE name = 'ban_check'),
                 'ban_check_success_rate',
                 'Ban Check Success Rate',
                 'Percentage of successful ban checks',
                 'percent',
                 'float')
            ON CONFLICT (category_id, name) DO NOTHING;
        END IF;
    END IF;
END $$;

-- Test RLS with different users (only if RLS functions exist)
DO $$
BEGIN
    -- Check if RLS functions exist
    IF EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'set_rls_context'
        AND pronargs = 2
        AND proargtypes::text LIKE '%23%text%' -- Check for integer and text arguments
    ) THEN
        -- Set RLS context for admin
        PERFORM set_rls_context(1, 'admin');

        -- Insert test data for admin
        INSERT INTO public.ban_check_tasks (
            task_id, status, message, progress, results, owner_id
        )
        VALUES (
            'test-task-admin', 'COMPLETED', 'Test task for admin', 100,
            '[{"steam_id": "76561198000000001", "status_summary": "NOT_BANNED", "details": "No bans detected"}]'::jsonb,
            1
        )
        ON CONFLICT (task_id) DO NOTHING;

        -- Clear RLS context
        PERFORM clear_rls_context();

        -- Set RLS context for regular user
        PERFORM set_rls_context(2, 'user');

        -- Insert test data for regular user
        INSERT INTO public.ban_check_tasks (
            task_id, status, message, progress, results, owner_id
        )
        VALUES (
            'test-task-user', 'COMPLETED', 'Test task for user', 100,
            '[{"steam_id": "76561198000000002", "status_summary": "BANNED", "details": "VAC ban on record"}]'::jsonb,
            2
        )
        ON CONFLICT (task_id) DO NOTHING;

        -- Clear RLS context
        PERFORM clear_rls_context();

        RAISE NOTICE 'Ban check tables setup with RLS completed successfully';
    ELSE
        -- Insert test data without RLS
        INSERT INTO public.ban_check_tasks (
            task_id, status, message, progress, results, owner_id
        )
        VALUES
            ('test-task-admin', 'COMPLETED', 'Test task for admin', 100,
             '[{"steam_id": "76561198000000001", "status_summary": "NOT_BANNED", "details": "No bans detected"}]'::jsonb,
             1),
            ('test-task-user', 'COMPLETED', 'Test task for user', 100,
             '[{"steam_id": "76561198000000002", "status_summary": "BANNED", "details": "VAC ban on record"}]'::jsonb,
             2)
        ON CONFLICT (task_id) DO NOTHING;

        RAISE NOTICE 'Ban check tables setup without RLS completed successfully (RLS functions not found)';
    END IF;
END;
$$;
