# Row-Level Security (RLS) Implementation

This document explains how Row-Level Security is implemented in the AccountDB application.

## Overview

Row-Level Security (RLS) ensures that users can only access data that belongs to them. In our application:

- Regular users can only see accounts they own
- Admin users can see all accounts
- The same principles apply to hardware and cards tables

## Implementation Details

### Database Setup

RLS is set up during database initialization in `inits/09-setup_rls.sql`:

1. **RLS Context Functions**:
   - `set_rls_context(user_id, user_role)`: Sets the current user context
   - `clear_rls_context()`: Clears the current user context

2. **RLS Policies**:
   - `accounts_user_policy`: Allows users to see only their own accounts
   - `accounts_admin_policy`: Allows admin users to see all accounts
   - Similar policies for hardware and cards tables

3. **Database User Configuration**:
   - `acc_user` role is used for application connections
   - `acc_user` has `NOBYPASSRLS` flag set to ensure RLS is enforced

### Application Integration

The application sets the RLS context when a user logs in:

1. **Connection Management**:
   - `get_user_db_connection()` in `backend/db/user_connection.py` sets the RLS context
   - The context includes the user's ID and role

2. **User Authentication**:
   - After successful authentication, the user's ID and role are passed to the database connection
   - This ensures all database operations respect the user's access permissions

## Testing RLS

You can test RLS functionality with the following SQL:

```sql
-- Set context for a regular user
SELECT set_rls_context(2, 'user');

-- Query accounts (should only show user's accounts)
SELECT * FROM accounts;

-- Set context for admin
SELECT set_rls_context(1, 'admin');

-- Query accounts (should show all accounts)
SELECT * FROM accounts;

-- Clear context
SELECT clear_rls_context();
```

## Troubleshooting

If RLS is not working as expected:

1. **Check Database Connection**:
   - Ensure the application is connecting as `acc_user`, not `postgres` or `ps_user`
   - Superusers bypass RLS by default

2. **Verify RLS is Enabled**:
   ```sql
   SELECT relname, relrowsecurity, relforcerowsecurity 
   FROM pg_class 
   WHERE relname IN ('accounts', 'hardware', 'cards');
   ```

3. **Check RLS Policies**:
   ```sql
   SELECT * FROM pg_policies 
   WHERE tablename IN ('accounts', 'hardware', 'cards');
   ```

4. **Test RLS Context**:
   ```sql
   SELECT set_rls_context(1, 'user');
   SELECT current_setting('app.current_user_id', TRUE), 
          current_setting('app.current_user_role', TRUE);
   ```

## Security Considerations

- Never use superuser accounts (`postgres`, `ps_user`) for application connections
- Always clear the RLS context after use
- Regularly audit RLS policies to ensure they match business requirements
