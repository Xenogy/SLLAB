-- Create the farmlabs_jobs table
CREATE TABLE IF NOT EXISTS public.farmlabs_jobs
(
    id SERIAL PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    job_id VARCHAR(100) NOT NULL,                                    -- Unique job identifier
    vm_id VARCHAR(100),                                              -- VM ID that ran the job
    bot_account_id VARCHAR(100),                                     -- Bot account ID that ran the job
    status VARCHAR(50) NOT NULL DEFAULT 'completed',                 -- Job status (completed, failed, etc.)
    job_type VARCHAR(100) NOT NULL,                                  -- Type of job
    start_time TIMESTAMP WITH TIME ZONE,                             -- When the job started
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,                      -- When the job completed
    result_data JSONB DEFAULT '{}'::jsonb,                           -- Result data as JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Update timestamp
    owner_id INTEGER REFERENCES public.users(id)                     -- Owner ID for RLS
);

-- Add comments to the table and columns
COMMENT ON TABLE public.farmlabs_jobs IS 'FarmLabs job completion records';
COMMENT ON COLUMN public.farmlabs_jobs.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.farmlabs_jobs.job_id IS 'Unique job identifier';
COMMENT ON COLUMN public.farmlabs_jobs.vm_id IS 'VM ID that ran the job';
COMMENT ON COLUMN public.farmlabs_jobs.bot_account_id IS 'Bot account ID that ran the job';
COMMENT ON COLUMN public.farmlabs_jobs.status IS 'Job status (completed, failed, etc.)';
COMMENT ON COLUMN public.farmlabs_jobs.job_type IS 'Type of job';
COMMENT ON COLUMN public.farmlabs_jobs.start_time IS 'When the job started';
COMMENT ON COLUMN public.farmlabs_jobs.end_time IS 'When the job completed';
COMMENT ON COLUMN public.farmlabs_jobs.result_data IS 'Result data as JSON';
COMMENT ON COLUMN public.farmlabs_jobs.created_at IS 'Creation timestamp';
COMMENT ON COLUMN public.farmlabs_jobs.updated_at IS 'Update timestamp';
COMMENT ON COLUMN public.farmlabs_jobs.owner_id IS 'Owner ID for RLS';

-- Create indexes for better performance
CREATE INDEX idx_farmlabs_jobs_job_id ON public.farmlabs_jobs (job_id);
CREATE INDEX idx_farmlabs_jobs_vm_id ON public.farmlabs_jobs (vm_id);
CREATE INDEX idx_farmlabs_jobs_bot_account_id ON public.farmlabs_jobs (bot_account_id);
CREATE INDEX idx_farmlabs_jobs_status ON public.farmlabs_jobs (status);
CREATE INDEX idx_farmlabs_jobs_job_type ON public.farmlabs_jobs (job_type);
CREATE INDEX idx_farmlabs_jobs_owner_id ON public.farmlabs_jobs (owner_id);

-- Add RLS policy
ALTER TABLE public.farmlabs_jobs ENABLE ROW LEVEL SECURITY;

-- Create policy for users to see only their own jobs
CREATE POLICY farmlabs_jobs_user_policy ON public.farmlabs_jobs
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

-- Create policy for admins to see all jobs
CREATE POLICY farmlabs_jobs_admin_policy ON public.farmlabs_jobs
    USING (current_setting('app.current_user_role')::TEXT = 'admin');

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_farmlabs_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_farmlabs_jobs_updated_at
BEFORE UPDATE ON public.farmlabs_jobs
FOR EACH ROW
EXECUTE FUNCTION update_farmlabs_jobs_updated_at();
