# Proposed Changes to Fix RLS Issues

## Current Issues

The main issue with the current implementation is that Row-Level Security (RLS) is not working correctly, allowing non-admin users to see accounts they don't own. This is likely due to several factors:

1. **Inconsistent Database Connection Usage**:
   - Some endpoints use the global `conn` variable instead of `get_user_db_connection`
   - This bypasses RLS and allows users to see data they shouldn't have access to

2. **RLS Policy Implementation**:
   - RLS policies may not be correctly defined or applied
   - Session variables may not be set correctly

3. **Data Ownership**:
   - Some records may not have an `owner_id` set
   - Default assignment to admin user may not be appropriate

## Proposed Changes

### 1. Database Connection Management

#### Replace Global Connection Usage

All uses of the global `conn` variable should be replaced with the appropriate context manager:

```python
# Before
cursor = conn.cursor()
try:
    cursor.execute("SELECT * FROM accounts")
    # ...
finally:
    cursor.close()

# After
with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
    cursor = user_conn.cursor()
    try:
        cursor.execute("SELECT * FROM accounts")
        # ...
    finally:
        cursor.close()
```

#### Enhance Connection Context Manager

Improve the `get_user_db_connection` context manager to better handle errors and verify RLS context:

```python
@contextmanager
def get_user_db_connection(user_id=None, user_role=None):
    conn = get_connection()
    try:
        if conn:
            if user_id is not None and user_role is not None:
                # Set session variables for RLS
                cursor = conn.cursor()
                try:
                    cursor.execute("SET app.current_user_id = %s", (str(user_id),))
                    cursor.execute("SET app.current_user_role = %s", (str(user_role),))
                    
                    # Verify session variables were set correctly
                    cursor.execute("SELECT current_setting('app.current_user_id'), current_setting('app.current_user_role')")
                    result = cursor.fetchone()
                    if result and result[0] == str(user_id) and result[1] == user_role:
                        print(f"RLS context set correctly: user_id={user_id}, role={user_role}")
                    else:
                        print(f"WARNING: RLS context not set correctly: {result}")
                finally:
                    cursor.close()
            else:
                print("WARNING: Missing user_id or user_role for RLS context")
        yield conn
    finally:
        if conn:
            return_connection(conn)
```

### 2. RLS Policy Implementation

#### Verify RLS Policies

Ensure RLS policies are correctly defined and applied:

```sql
-- Enable RLS on accounts table
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS accounts_user_policy ON public.accounts;
DROP POLICY IF EXISTS accounts_admin_policy ON public.accounts;

-- Create user policy
CREATE POLICY accounts_user_policy ON public.accounts
    FOR ALL
    TO acc_user
    USING (owner_id = current_setting('app.current_user_id')::INTEGER);

-- Create admin policy
CREATE POLICY accounts_admin_policy ON public.accounts
    FOR ALL
    TO acc_user
    USING (current_setting('app.current_user_role')::TEXT = 'admin');
```

#### Add RLS Testing

Add a function to test RLS policies:

```python
def test_rls(user_id, user_role):
    """Test RLS policies for a specific user."""
    with get_user_db_connection(user_id=user_id, user_role=user_role) as user_conn:
        cursor = user_conn.cursor()
        try:
            # Test accounts table
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE owner_id = %s", (user_id,))
            own_accounts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE owner_id != %s", (user_id,))
            other_accounts = cursor.fetchone()[0]
            
            print(f"User {user_id} ({user_role}) can see {own_accounts} of their own accounts")
            if user_role != 'admin' and other_accounts > 0:
                print(f"WARNING: RLS ISSUE - Non-admin user can see {other_accounts} accounts they don't own!")
            elif user_role == 'admin':
                print(f"Admin user can see {other_accounts} accounts owned by others (expected)")
            else:
                print("RLS working correctly: User cannot see accounts they don't own")
                
            # Test hardware table
            cursor.execute("SELECT COUNT(*) FROM hardware WHERE owner_id = %s", (user_id,))
            own_hardware = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hardware WHERE owner_id != %s", (user_id,))
            other_hardware = cursor.fetchone()[0]
            
            print(f"User {user_id} ({user_role}) can see {own_hardware} of their own hardware profiles")
            if user_role != 'admin' and other_hardware > 0:
                print(f"WARNING: RLS ISSUE - Non-admin user can see {other_hardware} hardware profiles they don't own!")
            
            # Test cards table
            cursor.execute("SELECT COUNT(*) FROM cards WHERE owner_id = %s", (user_id,))
            own_cards = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cards WHERE owner_id != %s", (user_id,))
            other_cards = cursor.fetchone()[0]
            
            print(f"User {user_id} ({user_role}) can see {own_cards} of their own cards")
            if user_role != 'admin' and other_cards > 0:
                print(f"WARNING: RLS ISSUE - Non-admin user can see {other_cards} cards they don't own!")
        finally:
            cursor.close()
```

### 3. Data Ownership

#### Fix Missing Owner IDs

Add a script to fix missing owner IDs:

