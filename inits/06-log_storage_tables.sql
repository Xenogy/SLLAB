-- Log Storage Tables
-- This script creates tables for storing logs from various sources

-- Create logs_categories table to define log categories
CREATE TABLE IF NOT EXISTS public.logs_categories
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    name VARCHAR(50) NOT NULL UNIQUE,                                -- Category name (e.g., 'system', 'application', 'security')
    description TEXT,                                                -- Category description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Update timestamp
);

-- Create logs_sources table to define log sources
CREATE TABLE IF NOT EXISTS public.logs_sources
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    name VARCHAR(100) NOT NULL UNIQUE,                               -- Source name (e.g., 'backend', 'windows_vm_agent', 'proxmox_host')
    description TEXT,                                                -- Source description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Update timestamp
);

-- Create logs_levels table to define log levels
CREATE TABLE IF NOT EXISTS public.logs_levels
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    name VARCHAR(20) NOT NULL UNIQUE,                                -- Level name (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    severity INTEGER NOT NULL,                                       -- Severity level (higher means more severe)
    color VARCHAR(20),                                               -- Color for UI display
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Update timestamp
);

-- Create logs table to store log entries
CREATE TABLE IF NOT EXISTS public.logs
(
    id BIGSERIAL PRIMARY KEY,                                        -- Auto-incrementing ID (Primary Key)
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,                     -- Timestamp of the log entry
    category_id INTEGER REFERENCES public.logs_categories(id),       -- Category ID (Foreign Key)
    source_id INTEGER REFERENCES public.logs_sources(id),            -- Source ID (Foreign Key)
    level_id INTEGER REFERENCES public.logs_levels(id),              -- Level ID (Foreign Key)
    message TEXT NOT NULL,                                           -- Log message
    details JSONB,                                                   -- Additional details in JSON format
    entity_type VARCHAR(50),                                         -- Entity type (e.g., 'vm', 'account', 'system')
    entity_id VARCHAR(100),                                          -- Entity ID (e.g., VM ID, account ID)
    user_id INTEGER,                                                 -- User ID associated with the log
    owner_id INTEGER,                                                -- Owner ID for RLS
    trace_id VARCHAR(100),                                           -- Trace ID for distributed tracing
    span_id VARCHAR(100),                                            -- Span ID for distributed tracing
    parent_span_id VARCHAR(100),                                     -- Parent Span ID for distributed tracing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Creation timestamp
);

-- Create index on logs for faster queries
CREATE INDEX idx_logs_timestamp ON public.logs(timestamp);
CREATE INDEX idx_logs_category_id ON public.logs(category_id);
CREATE INDEX idx_logs_source_id ON public.logs(source_id);
CREATE INDEX idx_logs_level_id ON public.logs(level_id);
CREATE INDEX idx_logs_entity ON public.logs(entity_type, entity_id);
CREATE INDEX idx_logs_user_id ON public.logs(user_id);
CREATE INDEX idx_logs_owner_id ON public.logs(owner_id);
CREATE INDEX idx_logs_trace_id ON public.logs(trace_id);
CREATE INDEX idx_logs_message_text ON public.logs USING gin(to_tsvector('english', message));
CREATE INDEX idx_logs_details ON public.logs USING gin(details);

-- Create logs_retention_policies table to define retention policies
CREATE TABLE IF NOT EXISTS public.logs_retention_policies
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    category_id INTEGER REFERENCES public.logs_categories(id),       -- Category ID (Foreign Key)
    source_id INTEGER REFERENCES public.logs_sources(id),            -- Source ID (Foreign Key)
    level_id INTEGER REFERENCES public.logs_levels(id),              -- Level ID (Foreign Key)
    retention_days INTEGER NOT NULL,                                 -- Retention period in days
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Update timestamp
);

-- Create RLS policies for logs
ALTER TABLE public.logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY logs_user_policy ON public.logs
    USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER OR
           current_setting('app.current_user_role', TRUE)::TEXT = 'admin');

