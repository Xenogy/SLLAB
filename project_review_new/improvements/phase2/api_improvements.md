# Phase 2: API Improvements

## Overview

This phase focuses on improving the API design, error handling, and input validation to create a more robust and maintainable backend. The goal is to standardize patterns across all endpoints and make the API more consistent and reliable.

## Objectives

1. Standardize error handling
2. Improve input validation
3. Create consistent response formats
4. Refactor direct SQL queries to use the repository pattern
5. Implement API documentation

## Detailed Tasks

### 1. Standardize Error Handling

#### 1.1 Create Error Handling Middleware

Create middleware for handling common errors and providing consistent error responses.

```python
# backend/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

async def error_handler_middleware(request: Request, call_next):
    """Middleware for handling errors and providing consistent error responses."""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if not isinstance(exc, StarletteHTTPException) else None,
                "path": request.url.path
            }
        )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "path": request.url.path
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler for HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Request error",
            "detail": exc.detail,
            "path": request.url.path
        }
    )
```

#### 1.2 Define Standard Error Response Format

Create a standard format for error responses.

```python
# backend/models/errors.py
from pydantic import BaseModel
from typing import Any, Optional, List, Dict

class ErrorDetail(BaseModel):
    """Model for error details."""
    loc: Optional[List[str]] = None
    msg: str
    type: str

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    detail: Optional[Any] = None
    path: Optional[str] = None
```

#### 1.3 Implement Consistent Error Logging

Create utilities for consistent error logging.

```python
# backend/utils/logging.py
import logging
import traceback
from fastapi import Request

logger = logging.getLogger(__name__)

def log_error(request: Request, error: Exception, message: str = "Error occurred"):
    """Log an error with consistent format."""
    logger.error(
        f"{message}: {error}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Client: {request.client.host if request.client else 'Unknown'}\n"
        f"Traceback: {traceback.format_exc()}"
    )

def log_warning(request: Request, message: str):
    """Log a warning with consistent format."""
    logger.warning(
        f"{message}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Client: {request.client.host if request.client else 'Unknown'}"
    )

def log_info(request: Request, message: str):
    """Log an info message with consistent format."""
    logger.info(
        f"{message}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}"
    )
```

#### 1.4 Refactor Endpoints to Use Standard Error Handling

Refactor all endpoints to use the standard error handling pattern.

```python
# backend/routers/proxmox_nodes.py
@router.get("/{node_id}", response_model=ProxmoxNodeResponse)
async def get_proxmox_node(
    node_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific Proxmox node by ID.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    try:
        repository = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])
        node = repository.get_node_by_id(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")
        
        return node
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, e, "Error retrieving Proxmox node")
        raise HTTPException(status_code=500, detail="Error retrieving Proxmox node")
```

### 2. Improve Input Validation

#### 2.1 Create Validation Utilities

Create utilities for common validation tasks.

```python
# backend/utils/validation.py
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field
import re

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
    
class SearchParams(BaseModel):
    """Common search parameters."""
    search: Optional[str] = None
    
    @validator('search')
    def validate_search(cls, v):
        if v and len(v) < 2:
            raise ValueError("Search term must be at least 2 characters")
        return v

def validate_hostname(hostname: str) -> str:
    """Validate a hostname."""
    if not hostname:
        raise ValueError("Hostname cannot be empty")
    
    # Simple hostname validation
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,61}[a-zA-Z0-9])?$', hostname):
        raise ValueError("Invalid hostname format")
    
    return hostname

def validate_port(port: int) -> int:
    """Validate a port number."""
    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535")
    
    return port

def validate_vmid(vmid: int) -> int:
    """Validate a VMID."""
    if vmid < 100:
        raise ValueError("VMID must be at least 100")
    
    return vmid
```

#### 2.2 Implement Comprehensive Input Validation

Use Pydantic models for comprehensive input validation.

```python
# backend/models/proxmox_nodes.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from backend.utils.validation import validate_hostname, validate_port

class ProxmoxNodeBase(BaseModel):
    """Base model for Proxmox nodes."""
    name: str = Field(..., min_length=1, max_length=100)
    hostname: str
    port: int = Field(8006, ge=1, le=65535)
    
    @validator('hostname')
    def validate_hostname(cls, v):
        return validate_hostname(v)
    
    @validator('port')
    def validate_port(cls, v):
        return validate_port(v)

class ProxmoxNodeCreate(ProxmoxNodeBase):
    """Model for creating a new Proxmox node."""
    pass

class ProxmoxNodeUpdate(ProxmoxNodeBase):
    """Model for updating a Proxmox node."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hostname: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    
    @validator('hostname')
    def validate_hostname(cls, v):
        if v is None:
            return v
        return validate_hostname(v)
    
    @validator('port')
    def validate_port(cls, v):
        if v is None:
            return v
        return validate_port(v)

class ProxmoxNodeResponse(ProxmoxNodeBase):
    """Response model for Proxmox nodes."""
    id: int
    status: str
    api_key: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    owner_id: int

class ProxmoxNodeListResponse(BaseModel):
    """Response model for listing Proxmox nodes."""
    nodes: List[ProxmoxNodeResponse]
    total: int
    limit: int
    offset: int
```

