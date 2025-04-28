# AccountDB Coding Standards

## Introduction

This document outlines the coding standards for the AccountDB project. Following these standards ensures that the codebase remains consistent, maintainable, and high-quality. All contributors are expected to adhere to these standards.

## Table of Contents

1. [Python Code Style](#python-code-style)
2. [SQL Code Style](#sql-code-style)
3. [Type Hints](#type-hints)
4. [Docstrings](#docstrings)
5. [Imports](#imports)
6. [Error Handling](#error-handling)
7. [Logging](#logging)
8. [Testing](#testing)
9. [Security](#security)
10. [Performance](#performance)
11. [Code Organization](#code-organization)
12. [Naming Conventions](#naming-conventions)
13. [Comments](#comments)
14. [Version Control](#version-control)
15. [Tools and Enforcement](#tools-and-enforcement)

## Python Code Style

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code, with a few modifications:

### Line Length

- Maximum line length is 88 characters (Black's default).
- Exception: URLs, paths, and long strings can exceed this limit.

### Indentation

- Use 4 spaces for indentation.
- Do not use tabs.

### Whitespace

- Use whitespace to improve readability.
- No trailing whitespace.
- Surround operators with a single space on each side.
- No space between a function name and the opening parenthesis.
- One space after commas in lists, dictionaries, function calls, etc.

### Quotes

- Use double quotes for strings that contain single quotes.
- Use single quotes for strings that contain double quotes.
- Use triple double quotes for docstrings.

### Blank Lines

- Two blank lines before top-level class and function definitions.
- One blank line before method definitions inside a class.
- Use blank lines to separate logical sections of code.

### Example

```python
def calculate_total(items: List[Dict[str, Any]]) -> float:
    """
    Calculate the total price of all items.
    
    Args:
        items: List of items with price information
        
    Returns:
        The total price
    """
    total = 0.0
    
    for item in items:
        price = item.get("price", 0.0)
        quantity = item.get("quantity", 1)
        total += price * quantity
    
    return total
```

## SQL Code Style

### Keywords

- Use UPPER CASE for SQL keywords.
- Example: `SELECT`, `FROM`, `WHERE`, `JOIN`, `AND`, `OR`, etc.

### Identifiers

- Use snake_case for table and column names.
- Use meaningful names for tables and columns.

### Indentation

- Use 4 spaces for indentation.
- Indent each clause of a SQL statement.

### Alignment

- Align related items vertically.
- Align column names in SELECT statements.
- Align conditions in WHERE clauses.

### Joins

- Use explicit JOIN syntax instead of implicit joins in the WHERE clause.
- Specify the join type (INNER, LEFT, RIGHT, FULL).

### Example

```sql
SELECT
    a.acc_id,
    a.acc_username,
    a.acc_email_address,
    h.hw_id,
    h.hw_name
FROM
    accounts a
LEFT JOIN
    hardware h ON a.acc_id = h.acc_id
WHERE
    a.prime = TRUE
    AND a.lock = FALSE
ORDER BY
    a.acc_created_at DESC
LIMIT 10;
```

## Type Hints

We use type hints for all Python code. This helps with code readability and enables better IDE support.

### Basic Types

- Use `int`, `float`, `str`, `bool`, etc. for basic types.
- Use `List[T]`, `Dict[K, V]`, `Tuple[T, ...]`, etc. for container types.
- Use `Optional[T]` for values that can be `None`.
- Use `Any` sparingly, only when the type is truly unknown.

### Return Types

- Always specify return types for functions and methods.
- Use `None` for functions that don't return a value.
- Use `-> None` for functions that don't return a value.

### Example

```python
from typing import Dict, List, Optional, Any

def get_account(acc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an account by ID.
    
    Args:
        acc_id: The account ID
        
    Returns:
        The account details or None if not found
    """
    # ...
```

## Docstrings

We use Google-style docstrings for all Python code.

### Function Docstrings

- Start with a brief description of what the function does.
- Add a more detailed description if necessary.
- Document all parameters using the `Args:` section.
- Document the return value using the `Returns:` section.
- Document any exceptions raised using the `Raises:` section.
- Document any side effects using the `Side Effects:` section.

### Class Docstrings

- Start with a brief description of what the class represents.
- Add a more detailed description if necessary.
- Document all attributes using the `Attributes:` section.
- Document any class-level exceptions using the `Raises:` section.

### Module Docstrings

- Start with a brief description of what the module does.
- Add a more detailed description if necessary.
- Document any module-level variables using the `Variables:` section.
- Document any module-level exceptions using the `Raises:` section.

### Example

```python
"""
Account management module.

This module provides functions for managing accounts, including
creating, reading, updating, and deleting accounts.

Variables:
    DEFAULT_LIMIT: Default limit for pagination
    DEFAULT_OFFSET: Default offset for pagination
"""

DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 0

def get_account(acc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an account by ID.
    
    This function retrieves an account from the database by its ID.
    If the account is not found, it returns None.
    
    Args:
        acc_id: The account ID
        
    Returns:
        The account details or None if not found
        
    Raises:
        ValueError: If the account ID is invalid
        DatabaseError: If there's an error connecting to the database
    """
    # ...
```

## Imports

### Import Order

1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

### Import Style

- Use absolute imports instead of relative imports.
- Import specific functions or classes when possible.
- Use `import x as y` when the name is too long or conflicts with another name.
- Use `from x import y` when importing specific functions or classes.
- Use `from x import y as z` when the name conflicts with another name.

### Example

```python
# Standard library imports
import json
import logging
from typing import Dict, List, Optional, Any

# Third-party imports
import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

# Local imports
from db import get_db_connection
from models.account import Account, AccountCreate, AccountUpdate
from utils.logging import get_logger
```

## Error Handling

### Exceptions

- Use specific exceptions instead of generic ones.
- Create custom exceptions for specific error cases.
- Document all exceptions that a function can raise.
- Handle exceptions at the appropriate level.

### Try-Except Blocks

- Use try-except blocks to handle exceptions.
- Catch specific exceptions instead of catching all exceptions.
- Keep try blocks as small as possible.
- Log exceptions with appropriate context.

### Example

```python
try:
    account = get_account(acc_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
except ValueError as e:
    logger.error(f"Invalid account ID: {acc_id}", exc_info=True)
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

## Logging

### Log Levels

- `DEBUG`: Detailed information, typically of interest only when diagnosing problems.
- `INFO`: Confirmation that things are working as expected.
- `WARNING`: An indication that something unexpected happened, or indicative of some problem in the near future.
- `ERROR`: Due to a more serious problem, the software has not been able to perform some function.
- `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running.

### Log Messages

- Log messages should be clear and concise.
- Include relevant context in log messages.
- Use string formatting for log messages.
- Log exceptions with `exc_info=True`.

### Example

```python
logger = get_logger(__name__)

def get_account(acc_id: str) -> Optional[Dict[str, Any]]:
    """Get an account by ID."""
    logger.debug(f"Getting account with ID: {acc_id}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE acc_id = %s", (acc_id,))
            account = cursor.fetchone()
            
            if account:
                logger.info(f"Found account with ID: {acc_id}")
                return dict(zip([column[0] for column in cursor.description], account))
            else:
                logger.warning(f"Account not found with ID: {acc_id}")
                return None
    except Exception as e:
        logger.error(f"Error getting account with ID: {acc_id}", exc_info=True)
        raise
```

## Testing

### Test Structure

- Use pytest for testing.
- Organize tests in the same structure as the code being tested.
- Use descriptive test names that explain what is being tested.
- Use the Arrange-Act-Assert pattern for tests.

### Test Coverage

- Aim for at least 80% code coverage.
- Test all code paths, including error cases.
- Use parameterized tests for testing multiple inputs.
- Use mocks for external dependencies.

### Example

```python
def test_get_account_returns_account_when_found():
    """Test that get_account returns an account when found."""
    # Arrange
    acc_id = "76561199123456789"
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (acc_id, "username", "email@example.com")
    mock_cursor.description = [("acc_id",), ("acc_username",), ("acc_email_address",)]
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    with patch("db.get_db_connection", return_value=mock_conn):
        # Act
        account = get_account(acc_id)
        
        # Assert
        assert account is not None
        assert account["acc_id"] == acc_id
        assert account["acc_username"] == "username"
        assert account["acc_email_address"] == "email@example.com"
```

## Security

### Input Validation

- Validate all user input.
- Use Pydantic models for request validation.
- Use parameterized queries to prevent SQL injection.
- Sanitize all user input before using it in SQL queries.

### Authentication and Authorization

- Use JWT tokens for authentication.
- Implement role-based access control.
- Use secure password hashing.
- Implement proper session management.

### Sensitive Data

- Do not log sensitive data.
- Do not store sensitive data in plain text.
- Use environment variables for sensitive configuration.
- Use secure connections for transmitting sensitive data.

### Example

```python
@router.get("/{acc_id}", response_model=AccountResponse)
async def get_account(
    acc_id: str = Path(..., description="The account ID"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get an account by ID."""
    # Check if the user has permission to access the account
    if current_user["role"] != "admin" and current_user["id"] != acc_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this account")
    
    account = get_account(acc_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account
```

## Performance

### Database Queries

- Use indexes for frequently queried columns.
- Use pagination for large result sets.
- Use cursor-based pagination for better performance.
- Use field selection to reduce the amount of data transferred.
- Use batch operations for bulk operations.

### Caching

- Use caching for frequently accessed data.
- Use cache headers for API responses.
- Implement cache invalidation for updated data.
- Use connection pooling for database connections.

### Asynchronous Programming

- Use asynchronous programming for I/O-bound operations.
- Use thread pools for CPU-bound operations.
- Use background tasks for long-running operations.
- Use streaming responses for large result sets.

### Example

```python
@router.get("/list", response_model=AccountListResponse)
async def list_accounts(
    limit: int = Query(100, description="Maximum number of accounts to return"),
    offset: int = Query(0, description="Number of accounts to skip"),
    sort_by: str = Query("acc_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    response: Response = None
):
    """List accounts with pagination."""
    # Set cache headers
    if response:
        response.headers["Cache-Control"] = "max-age=60, public"
    
    # Get accounts with pagination
    accounts, total = await get_accounts_with_pagination(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user
    )
    
    return {
        "accounts": accounts,
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

## Code Organization

### Project Structure

```
accountdb/
├── backend/
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── ...
│   │   └── ...
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── rate_limiting.py
│   │   └── ...
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py
│   │   └── ...
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   └── ...
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── init_db.py
│   │   └── ...
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_accounts.py
│   │   └── ...
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── ...
│   ├── config.py
│   ├── dependencies.py
│   ├── main.py
│   └── requirements.txt
├── docs/
│   ├── developer_guides/
│   │   ├── coding_standards.md
│   │   └── ...
│   ├── user_guides/
│   │   ├── user_guide.md
│   │   └── ...
│   └── ...
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### Module Organization

- Each module should have a single responsibility.
- Related functionality should be grouped together.
- Use `__init__.py` files to expose the public API of a package.
- Use relative imports within a package.

### Example

```python
"""
Account management module.

This module provides functions for managing accounts, including
creating, reading, updating, and deleting accounts.
"""

from .models import Account, AccountCreate, AccountUpdate
from .router import router

__all__ = ["Account", "AccountCreate", "AccountUpdate", "router"]
```

## Naming Conventions

### Variables and Functions

- Use snake_case for variable and function names.
- Use descriptive names that explain what the variable or function does.
- Avoid single-letter variable names, except for loop indices.
- Prefix private variables and functions with a single underscore.

### Classes

- Use PascalCase for class names.
- Use descriptive names that explain what the class represents.
- Use singular nouns for class names.

### Constants

- Use UPPER_CASE for constants.
- Use descriptive names that explain what the constant represents.

### Example

```python
# Constants
DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 0

# Variables
account_id = "76561199123456789"
user_accounts = []

# Functions
def get_account(acc_id: str) -> Optional[Dict[str, Any]]:
    """Get an account by ID."""
    # ...

# Classes
class AccountManager:
    """Manager for account operations."""
    
    def __init__(self, db_connection):
        self._db_connection = db_connection
    
    def get_account(self, acc_id: str) -> Optional[Dict[str, Any]]:
        """Get an account by ID."""
        # ...
```

## Comments

### When to Comment

- Comment complex algorithms.
- Comment non-obvious code.
- Comment workarounds for bugs or limitations.
- Comment code that might be confusing.

### When Not to Comment

- Don't comment obvious code.
- Don't comment what the code does (use docstrings for that).
- Don't comment out code (use version control instead).

### Comment Style

- Use complete sentences.
- Start with a capital letter.
- End with a period.
- Use present tense.

### Example

```python
# This is a complex algorithm for finding the optimal path.
# It uses a modified version of Dijkstra's algorithm with a custom heuristic.
def find_optimal_path(graph, start, end):
    # ...
    
    # Skip nodes that have already been visited.
    if node in visited:
        continue
    
    # This is a workaround for a bug in the graph library.
    # The bug causes the algorithm to get stuck in an infinite loop
    # when there are cycles in the graph.
    if node in path:
        continue
    
    # ...
```

## Version Control

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `perf`: Code changes that improve performance
- `test`: Adding or updating tests
- `chore`: Changes to the build process or auxiliary tools

Example:
```
feat(accounts): add pagination to accounts list endpoint

- Add limit and offset parameters
- Add total count to response
- Add pagination links to response

Closes #123
```

### Branch Naming

- `feature/your-feature-name`: For new features
- `fix/your-bug-fix`: For bug fixes
- `docs/your-documentation`: For documentation changes
- `refactor/your-refactoring`: For code refactoring
- `test/your-test`: For adding or updating tests

### Pull Requests

- Create a pull request for each feature or bug fix.
- Use a descriptive title for the pull request.
- Fill out the pull request template.
- Request a review from at least one maintainer.
- Address all feedback from the code review.

## Tools and Enforcement

### Code Formatting

We use the following tools for code formatting:

- **Black**: Code formatter
- **isort**: Import sorter

To format your code:

```bash
black .
isort .
```

### Linting

We use the following tools for linting:

- **flake8**: Linter
- **mypy**: Type checker

To lint your code:

```bash
flake8 .
mypy .
```

### Pre-commit Hooks

We use pre-commit hooks to enforce code style and run tests before committing. To set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

### Continuous Integration

We use GitHub Actions for continuous integration. The CI pipeline runs the following checks:

- Code formatting
- Linting
- Type checking
- Tests
- Test coverage

## Conclusion

Following these coding standards ensures that the AccountDB codebase remains consistent, maintainable, and high-quality. All contributors are expected to adhere to these standards. If you have any questions, please don't hesitate to ask.
