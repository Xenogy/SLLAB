-- Create the ps_user role for administrative operations
CREATE ROLE ps_user WITH
  LOGIN                                                               -- Can log in
  SUPERUSER                                                           -- Has superuser privileges
  INHERIT                                                             -- Inherits privileges of roles it is a member of
  CREATEDB                                                            -- Can create databases
  CREATEROLE                                                          -- Can create roles
  REPLICATION                                                         -- Can initiate streaming replication
  BYPASSRLS                                                           -- Can bypass row-level security
  PASSWORD 'BALLS123';                                                -- Password for the role

COMMENT ON ROLE ps_user IS 'Administrative user role with full privileges for system management';