-- Insert default log categories
INSERT INTO public.logs_categories (name, description)
VALUES
    ('system', 'System logs related to the application infrastructure'),
    ('application', 'Application logs from the backend services'),
    ('security', 'Security-related logs such as authentication and authorization'),
    ('audit', 'Audit logs for tracking user actions'),
    ('performance', 'Performance-related logs for monitoring system performance'),
    ('error', 'Error logs for tracking application errors'),
    ('vm', 'Logs related to virtual machines'),
    ('proxmox', 'Logs from Proxmox hosts'),
    ('windows_agent', 'Logs from Windows VM agents'),
    ('farmlabs', 'Logs related to FarmLabs integration')
ON CONFLICT (name) DO NOTHING;

-- Insert default log sources
INSERT INTO public.logs_sources (name, description)
VALUES
    ('backend', 'Backend API server'),
    ('frontend', 'Frontend web application'),
    ('database', 'Database operations'),
    ('proxmox_host', 'Proxmox host agent'),
    ('windows_vm_agent', 'Windows VM agent'),
    ('monitoring', 'Monitoring system'),
    ('scheduler', 'Task scheduler'),
    ('external_api', 'External API integrations')
ON CONFLICT (name) DO NOTHING;

-- Insert default log levels
INSERT INTO public.logs_levels (name, severity, color)
VALUES
    ('DEBUG', 10, '#6c757d'),    -- Gray
    ('INFO', 20, '#0d6efd'),     -- Blue
    ('WARNING', 30, '#ffc107'),  -- Yellow
    ('ERROR', 40, '#dc3545'),    -- Red
    ('CRITICAL', 50, '#7f0000')  -- Dark Red
ON CONFLICT (name) DO NOTHING;

-- Insert default retention policies
INSERT INTO public.logs_retention_policies (category_id, source_id, level_id, retention_days)
VALUES
    -- Debug logs are kept for 7 days
    ((SELECT id FROM public.logs_categories WHERE name = 'system'),
     NULL,
     (SELECT id FROM public.logs_levels WHERE name = 'DEBUG'),
     7),

    -- Info logs are kept for 30 days
    (NULL,
     NULL,
     (SELECT id FROM public.logs_levels WHERE name = 'INFO'),
     30),

    -- Warning logs are kept for 90 days
    (NULL,
     NULL,
     (SELECT id FROM public.logs_levels WHERE name = 'WARNING'),
     90),

    -- Error and Critical logs are kept for 365 days
    (NULL,
     NULL,
     (SELECT id FROM public.logs_levels WHERE name = 'ERROR'),
     365),

    (NULL,
     NULL,
     (SELECT id FROM public.logs_levels WHERE name = 'CRITICAL'),
     365),

    -- Security logs are kept for 2 years regardless of level
    ((SELECT id FROM public.logs_categories WHERE name = 'security'),
     NULL,
     NULL,
     730),

    -- Audit logs are kept for 2 years regardless of level
    ((SELECT id FROM public.logs_categories WHERE name = 'audit'),
     NULL,
     NULL,
     730)
ON CONFLICT DO NOTHING;

-- Set ownership
ALTER TABLE public.logs_categories OWNER TO ps_user;
ALTER TABLE public.logs_sources OWNER TO ps_user;
ALTER TABLE public.logs_levels OWNER TO ps_user;
ALTER TABLE public.logs OWNER TO ps_user;
ALTER TABLE public.logs_retention_policies OWNER TO ps_user;

-- Grant permissions
GRANT ALL ON TABLE public.logs_categories TO acc_user;
GRANT ALL ON TABLE public.logs_sources TO acc_user;
GRANT ALL ON TABLE public.logs_levels TO acc_user;
GRANT ALL ON TABLE public.logs TO acc_user;
GRANT ALL ON TABLE public.logs_retention_policies TO acc_user;

GRANT ALL ON TABLE public.logs_categories TO ps_user;
GRANT ALL ON TABLE public.logs_sources TO ps_user;
GRANT ALL ON TABLE public.logs_levels TO ps_user;
GRANT ALL ON TABLE public.logs TO ps_user;
GRANT ALL ON TABLE public.logs_retention_policies TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE logs_categories_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE logs_sources_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE logs_levels_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE logs_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE logs_retention_policies_id_seq TO acc_user;

GRANT USAGE, SELECT ON SEQUENCE logs_categories_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE logs_sources_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE logs_levels_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE logs_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE logs_retention_policies_id_seq TO ps_user;

