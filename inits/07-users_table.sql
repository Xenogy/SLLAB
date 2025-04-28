CREATE TABLE IF NOT EXISTS public.users
(
    id serial PRIMARY KEY,                                           -- Auto-incrementing ID (Primary Key)
    username text NOT NULL UNIQUE,                                   -- Username for login
    email text NOT NULL UNIQUE,                                      -- Email address
    password_hash text NOT NULL,                                     -- Hashed password
    full_name text,                                                  -- User's full name
    role text NOT NULL DEFAULT 'user',                               -- User role (admin, user, etc.)
    is_active boolean NOT NULL DEFAULT true,                         -- Whether the user is active
    created_at timestamp with time zone NOT NULL DEFAULT now(),      -- When the user was created
    last_login timestamp with time zone,                             -- Last login timestamp
    avatar_url text,                                                 -- URL to user's avatar image
    failed_login_attempts INTEGER DEFAULT 0,                         -- Number of failed login attempts
    lockout_time TIMESTAMP                                           -- Timestamp when the user was locked out
);

COMMENT ON COLUMN public.users.id IS 'Auto-incrementing ID (Primary Key)';
COMMENT ON COLUMN public.users.username IS 'Username for login';
COMMENT ON COLUMN public.users.email IS 'Email address';
COMMENT ON COLUMN public.users.password_hash IS 'Hashed password';
COMMENT ON COLUMN public.users.full_name IS 'User''s full name';
COMMENT ON COLUMN public.users.role IS 'User role (admin, user, etc.)';
COMMENT ON COLUMN public.users.is_active IS 'Whether the user is active';
COMMENT ON COLUMN public.users.created_at IS 'When the user was created';
COMMENT ON COLUMN public.users.last_login IS 'Last login timestamp';
COMMENT ON COLUMN public.users.avatar_url IS 'URL to user''s avatar image';
COMMENT ON COLUMN public.users.failed_login_attempts IS 'Number of failed login attempts';
COMMENT ON COLUMN public.users.lockout_time IS 'Timestamp when the user was locked out';

CREATE INDEX idx_users_username ON public.users (username);
CREATE INDEX idx_users_email ON public.users (email);
CREATE INDEX idx_users_role ON public.users (role);

ALTER TABLE IF EXISTS public.users
    OWNER to ps_user;

GRANT ALL ON TABLE public.users TO acc_user;
GRANT ALL ON TABLE public.users TO ps_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO acc_user;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO ps_user;

-- Create a default admin user (password: admin123)
INSERT INTO public.users (username, email, password_hash, full_name, role)
VALUES ('admin', 'admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin User', 'admin'),
       ('user', 'user@example.com', '$2b$12$3Q2R8eIAaQN0Al', 'Test User', 'user')
ON CONFLICT (username) DO NOTHING;
