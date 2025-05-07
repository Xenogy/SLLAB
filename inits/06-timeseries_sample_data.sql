-- Sample Timeseries Data for Testing
-- This script inserts sample data into the timeseries tables

-- Function to generate sample data for a given metric
CREATE OR REPLACE FUNCTION generate_sample_timeseries_data(
    p_metric_name VARCHAR,
    p_entity_type VARCHAR,
    p_entity_id VARCHAR,
    p_days INTEGER,
    p_min_value FLOAT,
    p_max_value FLOAT,
    p_owner_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_metric_id INTEGER;
    v_current_time TIMESTAMP WITH TIME ZONE;
    v_start_time TIMESTAMP WITH TIME ZONE;
    v_value FLOAT;
    v_hour INTEGER;
    v_day_offset INTEGER;
BEGIN
    -- Get metric ID
    SELECT id INTO v_metric_id FROM public.metrics_definitions WHERE name = p_metric_name;

    IF v_metric_id IS NULL THEN
        RAISE EXCEPTION 'Metric % not found', p_metric_name;
    END IF;

    -- Set time range
    v_current_time := NOW();
    v_start_time := v_current_time - (p_days || ' days')::INTERVAL;

    -- Generate hourly data points
    FOR v_day_offset IN 0..p_days-1 LOOP
        FOR v_hour IN 0..23 LOOP
            -- Calculate timestamp
            v_current_time := v_start_time + (v_day_offset || ' days')::INTERVAL + (v_hour || ' hours')::INTERVAL;

            -- Generate random value with daily pattern
            -- Morning: lower values, Afternoon: higher values, Evening: medium values
            IF v_hour BETWEEN 0 AND 7 THEN
                -- Early morning - lower values
                v_value := p_min_value + (p_max_value - p_min_value) * 0.3 * random();
            ELSIF v_hour BETWEEN 8 AND 16 THEN
                -- Working hours - higher values
                v_value := p_min_value + (p_max_value - p_min_value) * (0.6 + 0.4 * random());
            ELSE
                -- Evening - medium values
                v_value := p_min_value + (p_max_value - p_min_value) * (0.3 + 0.4 * random());
            END IF;

            -- Add some weekly pattern (weekends have lower values)
            IF EXTRACT(DOW FROM v_current_time) IN (0, 6) THEN -- 0 = Sunday, 6 = Saturday
                v_value := v_value * 0.7;
            END IF;

            -- Insert raw data point
            INSERT INTO public.timeseries_data (
                metric_id, timestamp, value_float, entity_type, entity_id, owner_id
            ) VALUES (
                v_metric_id, v_current_time, v_value, p_entity_type, p_entity_id, p_owner_id
            );
        END LOOP;
    END LOOP;

    -- Generate hourly aggregates
    INSERT INTO public.timeseries_aggregates (
        metric_id, period_start, period_end, period_type,
        min_value, max_value, avg_value, sum_value, count_value,
        entity_type, entity_id, owner_id
    )
    SELECT
        metric_id,
        date_trunc('hour', timestamp) AS period_start,
        date_trunc('hour', timestamp) + '1 hour'::INTERVAL AS period_end,
        'hourly' AS period_type,
        MIN(value_float) AS min_value,
        MAX(value_float) AS max_value,
        AVG(value_float) AS avg_value,
        SUM(value_float) AS sum_value,
        COUNT(*) AS count_value,
        entity_type,
        entity_id,
        owner_id
    FROM
        public.timeseries_data
    WHERE
        metric_id = v_metric_id AND
        entity_type = p_entity_type AND
        entity_id = p_entity_id AND
        owner_id = p_owner_id
    GROUP BY
        metric_id, date_trunc('hour', timestamp), entity_type, entity_id, owner_id;

    -- Generate daily aggregates
    INSERT INTO public.timeseries_aggregates (
        metric_id, period_start, period_end, period_type,
        min_value, max_value, avg_value, sum_value, count_value,
        entity_type, entity_id, owner_id
    )
    SELECT
        metric_id,
        date_trunc('day', timestamp) AS period_start,
        date_trunc('day', timestamp) + '1 day'::INTERVAL AS period_end,
        'daily' AS period_type,
        MIN(value_float) AS min_value,
        MAX(value_float) AS max_value,
        AVG(value_float) AS avg_value,
        SUM(value_float) AS sum_value,
        COUNT(*) AS count_value,
        entity_type,
        entity_id,
        owner_id
    FROM
        public.timeseries_data
    WHERE
        metric_id = v_metric_id AND
        entity_type = p_entity_type AND
        entity_id = p_entity_id AND
        owner_id = p_owner_id
    GROUP BY
        metric_id, date_trunc('day', timestamp), entity_type, entity_id, owner_id;
END;
$$ LANGUAGE plpgsql;

-- Generate sample data for admin user (ID 1)
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
        -- System metrics
        PERFORM generate_sample_timeseries_data('cpu_usage', 'system', 'system', 7, 10, 90, admin_id);
        PERFORM generate_sample_timeseries_data('memory_usage', 'system', 'system', 7, 20, 80, admin_id);
        PERFORM generate_sample_timeseries_data('disk_usage', 'system', 'system', 7, 30, 70, admin_id);
        PERFORM generate_sample_timeseries_data('network_in', 'system', 'system', 7, 100, 5000, admin_id);
        PERFORM generate_sample_timeseries_data('network_out', 'system', 'system', 7, 50, 2000, admin_id);
        PERFORM generate_sample_timeseries_data('error_count', 'system', 'system', 7, 0, 10, admin_id);

        -- VM metrics
        PERFORM generate_sample_timeseries_data('vm_count', 'system', 'system', 7, 5, 15, admin_id);
        PERFORM generate_sample_timeseries_data('vm_running_count', 'system', 'system', 7, 3, 10, admin_id);
        PERFORM generate_sample_timeseries_data('vm_stopped_count', 'system', 'system', 7, 1, 5, admin_id);
        PERFORM generate_sample_timeseries_data('vm_error_count', 'system', 'system', 7, 0, 2, admin_id);

        -- Account metrics
        PERFORM generate_sample_timeseries_data('account_count', 'system', 'system', 7, 10, 20, admin_id);
        PERFORM generate_sample_timeseries_data('account_active_count', 'system', 'system', 7, 8, 18, admin_id);
        PERFORM generate_sample_timeseries_data('account_locked_count', 'system', 'system', 7, 0, 3, admin_id);

        -- Job metrics
        PERFORM generate_sample_timeseries_data('job_count', 'system', 'system', 7, 5, 15, admin_id);
        PERFORM generate_sample_timeseries_data('job_active_count', 'system', 'system', 7, 2, 8, admin_id);
        PERFORM generate_sample_timeseries_data('job_completed_count', 'system', 'system', 7, 10, 30, admin_id);
        PERFORM generate_sample_timeseries_data('job_failed_count', 'system', 'system', 7, 0, 5, admin_id);
        PERFORM generate_sample_timeseries_data('job_execution_time', 'system', 'system', 7, 30, 300, admin_id);
    END IF;

    -- Generate sample data for regular user
    IF user_id IS NOT NULL THEN
        -- System metrics
        PERFORM generate_sample_timeseries_data('cpu_usage', 'system', 'system', 7, 10, 90, user_id);
        PERFORM generate_sample_timeseries_data('memory_usage', 'system', 'system', 7, 20, 80, user_id);
        PERFORM generate_sample_timeseries_data('disk_usage', 'system', 'system', 7, 30, 70, user_id);
        PERFORM generate_sample_timeseries_data('error_count', 'system', 'system', 7, 0, 5, user_id);

        -- VM metrics
        PERFORM generate_sample_timeseries_data('vm_count', 'system', 'system', 7, 2, 5, user_id);
        PERFORM generate_sample_timeseries_data('vm_running_count', 'system', 'system', 7, 1, 3, user_id);
        PERFORM generate_sample_timeseries_data('vm_stopped_count', 'system', 'system', 7, 0, 2, user_id);
        PERFORM generate_sample_timeseries_data('vm_error_count', 'system', 'system', 7, 0, 1, user_id);
    END IF;
END $$;

-- Clean up
DROP FUNCTION IF EXISTS generate_sample_timeseries_data(VARCHAR, VARCHAR, VARCHAR, INTEGER, FLOAT, FLOAT, INTEGER);
