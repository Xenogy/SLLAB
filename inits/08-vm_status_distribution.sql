-- VM Status Distribution Data
-- This script inserts sample VM status distribution data

-- Function to generate VM status distribution data
CREATE OR REPLACE FUNCTION generate_vm_status_distribution(
    p_days INTEGER,
    p_owner_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_metric_id INTEGER;
    v_current_time TIMESTAMP WITH TIME ZONE;
    v_start_time TIMESTAMP WITH TIME ZONE;
    v_running INTEGER;
    v_stopped INTEGER;
    v_error INTEGER;
    v_hour INTEGER;
    v_day_offset INTEGER;
BEGIN
    -- Set time range
    v_current_time := NOW();
    v_start_time := v_current_time - (p_days || ' days')::INTERVAL;
    
    -- Generate hourly data points
    FOR v_day_offset IN 0..p_days-1 LOOP
        FOR v_hour IN 0..23 LOOP
            -- Calculate timestamp
            v_current_time := v_start_time + (v_day_offset || ' days')::INTERVAL + (v_hour || ' hours')::INTERVAL;
            
            -- Generate random values with daily pattern
            IF p_owner_id = (SELECT id FROM public.users WHERE username = 'admin') THEN
                -- Admin has more VMs
                v_running := 3 + floor(random() * 7);
                v_stopped := 1 + floor(random() * 4);
                v_error := floor(random() * 2);
            ELSE
                -- Regular user has fewer VMs
                v_running := 1 + floor(random() * 2);
                v_stopped := floor(random() * 2);
                v_error := floor(random() * 1);
            END IF;
            
            -- Add some weekly pattern (weekends have fewer running VMs)
            IF EXTRACT(DOW FROM v_current_time) IN (0, 6) THEN -- 0 = Sunday, 6 = Saturday
                v_running := greatest(1, floor(v_running * 0.7));
                v_stopped := v_stopped + 1;
            END IF;
            
            -- Insert data point
            INSERT INTO public.vm_status_distribution (
                timestamp, running, stopped, error, owner_id
            ) VALUES (
                v_current_time, v_running, v_stopped, v_error, p_owner_id
            );
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create VM status distribution table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.vm_status_distribution (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    running INTEGER NOT NULL DEFAULT 0,
    stopped INTEGER NOT NULL DEFAULT 0,
    error INTEGER NOT NULL DEFAULT 0,
    owner_id INTEGER REFERENCES public.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on vm_status_distribution
CREATE INDEX IF NOT EXISTS idx_vm_status_distribution_timestamp ON public.vm_status_distribution(timestamp);
CREATE INDEX IF NOT EXISTS idx_vm_status_distribution_owner_id ON public.vm_status_distribution(owner_id);

-- Enable RLS on vm_status_distribution
ALTER TABLE public.vm_status_distribution ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for vm_status_distribution
CREATE POLICY vm_status_distribution_user_policy ON public.vm_status_distribution
    USING (owner_id = current_setting('app.current_user_id')::INTEGER OR
           current_setting('app.current_user_role')::TEXT = 'admin');

-- Set ownership
ALTER TABLE public.vm_status_distribution OWNER TO ps_user;

-- Grant permissions
GRANT ALL ON TABLE public.vm_status_distribution TO acc_user;
GRANT ALL ON TABLE public.vm_status_distribution TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE vm_status_distribution_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE vm_status_distribution_id_seq TO ps_user;

-- Generate sample data
DO $$
DECLARE
    admin_id INTEGER;
    user_id INTEGER;
BEGIN
    -- Get admin user ID
    SELECT id INTO admin_id FROM public.users WHERE username = 'admin';
    
    -- Get regular user ID
    SELECT id INTO user_id FROM public.users WHERE username = 'user';
    
    -- Generate sample data for admin user
    IF admin_id IS NOT NULL THEN
        PERFORM generate_vm_status_distribution(7, admin_id);
    END IF;
    
    -- Generate sample data for regular user
    IF user_id IS NOT NULL THEN
        PERFORM generate_vm_status_distribution(7, user_id);
    END IF;
END $$;

-- Clean up
DROP FUNCTION IF EXISTS generate_vm_status_distribution(INTEGER, INTEGER);
