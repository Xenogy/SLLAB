-- Add error_count metric to metrics_definitions table

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
        
        RAISE NOTICE 'Added error_count metric to metrics_definitions table';
    ELSE
        RAISE NOTICE 'error_count metric already exists in metrics_definitions table';
    END IF;
END $$;

-- Grant permissions
GRANT ALL ON TABLE public.metrics_definitions TO acc_user;
GRANT ALL ON TABLE public.metrics_definitions TO ps_user;
