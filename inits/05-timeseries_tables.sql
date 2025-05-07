-- Timeseries Tables for Performance Metrics
-- This script creates tables for storing timeseries data for various metrics

-- Create metrics_categories table to define metric categories
CREATE TABLE IF NOT EXISTS public.metrics_categories
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    name VARCHAR(50) NOT NULL UNIQUE,                                -- Category name (e.g., 'system', 'vm', 'account')
    description TEXT,                                                -- Category description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Update timestamp
);

-- Create metrics_definitions table to define available metrics
CREATE TABLE IF NOT EXISTS public.metrics_definitions
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    category_id INTEGER REFERENCES public.metrics_categories(id),    -- Category ID (Foreign Key)
    name VARCHAR(100) NOT NULL,                                      -- Metric name (e.g., 'cpu_usage', 'memory_usage')
    display_name VARCHAR(100) NOT NULL,                              -- Display name for the metric
    description TEXT,                                                -- Metric description
    unit VARCHAR(20),                                                -- Unit of measurement (e.g., '%', 'MB', 'count')
    data_type VARCHAR(20) NOT NULL DEFAULT 'float',                  -- Data type (float, integer, boolean, string)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,                         -- Whether the metric is active
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    UNIQUE(category_id, name)                                        -- Ensure metric names are unique within a category
);

-- Create timeseries_data table to store metric values
CREATE TABLE IF NOT EXISTS public.timeseries_data
(
    id BIGSERIAL PRIMARY KEY,                                        -- Auto-incrementing ID (Primary Key)
    metric_id INTEGER NOT NULL REFERENCES public.metrics_definitions(id), -- Metric ID (Foreign Key)
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,                     -- Timestamp of the measurement
    value_float DOUBLE PRECISION,                                    -- Float value (for float metrics)
    value_int BIGINT,                                                -- Integer value (for integer metrics)
    value_bool BOOLEAN,                                              -- Boolean value (for boolean metrics)
    value_text TEXT,                                                 -- Text value (for string metrics)
    entity_type VARCHAR(50),                                         -- Entity type (e.g., 'vm', 'account', 'system')
    entity_id VARCHAR(100),                                          -- Entity ID (e.g., VM ID, account ID)
    owner_id INTEGER,                                                -- Owner ID for RLS
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Creation timestamp
);

-- Create index on timeseries_data for faster queries
CREATE INDEX idx_timeseries_data_metric_id ON public.timeseries_data(metric_id);
CREATE INDEX idx_timeseries_data_timestamp ON public.timeseries_data(timestamp);
CREATE INDEX idx_timeseries_data_entity ON public.timeseries_data(entity_type, entity_id);
CREATE INDEX idx_timeseries_data_owner_id ON public.timeseries_data(owner_id);

-- Create timeseries_aggregates table for pre-calculated aggregates
CREATE TABLE IF NOT EXISTS public.timeseries_aggregates
(
    id BIGSERIAL PRIMARY KEY,                                        -- Auto-incrementing ID (Primary Key)
    metric_id INTEGER NOT NULL REFERENCES public.metrics_definitions(id), -- Metric ID (Foreign Key)
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,                  -- Start of the aggregation period
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,                    -- End of the aggregation period
    period_type VARCHAR(20) NOT NULL,                                -- Aggregation period type (hourly, daily, weekly, monthly)
    min_value DOUBLE PRECISION,                                      -- Minimum value during the period
    max_value DOUBLE PRECISION,                                      -- Maximum value during the period
    avg_value DOUBLE PRECISION,                                      -- Average value during the period
    sum_value DOUBLE PRECISION,                                      -- Sum of values during the period
    count_value INTEGER,                                             -- Count of values during the period
    entity_type VARCHAR(50),                                         -- Entity type (e.g., 'vm', 'account', 'system')
    entity_id VARCHAR(100),                                          -- Entity ID (e.g., VM ID, account ID)
    owner_id INTEGER,                                                -- Owner ID for RLS
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP    -- Creation timestamp
);

-- Create index on timeseries_aggregates for faster queries
CREATE INDEX idx_timeseries_aggregates_metric_id ON public.timeseries_aggregates(metric_id);
CREATE INDEX idx_timeseries_aggregates_period ON public.timeseries_aggregates(period_type, period_start, period_end);
CREATE INDEX idx_timeseries_aggregates_entity ON public.timeseries_aggregates(entity_type, entity_id);
CREATE INDEX idx_timeseries_aggregates_owner_id ON public.timeseries_aggregates(owner_id);