#### 2.3 Add Custom Validators for Complex Validation

Create custom validators for complex validation rules.

```python
# backend/models/vms.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from backend.utils.validation import validate_vmid

class VMBase(BaseModel):
    """Base model for VMs."""
    vmid: int
    name: str = Field(..., min_length=1, max_length=100)
    ip_address: Optional[str] = None
    status: str = "stopped"
    cpu_cores: Optional[int] = Field(None, ge=1, le=128)
    memory_mb: Optional[int] = Field(None, ge=128)
    disk_gb: Optional[int] = Field(None, ge=1)
    proxmox_node_id: Optional[int] = None
    template_id: Optional[int] = None
    notes: Optional[str] = None
    
    @validator('vmid')
    def validate_vmid(cls, v):
        return validate_vmid(v)
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v is None:
            return v
        
        # Simple IP address validation
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Invalid IP address format")
        
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["running", "stopped", "paused", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return v
```

#### 2.4 Implement Validation Middleware

Create middleware for common validation tasks.

```python
# backend/middleware/validation.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import json

class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for common validation tasks."""
    
    async def dispatch(self, request: Request, call_next):
        # Check content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return Response(
                    content=json.dumps({
                        "error": "Validation error",
                        "detail": "Content-Type must be application/json",
                        "path": request.url.path
                    }),
                    status_code=415,
                    media_type="application/json"
                )
        
        # Proceed with the request
        return await call_next(request)
```

### 3. Create Consistent Response Formats

#### 3.1 Define Standard Response Models

Create standard response models for different types of responses.

```python
# backend/models/responses.py
from pydantic import BaseModel, Field
from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response model."""
    items: List[T]
    total: int
    limit: int
    offset: int

class SuccessResponse(BaseModel):
    """Standard success response model."""
    success: bool = True
    message: str
    data: Optional[Any] = None

class CreatedResponse(BaseModel):
    """Standard response for resource creation."""
    id: Any
    created_at: datetime
    message: str = "Resource created successfully"

class UpdatedResponse(BaseModel):
    """Standard response for resource update."""
    id: Any
    updated_at: datetime
    message: str = "Resource updated successfully"

class DeletedResponse(BaseModel):
    """Standard response for resource deletion."""
    id: Any
    message: str = "Resource deleted successfully"
```

#### 3.2 Implement Pagination Utilities

Create utilities for consistent pagination.

```python
# backend/utils/pagination.py
from typing import Dict, List, Any, Optional, Tuple
from fastapi import Query

def paginate_query(query: str, params: List, limit: int, offset: int) -> Tuple[str, List]:
    """Add pagination to a SQL query."""
    # Add ORDER BY if not present
    if "ORDER BY" not in query.upper():
        query += " ORDER BY id DESC"
    
    # Add pagination
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    return query, params

def get_pagination_params(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, int]:
    """Get pagination parameters from request."""
    return {"limit": limit, "offset": offset}

def create_paginated_response(items: List[Any], total: int, limit: int, offset: int) -> Dict[str, Any]:
    """Create a paginated response."""
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

#### 3.3 Implement Filtering Utilities

Create utilities for consistent filtering.

```python
# backend/utils/filtering.py
from typing import Dict, List, Any, Optional, Tuple

def add_search_filter(query: str, params: List, search: Optional[str], columns: List[str]) -> Tuple[str, List]:
    """Add search filter to a SQL query."""
    if not search:
        return query, params
    
    search_conditions = []
    for column in columns:
        search_conditions.append(f"{column} ILIKE %s")
        params.append(f"%{search}%")
    
    query += f" AND ({' OR '.join(search_conditions)})"
    
    return query, params

def add_status_filter(query: str, params: List, status: Optional[str]) -> Tuple[str, List]:
    """Add status filter to a SQL query."""
    if not status:
        return query, params
    
    query += " AND status = %s"
    params.append(status)
    
    return query, params
