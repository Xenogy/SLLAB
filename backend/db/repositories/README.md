# Repository Pattern for Database Access

This directory contains repository classes for database access with Row-Level Security (RLS) support. Each repository class provides methods for accessing a specific entity in the database.

## Repository Structure

- `__init__.py`: Package initialization file
- `base.py`: Base repository class that extends DatabaseAccess
- `accounts.py`: Repository for account data
- `hardware.py`: Repository for hardware data
- `vms.py`: Repository for VM data
- `proxmox_nodes.py`: Repository for Proxmox node data
- `users.py`: Repository for user data

## Using Repositories

### Creating a Repository Instance

```python
from db.repositories.accounts import AccountRepository

# Create a repository instance without RLS context
account_repo = AccountRepository()

# Create a repository instance with RLS context
account_repo = AccountRepository(user_id=1, user_role="admin")
```

### Using Repository Methods

```python
# Get all accounts
accounts = account_repo.get_accounts()

# Get an account by ID
account = account_repo.get_account_by_id("acc123")

# Create a new account
account_data = {
    "acc_id": "acc123",
    "acc_username": "user123",
    "acc_password": "password123",
    "acc_email_address": "user@example.com",
    "acc_email_password": "email_password123",
    "owner_id": 1
}
account = account_repo.create_account(account_data)

# Update an account
update_data = {
    "acc_username": "new_username"
}
updated_account = account_repo.update_account("acc123", update_data)

# Delete an account
success = account_repo.delete_account("acc123")
```

## Row-Level Security (RLS)

The repository pattern ensures that Row-Level Security (RLS) is applied to all database operations. When a repository instance is created with a user_id and user_role, all database operations will be performed with that user's context.

This means that users can only see and modify data that they have access to, based on the RLS policies defined in the database.

## Adding a New Repository

To add a new repository for a new entity:

1. Create a new file in the repositories directory (e.g., `new_entity.py`)
2. Define a new repository class that extends BaseRepository
3. Set the table_name, id_column, default_columns, and default_order_by attributes
4. Implement entity-specific methods

Example:

```python
from typing import Optional, Dict, Any, List, Tuple, Union
from .base import BaseRepository

class NewEntityRepository(BaseRepository):
    """Repository for new entity data."""
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """Initialize the NewEntityRepository instance."""
        super().__init__(user_id, user_role)
        self.table_name = "new_entities"
        self.id_column = "id"
        self.default_columns = "id, name, description, owner_id, created_at, updated_at"
        self.default_order_by = "id DESC"
        self.search_columns = ["name", "description"]
    
    def get_entities(self, limit: int = 10, offset: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        """Get a list of entities with pagination and filtering."""
        # Implementation
        pass
    
    def get_entity_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific entity by ID."""
        return self.get_by_id(entity_id)
    
    # Add more entity-specific methods
```

## Best Practices

1. **Use RLS Context**: Always create repository instances with user_id and user_role when accessing user-specific data.
2. **Use Specific Methods**: Use entity-specific methods instead of generic methods when possible.
3. **Handle Errors**: Handle errors gracefully and provide meaningful error messages.
4. **Use Transactions**: Use transactions for operations that involve multiple database operations.
5. **Validate Input**: Validate input data before performing database operations.
6. **Use Pagination**: Use pagination for methods that return multiple entities.
7. **Use Search**: Use search functionality for methods that return multiple entities.