-- Create RLS policies for timeseries_data
ALTER TABLE public.timeseries_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY timeseries_data_user_policy ON public.timeseries_data
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR
           current_setting('app.current_user_role')::TEXT = 'admin');

-- Create RLS policies for timeseries_aggregates
ALTER TABLE public.timeseries_aggregates ENABLE ROW LEVEL SECURITY;

CREATE POLICY timeseries_aggregates_user_policy ON public.timeseries_aggregates
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR
           current_setting('app.current_user_role')::TEXT = 'admin');

-- Insert default metric categories
INSERT INTO public.metrics_categories (name, description)
VALUES
    ('system', 'System-wide metrics like CPU, memory, and disk usage'),
    ('vm', 'Virtual machine metrics like status, CPU, and memory usage'),
    ('account', 'Account metrics like status and activity'),
    ('job', 'Job metrics like execution time and status')
ON CONFLICT (name) DO NOTHING;

-- Insert default metric definitions
INSERT INTO public.metrics_definitions (category_id, name, display_name, description, unit, data_type)
VALUES
    -- System metrics
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'cpu_usage', 'CPU Usage', 'System CPU usage percentage', '%', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'memory_usage', 'Memory Usage', 'System memory usage percentage', '%', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'disk_usage', 'Disk Usage', 'System disk usage percentage', '%', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'network_in', 'Network In', 'Network incoming traffic', 'KB/s', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'network_out', 'Network Out', 'Network outgoing traffic', 'KB/s', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'active_connections', 'Active Connections', 'Number of active database connections', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'system'), 'error_count', 'Error Count', 'Total number of system errors', 'count', 'integer'),

    -- VM metrics
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_count', 'VM Count', 'Total number of VMs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_running_count', 'Running VMs', 'Number of running VMs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_stopped_count', 'Stopped VMs', 'Number of stopped VMs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_error_count', 'Error VMs', 'Number of VMs in error state', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_cpu_usage', 'VM CPU Usage', 'VM CPU usage percentage', '%', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_memory_usage', 'VM Memory Usage', 'VM memory usage percentage', '%', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_disk_usage', 'VM Disk Usage', 'VM disk usage percentage', '%', 'float'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'vm'), 'vm_uptime', 'VM Uptime', 'VM uptime in seconds', 'seconds', 'integer'),

    -- Account metrics
    ((SELECT id FROM public.metrics_categories WHERE name = 'account'), 'account_count', 'Account Count', 'Total number of accounts', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'account'), 'account_active_count', 'Active Accounts', 'Number of active accounts', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'account'), 'account_locked_count', 'Locked Accounts', 'Number of locked accounts', 'count', 'integer'),

    -- Job metrics
    ((SELECT id FROM public.metrics_categories WHERE name = 'job'), 'job_count', 'Job Count', 'Total number of jobs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'job'), 'job_active_count', 'Active Jobs', 'Number of active jobs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'job'), 'job_completed_count', 'Completed Jobs', 'Number of completed jobs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'job'), 'job_failed_count', 'Failed Jobs', 'Number of failed jobs', 'count', 'integer'),
    ((SELECT id FROM public.metrics_categories WHERE name = 'job'), 'job_execution_time', 'Job Execution Time', 'Job execution time in seconds', 'seconds', 'float')
ON CONFLICT (category_id, name) DO NOTHING;

-- Set ownership
ALTER TABLE public.metrics_categories OWNER TO ps_user;
ALTER TABLE public.metrics_definitions OWNER TO ps_user;
ALTER TABLE public.timeseries_data OWNER TO ps_user;
ALTER TABLE public.timeseries_aggregates OWNER TO ps_user;

-- Grant permissions
GRANT ALL ON TABLE public.metrics_categories TO acc_user;
GRANT ALL ON TABLE public.metrics_definitions TO acc_user;
GRANT ALL ON TABLE public.timeseries_data TO acc_user;
GRANT ALL ON TABLE public.timeseries_aggregates TO acc_user;

GRANT ALL ON TABLE public.metrics_categories TO ps_user;
GRANT ALL ON TABLE public.metrics_definitions TO ps_user;
GRANT ALL ON TABLE public.timeseries_data TO ps_user;
GRANT ALL ON TABLE public.timeseries_aggregates TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE metrics_categories_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE metrics_definitions_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE timeseries_data_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE timeseries_aggregates_id_seq TO acc_user;

GRANT USAGE, SELECT ON SEQUENCE metrics_categories_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE metrics_definitions_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE timeseries_data_id_seq TO ps_user;
GRANT USAGE, SELECT ON SEQUENCE timeseries_aggregates_id_seq TO ps_user;
