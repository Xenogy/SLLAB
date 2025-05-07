-- Add error_count metric to metrics_definitions table if it doesn't exist

-- Check if the metric already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.metrics_definitions 
        WHERE name = 'error_count' AND category_id = (SELECT id FROM public.metrics_categories WHERE name = 'system')
    ) THEN
        -- Insert the new metric
        INSERT INTO public.metrics_definitions (category_id, name, display_name, description, unit, data_type)
        VALUES (
            (SELECT id FROM public.metrics_categories WHERE name = 'system'),
            'error_count',
            'Error Count',
            'Total number of system errors',
            'count',
            'integer'
        );
        
        -- Generate sample data for admin user
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
                -- Get metric ID
                DECLARE
                    v_metric_id INTEGER;
                BEGIN
                    SELECT id INTO v_metric_id FROM public.metrics_definitions WHERE name = 'error_count';
                    
                    -- Insert some sample data points
                    FOR i IN 0..6 LOOP
                        INSERT INTO public.timeseries_data (
                            metric_id, timestamp, value_float, entity_type, entity_id, owner_id
                        ) VALUES (
                            v_metric_id, 
                            NOW() - ((6-i) || ' days')::INTERVAL, 
                            FLOOR(RANDOM() * 10), 
                            'system', 
                            'system', 
                            admin_id
                        );
                    END LOOP;
                END;
            END IF;
            
            -- Generate sample data for regular user
            IF user_id IS NOT NULL THEN
                -- Get metric ID
                DECLARE
                    v_metric_id INTEGER;
                BEGIN
                    SELECT id INTO v_metric_id FROM public.metrics_definitions WHERE name = 'error_count';
                    
                    -- Insert some sample data points
                    FOR i IN 0..6 LOOP
                        INSERT INTO public.timeseries_data (
                            metric_id, timestamp, value_float, entity_type, entity_id, owner_id
                        ) VALUES (
                            v_metric_id, 
                            NOW() - ((6-i) || ' days')::INTERVAL, 
                            FLOOR(RANDOM() * 5), 
                            'system', 
                            'system', 
                            user_id
                        );
                    END LOOP;
                END;
            END IF;
        END $$;
        
        RAISE NOTICE 'Added error_count metric to metrics_definitions table with sample data';
    ELSE
        RAISE NOTICE 'error_count metric already exists in metrics_definitions table';
    END IF;
END $$;