-- Create function to clean up old logs based on retention policies
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    policy RECORD;
BEGIN
    -- Process each retention policy
    FOR policy IN
        SELECT
            category_id,
            source_id,
            level_id,
            retention_days
        FROM
            public.logs_retention_policies
    LOOP
        -- Build the WHERE clause based on the policy
        WITH deleted AS (
            DELETE FROM public.logs
            WHERE timestamp < (CURRENT_TIMESTAMP - (policy.retention_days || ' days')::INTERVAL)
            AND (policy.category_id IS NULL OR category_id = policy.category_id)
            AND (policy.source_id IS NULL OR source_id = policy.source_id)
            AND (policy.level_id IS NULL OR level_id = policy.level_id)
            RETURNING id
        )
        SELECT COUNT(*) INTO deleted_count FROM deleted;

        -- Add to the total count
        deleted_count := deleted_count + deleted_count;
    END LOOP;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to add a log entry
CREATE OR REPLACE FUNCTION add_log_entry(
    p_timestamp TIMESTAMP WITH TIME ZONE,
    p_category VARCHAR(50),
    p_source VARCHAR(100),
    p_level VARCHAR(20),
    p_message TEXT,
    p_details JSONB,
    p_entity_type VARCHAR(50),
    p_entity_id VARCHAR(100),
    p_user_id INTEGER,
    p_owner_id INTEGER,
    p_trace_id VARCHAR(100),
    p_span_id VARCHAR(100),
    p_parent_span_id VARCHAR(100)
)
RETURNS BIGINT AS $$
DECLARE
    v_category_id INTEGER;
    v_source_id INTEGER;
    v_level_id INTEGER;
    v_log_id BIGINT;
BEGIN
    -- Get or create category
    SELECT id INTO v_category_id FROM public.logs_categories WHERE name = p_category;
    IF v_category_id IS NULL AND p_category IS NOT NULL THEN
        INSERT INTO public.logs_categories (name) VALUES (p_category) RETURNING id INTO v_category_id;
    END IF;

    -- Get or create source
    SELECT id INTO v_source_id FROM public.logs_sources WHERE name = p_source;
    IF v_source_id IS NULL AND p_source IS NOT NULL THEN
        INSERT INTO public.logs_sources (name) VALUES (p_source) RETURNING id INTO v_source_id;
    END IF;

    -- Get level (don't create if not exists - use default)
    SELECT id INTO v_level_id FROM public.logs_levels WHERE name = p_level;
    IF v_level_id IS NULL AND p_level IS NOT NULL THEN
        -- Use INFO as default if level doesn't exist
        SELECT id INTO v_level_id FROM public.logs_levels WHERE name = 'INFO';
    END IF;

    -- Insert log entry
    INSERT INTO public.logs (
        timestamp,
        category_id,
        source_id,
        level_id,
        message,
        details,
        entity_type,
        entity_id,
        user_id,
        owner_id,
        trace_id,
        span_id,
        parent_span_id
    ) VALUES (
        COALESCE(p_timestamp, CURRENT_TIMESTAMP),
        v_category_id,
        v_source_id,
        v_level_id,
        p_message,
        p_details,
        p_entity_type,
        p_entity_id,
        p_user_id,
        p_owner_id,
        p_trace_id,
        p_span_id,
        p_parent_span_id
    ) RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- Comment on tables and columns
COMMENT ON TABLE public.logs_categories IS 'Categories for log entries';
COMMENT ON TABLE public.logs_sources IS 'Sources of log entries';
COMMENT ON TABLE public.logs_levels IS 'Severity levels for log entries';
COMMENT ON TABLE public.logs IS 'Log entries from various sources';
COMMENT ON TABLE public.logs_retention_policies IS 'Retention policies for log entries';

COMMENT ON FUNCTION cleanup_old_logs() IS 'Function to clean up old logs based on retention policies';
COMMENT ON FUNCTION add_log_entry(
    TIMESTAMP WITH TIME ZONE,
    VARCHAR(50),
    VARCHAR(100),
    VARCHAR(20),
    TEXT,
    JSONB,
    VARCHAR(50),
    VARCHAR(100),
    INTEGER,
    INTEGER,
    VARCHAR(100),
    VARCHAR(100),
    VARCHAR(100)
) IS 'Function to add a log entry with automatic category, source, and level resolution';
