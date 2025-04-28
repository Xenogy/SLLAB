# API Architecture

## Overview

The API is built using FastAPI, a modern, fast web framework for building APIs with Python. It provides endpoints for managing accounts, hardware profiles, cards, and user authentication.

## API Structure

### Routers

The API is organized into routers, each handling a specific domain:

1. **auth**: Authentication and user management
2. **accounts**: Account management
3. **hardware**: Hardware profile management
4. **cards**: Card management
5. **steam_auth**: Steam authentication
6. **account_status**: Account status management
7. **upload**: File upload for bulk account creation

### Middleware

1. **CORS Middleware**: Handles Cross-Origin Resource Sharing
2. **Authentication Middleware**: Validates JWT tokens

### Dependencies

1. **get_query_token**: Validates API token for backward compatibility
2. **get_token_header**: Validates token in header
3. **get_current_user**: Gets the current user from JWT token
4. **get_current_active_user**: Gets the current active user

## Authentication Flow

1. **Login**:
   - Client sends username and password to `/auth/token`
   - Server validates credentials and returns JWT token
   - Client stores token in localStorage

2. **Authenticated Requests**:
   - Client includes token in Authorization header
   - Server validates token and identifies user
   - Server sets RLS context based on user ID and role

3. **Public Endpoints**:
   - Some endpoints (e.g., `/auth/signup-status`, `/auth/register`) don't require authentication
   - These endpoints are marked with `dependencies=[]`

## API Endpoints

### Authentication

- `POST /auth/token`: Login and get access token
- `GET /auth/me`: Get current user information
- `POST /auth/register`: Register a new user
- `GET /auth/signup-status`: Check if signups are enabled
- `POST /auth/change-password`: Change user password

### Accounts

- `GET /accounts/list`: List accounts with pagination and filtering
- `POST /accounts/list`: List accounts (POST method)
- `GET /accounts/{acc_username}`: Get account by username
- `POST /accounts/info`: Get specific account information
- `POST /accounts/new`: Create a new account
- `POST /accounts/new/bulk`: Create multiple accounts
- `DELETE /accounts/{acc_id}`: Delete an account

### Hardware

- `GET /hardware`: List hardware profiles
- `GET /hardware/{id}`: Get hardware profile by ID
- `POST /hardware/new`: Create a new hardware profile
- `PUT /hardware/{id}`: Update a hardware profile
- `DELETE /hardware/{id}`: Delete a hardware profile

### Steam Gift Cards

- `GET /cards`: List Steam gift cards
- `GET /cards/{id}`: Get Steam gift card by ID
- `POST /cards/new`: Create a new Steam gift card
- `PUT /cards/{id}`: Update a Steam gift card
- `DELETE /cards/{id}`: Delete a Steam gift card

### Steam Authentication

- `GET /steam/auth/2fa`: Generate Steam Guard 2FA code
- `GET /steam/auth/info`: Get Steam authentication information

### Account Status

- `POST /account-status/lock`: Lock or unlock an account
- `POST /account-status/lock/bulk`: Lock or unlock multiple accounts
- `POST /account-status/prime`: Set prime status of an account
- `POST /account-status/prime/bulk`: Set prime status of multiple accounts
- `GET /account-status/fresh`: Get fresh (unused) accounts

### Upload

- `POST /upload/json`: Upload accounts from JSON file
- `POST /upload/csv`: Upload accounts from CSV file

## Database Connection Management

Each endpoint should use the appropriate database connection:

1. **User-Specific Connection**:
   ```python
   with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
       # Database operations with RLS context
   ```

2. **Regular Connection** (for non-RLS tables):
   ```python
   with get_db_connection() as db_conn:
       # Database operations without RLS context
   ```

## Error Handling

1. **HTTP Exceptions**:
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 500: Internal Server Error

2. **Custom Error Responses**:
   - Validation errors
   - Database errors
   - Authentication errors

## Current Issues and Improvement Areas

1. **Inconsistent Authentication**:
   - Some endpoints require authentication but don't use it properly
   - Public endpoints sometimes fail due to authentication requirements

2. **Database Connection Usage**:
   - Inconsistent use of database connection context managers
   - Some endpoints use the global connection instead of user-specific connection

3. **Error Handling**:
   - Inconsistent error handling across endpoints
   - Some errors are not properly logged or reported

## Recommended API Improvements

1. **Consistent Authentication**:
   - Clearly mark public endpoints with `dependencies=[]`
   - Ensure all authenticated endpoints use `get_current_active_user`

2. **Database Connection Usage**:
   - Replace all uses of the global connection with context managers
   - Use `get_user_db_connection` for RLS-protected tables
   - Use `get_db_connection` for non-RLS tables

3. **Error Handling**:
   - Implement consistent error handling across all endpoints
   - Add proper logging for all errors
   - Return appropriate HTTP status codes and error messages

4. **API Documentation**:
   - Improve OpenAPI documentation
   - Add examples and descriptions for all endpoints
   - Document authentication requirements clearly