```python
def fix_ownership():
    """Fix ownership for existing records."""
    with get_db_connection() as db_conn:
        cursor = db_conn.cursor()
        try:
            # Get admin user ID
            cursor.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1")
            admin_id = cursor.fetchone()[0]
            
            # Fix accounts table
            cursor.execute("UPDATE accounts SET owner_id = %s WHERE owner_id IS NULL", (admin_id,))
            accounts_updated = cursor.rowcount
            
            # Fix hardware table
            cursor.execute("UPDATE hardware SET owner_id = %s WHERE owner_id IS NULL", (admin_id,))
            hardware_updated = cursor.rowcount
            
            # Fix cards table
            cursor.execute("UPDATE cards SET owner_id = %s WHERE owner_id IS NULL", (admin_id,))
            cards_updated = cursor.rowcount
            
            db_conn.commit()
            
            print(f"Fixed ownership for {accounts_updated} accounts, {hardware_updated} hardware profiles, and {cards_updated} cards")
        except Exception as e:
            db_conn.rollback()
            print(f"Error fixing ownership: {e}")
        finally:
            cursor.close()
```

#### Add Triggers to Enforce Ownership

Add database triggers to ensure all records have an owner:

```sql
-- Trigger function to set owner_id if not provided
CREATE OR REPLACE FUNCTION set_owner_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.owner_id IS NULL THEN
        RAISE EXCEPTION 'owner_id cannot be NULL';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for accounts table
CREATE TRIGGER ensure_accounts_owner_id
BEFORE INSERT OR UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION set_owner_id();

-- Trigger for hardware table
CREATE TRIGGER ensure_hardware_owner_id
BEFORE INSERT OR UPDATE ON hardware
FOR EACH ROW
EXECUTE FUNCTION set_owner_id();

-- Trigger for cards table
CREATE TRIGGER ensure_cards_owner_id
BEFORE INSERT OR UPDATE ON cards
FOR EACH ROW
EXECUTE FUNCTION set_owner_id();
```

### 4. API Endpoint Updates

#### Update Account Endpoints

Ensure all account endpoints use the user-specific connection:

```python
@router.get("/list", response_model=AccountListResponse)
async def list_accounts(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: str = "acc_id",
    sort_order: str = "asc",
    filter_prime: Optional[bool] = None,
    filter_lock: Optional[bool] = None,
    filter_perm_lock: Optional[bool] = None,
    current_user = Depends(get_current_active_user)
):
    """Get a list of accounts with pagination, sorting, and filtering."""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()
        try:
            # ... (rest of the function)
        finally:
            cursor.close()
```

#### Update Hardware Endpoints

Ensure all hardware endpoints use the user-specific connection:

```python
@router.get("/", response_model=List[HardwareResponse])
async def list_hardware(current_user = Depends(get_current_active_user)):
    """Get a list of hardware profiles."""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()
        try:
            # ... (rest of the function)
        finally:
            cursor.close()
```

#### Update Card Endpoints

Ensure all card endpoints use the user-specific connection:

```python
@router.get("/", response_model=List[CardResponse])
async def list_cards(current_user = Depends(get_current_active_user)):
    """Get a list of cards."""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()
        try:
            # ... (rest of the function)
        finally:
            cursor.close()
```

### 5. Testing and Verification

#### Add RLS Tests

Add tests to verify RLS is working correctly:

```python
def test_rls_implementation():
    """Test RLS implementation for all tables."""
    # Test admin user
    test_rls(user_id=1, user_role='admin')
    
    # Test regular user
    test_rls(user_id=2, user_role='user')
    
    # Test another regular user
    test_rls(user_id=3, user_role='user')
```

#### Add API Tests

Add tests to verify API endpoints respect RLS:

```python
async def test_api_endpoints():
    """Test API endpoints respect RLS."""
    # Test admin user
    admin_token = create_test_token(user_id=1, user_role='admin')
    
    # Test regular user
    user_token = create_test_token(user_id=2, user_role='user')
    
    # Test accounts endpoint
    admin_accounts = await client.get("/accounts/list", headers={"Authorization": f"Bearer {admin_token}"})
    user_accounts = await client.get("/accounts/list", headers={"Authorization": f"Bearer {user_token}"})
    
    print(f"Admin can see {len(admin_accounts.json()['accounts'])} accounts")
    print(f"User can see {len(user_accounts.json()['accounts'])} accounts")
    
    # Verify user can only see their own accounts
    for account in user_accounts.json()['accounts']:
        # Get account owner
        with get_db_connection() as db_conn:
            cursor = db_conn.cursor()
            cursor.execute("SELECT owner_id FROM accounts WHERE acc_id = %s", (account['acc_id'],))
            owner_id = cursor.fetchone()[0]
            cursor.close()
        
        if owner_id != 2:
            print(f"WARNING: RLS ISSUE - User can see account {account['acc_id']} owned by user {owner_id}")
```

## Implementation Plan

1. **Phase 1: Fix Database Connection Usage**
   - Replace all uses of the global `conn` variable with context managers
   - Enhance the connection context manager to verify RLS context
   - Add RLS testing function

2. **Phase 2: Fix RLS Policy Implementation**
   - Verify RLS policies are correctly defined and applied
   - Test RLS policies for all tables

3. **Phase 3: Fix Data Ownership**
   - Fix missing owner IDs
   - Add triggers to enforce ownership

4. **Phase 4: Update API Endpoints**
   - Update all endpoints to use the user-specific connection
   - Test API endpoints respect RLS

5. **Phase 5: Testing and Verification**
   - Add comprehensive tests for RLS
   - Verify all issues are fixed
