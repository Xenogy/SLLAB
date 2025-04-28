# API Design Issues

## High Priority Issues

### 1. Inconsistent Error Handling

**Description:**  
Error handling is inconsistent across endpoints. Some endpoints use try/except blocks with detailed error messages, while others have minimal error handling.

**Impact:**  
This makes debugging difficult and can lead to unclear error messages for users. It also increases the risk of unhandled exceptions crashing the application.

**Examples:**
- Some endpoints use detailed try/except blocks with specific error messages
- Other endpoints have minimal error handling
- Some errors are logged while others are not
- Inconsistent HTTP status codes for similar errors

**Code Example:**
```python
# Detailed error handling
try:
    # Code that might raise an exception
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Proxmox node not found")
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error retrieving Proxmox node: {e}")
    raise HTTPException(status_code=500, detail=f"Error retrieving Proxmox node: {str(e)}")

# Minimal error handling
result = cursor.fetchone()
if not result:
    raise HTTPException(status_code=404, detail="Not found")
```

**Recommended Fix:**
- Create a consistent error handling pattern
- Implement middleware for common error handling
- Ensure all endpoints return consistent error responses
- Add proper logging for all errors

### 2. Direct SQL Queries in Endpoints

**Description:**  
Many endpoints contain direct SQL queries instead of using a data access layer or repository pattern.

**Impact:**  
This makes the code harder to maintain and test. It also increases the risk of SQL injection vulnerabilities and makes it difficult to change the database schema.

**Examples:**
- Most endpoints contain SQL queries directly in the handler function
- SQL queries are duplicated across multiple endpoints
- No abstraction for database operations

**Code Example:**
```python
@router.get("/{node_id}", response_model=ProxmoxNodeResponse)
async def get_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
        cursor = conn.cursor()
        try:
            # Direct SQL query in endpoint
            query = """
                SELECT
                    id, name, hostname, port, status, api_key, last_seen,
                    created_at, updated_at, owner_id
                FROM proxmox_nodes
                WHERE id = %s
            """
            cursor.execute(query, (node_id,))
            result = cursor.fetchone()
            # ...
```

**Recommended Fix:**
- Create a data access layer or repository pattern
- Move SQL queries to repository classes
- Use dependency injection for repositories
- Create reusable functions for common queries

### 3. Lack of Comprehensive Input Validation

**Description:**  
Input validation is inconsistent and sometimes missing. Some endpoints validate inputs thoroughly, while others have minimal validation.

**Impact:**  
This can lead to security vulnerabilities, data integrity issues, and unexpected behavior.

**Examples:**
- Some endpoints use Pydantic models for validation
- Other endpoints have minimal validation
- Some validation is done manually in the endpoint handler
- Inconsistent validation rules for similar data

**Code Example:**
```python
# Thorough validation with Pydantic
class ProxmoxNodeCreate(BaseModel):
    name: str
    hostname: str
    port: int = 8006

@router.post("/", response_model=ProxmoxNodeResponse)
async def create_proxmox_node(
    node: ProxmoxNodeCreate,
    current_user: dict = Depends(get_current_user)
):
    # ...

# Minimal validation
@router.get("/{node_id}")
async def get_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    # No validation for node_id (could be negative, zero, etc.)
    # ...
```

**Recommended Fix:**
- Use Pydantic models for all input validation
- Create consistent validation rules
- Add custom validators for complex validation
- Implement validation middleware for common validations

## Medium Priority Issues

### 1. Inconsistent Response Formats

**Description:**  
API responses have inconsistent formats. Some endpoints return lists, while others return objects with metadata.

**Impact:**  
This makes it harder for frontend developers to work with the API and increases the risk of bugs.

**Examples:**
- Some endpoints return lists: `[item1, item2, ...]`
- Others return objects with metadata: `{"items": [item1, item2, ...], "total": 2}`
- Inconsistent field naming (snake_case vs. camelCase)
- Inconsistent date formats

**Code Example:**
```python
# List response
@router.get("/proxmox", response_model=List[VMResponse])
async def get_proxmox_vms(
    current_user: dict = Depends(get_current_user)
):
    # ...
    return all_vms

# Object with metadata response
@router.get("/", response_model=VMListResponse)
async def get_vms(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    # ...
):
    # ...
    return {
        "vms": vms,
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

**Recommended Fix:**
- Standardize response formats
- Use consistent pagination patterns
- Use consistent field naming
- Document response formats

### 2. Missing API Documentation

**Description:**  
API endpoints are not well-documented. There is no OpenAPI/Swagger documentation, and endpoint docstrings are inconsistent.

**Impact:**  
This makes it harder for developers to understand and use the API.

**Examples:**
- No OpenAPI/Swagger documentation
- Inconsistent docstrings
- Missing examples
- No documentation for error responses

**Code Example:**
```python
# Good docstring
@router.get("/{node_id}", response_model=ProxmoxNodeResponse)
async def get_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific Proxmox node by ID.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    # ...

# Minimal docstring
@router.delete("/{node_id}")
async def delete_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a Proxmox node."""
    # ...
```

**Recommended Fix:**
- Add OpenAPI/Swagger documentation
- Standardize docstrings
- Add examples for all endpoints
- Document error responses

## Low Priority Issues

### 1. Inconsistent Naming Conventions

**Description:**  
Naming conventions are inconsistent across the codebase. Some endpoints use snake_case, while others use camelCase.

**Impact:**  
This makes the code harder to understand and maintain.

**Examples:**
- Inconsistent variable naming (snake_case vs. camelCase)
- Inconsistent function naming
- Inconsistent endpoint naming

**Code Example:**
```python
# snake_case
@router.get("/proxmox-nodes/{node_id}")
async def get_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    # ...

# camelCase
@router.get("/vms/{vmId}")
async def getVm(
    vmId: int,
    currentUser: dict = Depends(get_current_user)
):
    # ...
```

**Recommended Fix:**
- Standardize naming conventions
- Create a style guide
- Use linting tools to enforce conventions
