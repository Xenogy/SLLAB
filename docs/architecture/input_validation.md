# Input Validation

## Overview

This document describes the input validation approach used in the AccountDB project. Input validation is a critical security feature that ensures that data received from users or external systems is valid, safe, and meets the expected format and constraints before being processed by the application.

## Implementation

### Validation Module

The project uses a centralized validation module (`validation.py`) to handle all input validation. This module provides functions for validating various types of data, including:

- Strings
- Numbers
- Emails
- Dates
- Files
- Account data
- Card data
- Hardware data

```python
# Example validation function
def validate_string(value: str, min_length: int = 1, max_length: int = 255, pattern: Optional[str] = None) -> ValidationResult:
    """
    Validate a string value.
    
    Args:
        value: The string to validate
        min_length: The minimum length of the string
        max_length: The maximum length of the string
        pattern: A regular expression pattern the string must match
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    if not isinstance(value, str):
        errors.append({
            "field": "value",
            "message": f"Value must be a string, got {type(value).__name__}"
        })
        return ValidationResult(valid=False, errors=errors)
    
    if len(value) < min_length:
        errors.append({
            "field": "value",
            "message": f"String must be at least {min_length} characters long"
        })
    
    if len(value) > max_length:
        errors.append({
            "field": "value",
            "message": f"String must be at most {max_length} characters long"
        })
    
    if pattern and not re.match(pattern, value):
        errors.append({
            "field": "value",
            "message": f"String must match pattern {pattern}"
        })
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### Validation Middleware

The project uses validation middleware (`middleware/validation.py`) to validate requests before they reach the endpoint handlers. This middleware provides functions for validating:

- Request bodies
- Query parameters
- Path parameters
- File uploads

```python
# Example middleware function
async def validate_request_body(request: Request, model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Validate request body against a Pydantic model.
    
    Args:
        request: The FastAPI request object
        model: The Pydantic model to validate against
        
    Returns:
        Dict[str, Any]: The validated data
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        body = await request.json()
        validated_data = model(**body)
        return validated_data.dict()
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"]
            })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors}
        )
```

### File Upload Validation

The project validates file uploads to ensure that they meet the expected format and size constraints. This includes:

- Validating file types
- Validating file sizes
- Validating file contents

```python
# Example file validation
def validate_file(content_type: str, size: int, file_type: str = None, max_size: int = MAX_FILE_SIZE) -> ValidationResult:
    """
    Validate a file's content type and size.
    
    Args:
        content_type: The content type to validate
        size: The file size in bytes
        file_type: The expected file type (json, csv, image, text)
        max_size: The maximum allowed size in bytes
        
    Returns:
        ValidationResult: The validation result
    """
    errors = []
    
    # Validate file type
    if file_type:
        if file_type not in ALLOWED_FILE_TYPES:
            errors.append({
                "field": "file_type",
                "message": f"File type {file_type} is not supported. Supported types: {', '.join(ALLOWED_FILE_TYPES.keys())}"
            })
        else:
            allowed_types = ALLOWED_FILE_TYPES[file_type]
            type_result = validate_file_type(content_type, allowed_types)
            if not type_result.valid:
                errors.extend(type_result.errors)
    
    # Validate file size
    size_result = validate_file_size(size, max_size)
    if not size_result.valid:
        errors.extend(size_result.errors)
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### Pydantic Models

The project uses Pydantic models to validate complex data structures. These models provide:

- Type validation
- Field validation
- Custom validators
- Default values
- Required fields

```python
# Example Pydantic model
class UserValidator(BaseModel):
    """Validator for user data."""
    username: str
    password: str
    
    @validator('username')
    def username_must_be_valid(cls, v):
        result = validate_username(v)
        if not result.valid:
            raise ValueError(result.errors[0]['message'])
        return v
    
    @validator('password')
    def password_must_be_valid(cls, v):
        result = validate_password(v)
        if not result.valid:
            raise ValueError(result.errors[0]['message'])
        return v
```

## Usage

### Validating Request Bodies

To validate request bodies, use the `validate_request_body` function:

```python
@router.post("/users")
async def create_user(request: Request):
    validated_data = await validate_request_body(request, UserValidator)
    # Process validated data
    return {"message": "User created successfully"}
```

### Validating Query Parameters

To validate query parameters, use the validation functions:

```python
@router.get("/users")
async def list_users(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None
):
    # Validate pagination parameters
    pagination = validate_pagination(limit, offset)
    
    # Validate search parameter
    search = validate_search(search)
    
    # Process validated parameters
    return {"users": []}
```

### Validating File Uploads

To validate file uploads, use the `validate_file_upload` function:

```python
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate file
    await validate_file_upload(file, file_type="json", max_size=10 * 1024 * 1024)
    
    # Process validated file
    return {"message": "File uploaded successfully"}
```

## Security Considerations

### Input Sanitization

Input validation is not a substitute for input sanitization. Even validated input should be sanitized before being used in sensitive operations such as:

- SQL queries
- HTML rendering
- Shell commands
- File system operations

### Validation Bypass

Validation can be bypassed if not applied consistently. Ensure that all input is validated, including:

- Request bodies
- Query parameters
- Path parameters
- Headers
- Cookies
- File uploads

### Error Messages

Validation error messages should be informative but not reveal sensitive information. Avoid including:

- Internal implementation details
- Stack traces
- Database queries
- File paths

## Best Practices

1. **Validate all input**: Validate all input from external sources, including users, APIs, and files.
2. **Use a centralized validation module**: Use a centralized validation module to ensure consistent validation.
3. **Use Pydantic models**: Use Pydantic models to validate complex data structures.
4. **Validate early**: Validate input as early as possible in the request processing pipeline.
5. **Validate strictly**: Validate input strictly, rejecting anything that doesn't meet the expected format and constraints.
6. **Log validation errors**: Log validation errors to help identify potential attacks.
7. **Return helpful error messages**: Return helpful error messages to users to help them correct their input.
8. **Use parameterized queries**: Use parameterized queries to prevent SQL injection.
9. **Sanitize validated input**: Sanitize validated input before using it in sensitive operations.
10. **Test validation**: Test validation with both valid and invalid input to ensure it works as expected.
