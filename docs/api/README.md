# API Documentation

## Overview

The AccountDB API provides a RESTful interface for managing Steam accounts, hardware profiles, cards, and user authentication. This document describes the API endpoints, request and response formats, authentication, and error handling.

## Base URL

The base URL for the API is:

```
https://api.accountdb.example.com
```

## Authentication

Most API endpoints require authentication using a JWT token. To authenticate:

1. Get a token using the `/auth/token` endpoint.
2. Include the token in the `Authorization` header as `Bearer {token}`.

### Getting a Token

```http
POST /auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request. In case of an error, the response body will contain an error message and additional details when appropriate.

Example error response:

```json
{
  "detail": "Account not found"
}
```

## API Endpoints

The API provides the following endpoints:

### Authentication

#### Get a JWT Token

```http
POST /auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Register a New User

```http
POST /auth/register
Content-Type: application/json

{
  "username": "new_user",
  "email": "user@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "id": 1,
  "username": "new_user",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": 1609459200
}
```

#### Get Current User Information

```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "id": 1,
  "username": "your_username",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": 1609459200
}
```

### Accounts

#### List Accounts (GET)

```http
GET /accounts/list?limit=100&offset=0&sort_by=acc_id&sort_order=asc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "accounts": [
    {
      "acc_id": "76561199123456789",
      "acc_username": "steamuser1",
      "acc_email_address": "user1@example.com",
      "prime": true,
      "lock": false,
      "perm_lock": false,
      "acc_created_at": 1609459200
    },
    {
      "acc_id": "76561199987654321",
      "acc_username": "steamuser2",
      "acc_email_address": "user2@example.com",
      "prime": false,
      "lock": true,
      "perm_lock": false,
      "acc_created_at": 1609545600
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

#### List Accounts (POST)

```http
POST /accounts/list
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "limit": 100,
  "offset": 0,
  "search": "steam",
  "sort_by": "acc_id",
  "sort_order": "asc",
  "filter_prime": true,
  "filter_lock": false,
  "filter_perm_lock": false
}
```

Response:

```json
{
  "accounts": [
    {
      "acc_id": "76561199123456789",
      "acc_username": "steamuser1",
      "acc_email_address": "user1@example.com",
      "prime": true,
      "lock": false,
      "perm_lock": false,
      "acc_created_at": 1609459200
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### Get Account by Username

```http
GET /accounts/{acc_username}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "account": {
    "acc_id": "76561199123456789",
    "acc_username": "steamuser1",
    "acc_email_address": "user1@example.com",
    "prime": true,
    "lock": false,
    "perm_lock": false,
    "acc_created_at": 1609459200
  }
}
```

#### Create a New Account

```http
POST /accounts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "acc_id": "76561199123456789",
  "acc_username": "steamuser1",
  "acc_password": "password123",
  "acc_email_address": "user1@example.com",
  "acc_email_password": "emailpass123",
  "prime": false,
  "lock": false,
  "perm_lock": false,
  "acc_created_at": null
}
```

Response:

```json
{
  "account": {
    "acc_id": "76561199123456789",
    "acc_username": "steamuser1",
    "acc_email_address": "user1@example.com",
    "prime": false,
    "lock": false,
    "perm_lock": false,
    "acc_created_at": 1609459200
  }
}
```

#### Update an Account

```http
PUT /accounts/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "acc_username": "steamuser1_updated",
  "acc_password": "newpassword123",
  "acc_email_address": "user1_updated@example.com",
  "acc_email_password": "newemailpass123",
  "prime": true,
  "lock": true,
  "perm_lock": false
}
```

Response:

```json
{
  "account": {
    "acc_id": "76561199123456789",
    "acc_username": "steamuser1_updated",
    "acc_email_address": "user1_updated@example.com",
    "prime": true,
    "lock": true,
    "perm_lock": false,
    "acc_created_at": 1609459200
  }
}
```

#### Delete an Account

```http
DELETE /accounts/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```
204 No Content
```

### Hardware

#### List Hardware Profiles

```http
GET /hardware/list?limit=100&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "hardware": [
    {
      "id": 1,
      "acc_id": "76561199123456789",
      "hw_id": "hw_id_1",
      "hw_name": "Hardware 1",
      "hw_type": "Type 1",
      "hw_created_at": 1609459200
    },
    {
      "id": 2,
      "acc_id": "76561199987654321",
      "hw_id": "hw_id_2",
      "hw_name": "Hardware 2",
      "hw_type": "Type 2",
      "hw_created_at": 1609545600
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

#### Get Hardware Profile by ID

```http
GET /hardware/{hw_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "hardware": {
    "id": 1,
    "acc_id": "76561199123456789",
    "hw_id": "hw_id_1",
    "hw_name": "Hardware 1",
    "hw_type": "Type 1",
    "hw_created_at": 1609459200
  }
}
```

#### Create a New Hardware Profile

```http
POST /hardware
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "acc_id": "76561199123456789",
  "hw_id": "hw_id_1",
  "hw_name": "Hardware 1",
  "hw_type": "Type 1"
}
```

Response:

```json
{
  "hardware": {
    "id": 1,
    "acc_id": "76561199123456789",
    "hw_id": "hw_id_1",
    "hw_name": "Hardware 1",
    "hw_type": "Type 1",
    "hw_created_at": 1609459200
  }
}
```

#### Update a Hardware Profile

```http
PUT /hardware/{hw_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "hw_name": "Hardware 1 Updated",
  "hw_type": "Type 1 Updated"
}
```

Response:

```json
{
  "hardware": {
    "id": 1,
    "acc_id": "76561199123456789",
    "hw_id": "hw_id_1",
    "hw_name": "Hardware 1 Updated",
    "hw_type": "Type 1 Updated",
    "hw_created_at": 1609459200
  }
}
```

#### Delete a Hardware Profile

```http
DELETE /hardware/{hw_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```
204 No Content
```

### Cards

#### List Cards

```http
GET /cards/list?limit=100&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "cards": [
    {
      "id": 1,
      "acc_id": "76561199123456789",
      "card_id": "card_id_1",
      "card_name": "Card 1",
      "card_type": "Type 1",
      "card_created_at": 1609459200
    },
    {
      "id": 2,
      "acc_id": "76561199987654321",
      "card_id": "card_id_2",
      "card_name": "Card 2",
      "card_type": "Type 2",
      "card_created_at": 1609545600
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

#### Get Card by ID

```http
GET /cards/{card_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "card": {
    "id": 1,
    "acc_id": "76561199123456789",
    "card_id": "card_id_1",
    "card_name": "Card 1",
    "card_type": "Type 1",
    "card_created_at": 1609459200
  }
}
```

#### Create a New Card

```http
POST /cards
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "acc_id": "76561199123456789",
  "card_id": "card_id_1",
  "card_name": "Card 1",
  "card_type": "Type 1"
}
```

Response:

```json
{
  "card": {
    "id": 1,
    "acc_id": "76561199123456789",
    "card_id": "card_id_1",
    "card_name": "Card 1",
    "card_type": "Type 1",
    "card_created_at": 1609459200
  }
}
```

#### Update a Card

```http
PUT /cards/{card_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "card_name": "Card 1 Updated",
  "card_type": "Type 1 Updated"
}
```

Response:

```json
{
  "card": {
    "id": 1,
    "acc_id": "76561199123456789",
    "card_id": "card_id_1",
    "card_name": "Card 1 Updated",
    "card_type": "Type 1 Updated",
    "card_created_at": 1609459200
  }
}
```

#### Delete a Card

```http
DELETE /cards/{card_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```
204 No Content
```

### Steam Authentication

#### Generate a Steam Guard 2FA Code

```http
GET /steam-auth/generate-code/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "code": "ABCDEF",
  "expires_in": 30
}
```

#### Get Steam Authentication Status

```http
GET /steam-auth/status/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "status": "authenticated",
  "last_login": 1609459200
}
```

### Account Status

#### List Account Statuses

```http
GET /account-status/list?limit=100&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "account_statuses": [
    {
      "id": 1,
      "acc_id": "76561199123456789",
      "status": "active",
      "last_updated": 1609459200
    },
    {
      "id": 2,
      "acc_id": "76561199987654321",
      "status": "inactive",
      "last_updated": 1609545600
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

#### Get Account Status by ID

```http
GET /account-status/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "account_status": {
    "id": 1,
    "acc_id": "76561199123456789",
    "status": "active",
    "last_updated": 1609459200
  }
}
```

#### Create a New Account Status

```http
POST /account-status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "acc_id": "76561199123456789",
  "status": "active"
}
```

Response:

```json
{
  "account_status": {
    "id": 1,
    "acc_id": "76561199123456789",
    "status": "active",
    "last_updated": 1609459200
  }
}
```

#### Update an Account Status

```http
PUT /account-status/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "inactive"
}
```

Response:

```json
{
  "account_status": {
    "id": 1,
    "acc_id": "76561199123456789",
    "status": "inactive",
    "last_updated": 1609459200
  }
}
```

### Upload

#### Upload Accounts for Bulk Creation

```http
POST /upload/accounts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

file=@accounts.csv
```

Response:

```json
{
  "success": true,
  "message": "Accounts uploaded successfully",
  "created": 10,
  "failed": 0
}
```

## OpenAPI Documentation

The API is documented using OpenAPI, providing interactive documentation for API consumers. The OpenAPI documentation is available at:

```
https://api.accountdb.example.com/api/docs
```

The ReDoc documentation is available at:

```
https://api.accountdb.example.com/api/redoc
```

## Conclusion

The AccountDB API provides a comprehensive set of endpoints for managing Steam accounts, hardware profiles, cards, and user authentication. It follows REST principles, provides consistent error handling, and uses JWT-based authentication to ensure that only authorized users can access protected endpoints.

For more detailed information about the API, please refer to the OpenAPI documentation.