```

#### 3.4 Refactor Endpoints to Use Consistent Response Formats

Refactor all endpoints to use the standard response formats.

```python
# backend/routers/proxmox_nodes.py
@router.get("/", response_model=PaginatedResponse[ProxmoxNodeResponse])
async def get_proxmox_nodes(
    pagination: Dict[str, int] = Depends(get_pagination_params),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of Proxmox nodes with pagination and filtering.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    try:
        repository = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])
        result = repository.get_nodes(
            limit=pagination["limit"],
            offset=pagination["offset"],
            search=search,
            status=status
        )
        
        return create_paginated_response(
            items=result["nodes"],
            total=result["total"],
            limit=pagination["limit"],
            offset=pagination["offset"]
        )
    except Exception as e:
        log_error(request, e, "Error retrieving Proxmox nodes")
        raise HTTPException(status_code=500, detail="Error retrieving Proxmox nodes")
```

### 4. Refactor Direct SQL Queries

#### 4.1 Create Repository Classes

Create repository classes for all entities that use the database access layer created in Phase 1.

```python
# backend/repositories/vms.py
from typing import Dict, List, Any, Optional
from db.access import DatabaseAccess
from backend.utils.pagination import paginate_query
from backend.utils.filtering import add_search_filter, add_status_filter

class VMRepository(DatabaseAccess):
    """Repository for VMs."""
    
    def get_vms(self, limit: int = 10, offset: int = 0, search: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Get a list of VMs with pagination and filtering."""
        query = """
            SELECT
                v.id, v.vmid, v.name, v.ip_address, v.status, v.cpu_cores, v.memory_mb,
                v.disk_gb, v.proxmox_node_id, pn.name as proxmox_node, v.template_id, v.notes, v.created_at, v.updated_at, v.owner_id
            FROM vms v
            LEFT JOIN proxmox_nodes pn ON v.proxmox_node_id = pn.id
            WHERE 1=1
        """
        params = []
        
        # Add search filter
        if search:
            query, params = add_search_filter(query, params, search, ["v.name", "v.ip_address"])
        
        # Add status filter
        if status:
            query, params = add_status_filter(query, params, status)
        
        # Count total records
        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS filtered_vms"
        count_result = self.execute_query(count_query, tuple(params))
        total = count_result[0]['total'] if count_result else 0
        
        # Add pagination
        query, params = paginate_query(query, params, limit, offset)
        
        # Execute the query
        vms = self.execute_query(query, tuple(params))
        
        return {
            "vms": vms,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_vm_by_id(self, vm_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific VM by ID."""
        query = """
            SELECT
                v.id, v.vmid, v.name, v.ip_address, v.status, v.cpu_cores, v.memory_mb,
                v.disk_gb, v.proxmox_node_id, pn.name as proxmox_node, v.template_id, v.notes, v.created_at, v.updated_at, v.owner_id
            FROM vms v
            LEFT JOIN proxmox_nodes pn ON v.proxmox_node_id = pn.id
            WHERE v.id = %s
        """
        results = self.execute_query(query, (vm_id,))
        return results[0] if results else None
    
    def create_vm(self, vm_data: Dict[str, Any], owner_id: int) -> Dict[str, Any]:
        """Create a new VM."""
        query = """
            INSERT INTO vms (
                vmid, name, ip_address, status, cpu_cores, memory_mb,
                disk_gb, proxmox_node_id, template_id, notes, owner_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING
                id, vmid, name, ip_address, status, cpu_cores, memory_mb,
                disk_gb, proxmox_node_id, template_id, notes, created_at, updated_at, owner_id
        """
        params = (
            vm_data["vmid"],
            vm_data["name"],
            vm_data.get("ip_address"),
            vm_data.get("status", "stopped"),
            vm_data.get("cpu_cores"),
            vm_data.get("memory_mb"),
            vm_data.get("disk_gb"),
            vm_data.get("proxmox_node_id"),
            vm_data.get("template_id"),
            vm_data.get("notes"),
            owner_id
        )
        results = self.execute_query(query, params)
        return results[0] if results else None
```

#### 4.2 Refactor Endpoints to Use Repository Classes

Refactor all endpoints to use the repository classes.

```python
# backend/routers/vms.py
@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific virtual machine by ID.
    Uses Row-Level Security to ensure users can only see their own VMs.
    """
    try:
        repository = VMRepository(user_id=current_user["id"], user_role=current_user["role"])
        vm = repository.get_vm_by_id(vm_id)
        
        if not vm:
            raise HTTPException(status_code=404, detail="VM not found")
        
        return vm
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, e, "Error retrieving VM")
        raise HTTPException(status_code=500, detail="Error retrieving VM")

@router.post("/", response_model=VMResponse)
async def create_vm(
    vm: VMCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new virtual machine.
    Sets the owner_id to the current user's ID.
    """
    try:
        repository = VMRepository(user_id=current_user["id"], user_role=current_user["role"])
        created_vm = repository.create_vm(vm.dict(), current_user["id"])
        
        # Get the proxmox_node name if proxmox_node_id is not None
        if created_vm["proxmox_node_id"] is not None:
            node_repository = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])
            node = node_repository.get_node_by_id(created_vm["proxmox_node_id"])
            if node:
                created_vm["proxmox_node"] = node["name"]
        
        return created_vm
    except Exception as e:
        log_error(request, e, "Error creating VM")
        raise HTTPException(status_code=500, detail="Error creating VM")
