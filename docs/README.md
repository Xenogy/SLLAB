# Account Management System Documentation

This directory contains documentation for the Account Management System project.

## Contents

- [Project Overview](project_overview.md): High-level overview of the project
- [Proposed Changes](proposed_changes.md): Proposed changes to fix current issues

### Architecture Documentation

- [Security Model](architecture/security_model.md): Security model and implementation
- [Database Schema](architecture/database_schema.md): Database schema and RLS implementation
- [API Architecture](architecture/api_architecture.md): API architecture and endpoints
- [Frontend Architecture](architecture/frontend_architecture.md): Frontend architecture and components

## Current Issues

The main issue with the current implementation is that Row-Level Security (RLS) is not working correctly, allowing non-admin users to see accounts they don't own. This is likely due to several factors:

1. **Inconsistent Database Connection Usage**: Some endpoints use the global `conn` variable instead of `get_user_db_connection`, bypassing RLS.
2. **RLS Policy Implementation**: RLS policies may not be correctly defined or applied.
3. **Data Ownership**: Some records may not have an `owner_id` set.

See the [Proposed Changes](proposed_changes.md) document for a detailed plan to fix these issues.

## Next Steps

1. Review the documentation to understand the current architecture and issues
2. Implement the proposed changes to fix the RLS issues
3. Test the changes to ensure RLS is working correctly
4. Update the documentation as needed
