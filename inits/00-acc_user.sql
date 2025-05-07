-- Create the acc_user role for regular account operations
CREATE ROLE acc_user WITH
  LOGIN                                                               -- Can log in
  NOSUPERUSER                                                         -- Not a superuser
  INHERIT                                                             -- Inherits privileges of roles it is a member of
  NOCREATEDB                                                          -- Cannot create databases
  NOCREATEROLE                                                        -- Cannot create roles
  REPLICATION                                                         -- Can initiate streaming replication
  NOBYPASSRLS                                                         -- Cannot bypass row-level security
  PASSWORD 'CHANGEME';                                                -- Password for the role

COMMENT ON ROLE acc_user IS 'Regular user role for account operations with limited privileges';