```

### 5. Implement API Documentation

#### 5.1 Add OpenAPI Documentation

Configure FastAPI to generate comprehensive OpenAPI documentation.

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="AccountDB API",
    description="API for managing accounts, hardware, virtual machines, and Proxmox nodes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="AccountDB API",
        version="1.0.0",
        description="API for managing accounts, hardware, virtual machines, and Proxmox nodes",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Apply security to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

#### 5.2 Add Detailed Docstrings

Add detailed docstrings to all endpoints.

```python
# backend/routers/proxmox_nodes.py
@router.get("/{node_id}", response_model=ProxmoxNodeResponse)
async def get_proxmox_node(
    node_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific Proxmox node by ID.
    
    This endpoint retrieves detailed information about a specific Proxmox node.
    It uses Row-Level Security to ensure users can only see their own nodes.
    
    Parameters:
    - **node_id**: The ID of the Proxmox node to retrieve
    
    Returns:
    - **ProxmoxNodeResponse**: Detailed information about the Proxmox node
    
    Raises:
    - **404**: If the Proxmox node is not found
    - **500**: If there is an error retrieving the Proxmox node
    
    Security:
    - Requires authentication
    - Uses Row-Level Security to ensure users can only see their own nodes
    """
    try:
        repository = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])
        node = repository.get_node_by_id(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")
        
        return node
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, e, "Error retrieving Proxmox node")
        raise HTTPException(status_code=500, detail="Error retrieving Proxmox node")
```

#### 5.3 Add Examples

Add examples to the API documentation.

```python
# backend/models/proxmox_nodes.py
class ProxmoxNodeResponse(ProxmoxNodeBase):
    """Response model for Proxmox nodes."""
    id: int
    status: str
    api_key: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    owner_id: int
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "pve1",
                "hostname": "proxmox.example.com",
                "port": 8006,
                "status": "connected",
                "api_key": "HiWljrpE9xLgOz6x0A9bmEJwSgyd2KAi_xsb4V6xoPg",
                "last_seen": "2023-04-26T12:34:56",
                "created_at": "2023-04-25T10:20:30",
                "updated_at": "2023-04-26T12:34:56",
                "owner_id": 1
            }
        }
```

#### 5.4 Document Error Responses

Document all possible error responses for each endpoint.

```python
# backend/routers/proxmox_nodes.py
@router.get("/{node_id}", response_model=ProxmoxNodeResponse, responses={
    404: {"description": "Proxmox node not found", "model": ErrorResponse},
    500: {"description": "Internal server error", "model": ErrorResponse}
})
async def get_proxmox_node(
    node_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific Proxmox node by ID.
    
    This endpoint retrieves detailed information about a specific Proxmox node.
    It uses Row-Level Security to ensure users can only see their own nodes.
    
    Parameters:
    - **node_id**: The ID of the Proxmox node to retrieve
    
    Returns:
    - **ProxmoxNodeResponse**: Detailed information about the Proxmox node
    
    Raises:
    - **404**: If the Proxmox node is not found
    - **500**: If there is an error retrieving the Proxmox node
    
    Security:
    - Requires authentication
    - Uses Row-Level Security to ensure users can only see their own nodes
    """
    try:
        repository = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])
        node = repository.get_node_by_id(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")
        
        return node
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, e, "Error retrieving Proxmox node")
        raise HTTPException(status_code=500, detail="Error retrieving Proxmox node")
```

## Expected Outcomes

By implementing these improvements, we expect to achieve the following outcomes:

1. **Improved Error Handling**: All endpoints will have consistent error handling, making it easier to debug issues and providing better error messages to users.
2. **Better Input Validation**: All inputs will be thoroughly validated, reducing the risk of data integrity issues and security vulnerabilities.
3. **Consistent API Design**: All endpoints will follow consistent patterns for requests and responses, making the API easier to use and understand.
4. **Improved Maintainability**: The codebase will be more maintainable with repository classes and consistent patterns.
5. **Better Documentation**: The API will be well-documented, making it easier for developers to understand and use.

## Timeline

This phase is expected to take 3 weeks to complete:

- Week 1: Standardize error handling
- Week 2: Improve input validation
- Week 3: Create consistent response formats, refactor direct SQL queries, and implement API documentation
