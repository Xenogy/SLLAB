# User Guide

## Introduction

This guide is intended for users of the AccountDB API. It provides information about how to use the API to manage Steam accounts, hardware profiles, cards, and user authentication.

## Getting Started

### Authentication

Most API endpoints require authentication using a JWT token. To authenticate:

1. Get a token using the `/auth/token` endpoint.
2. Include the token in the `Authorization` header as `Bearer {token}`.

#### Getting a Token

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

### Making API Requests

Once you have a token, you can make API requests by including the token in the `Authorization` header:

```http
GET /accounts/list
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Managing Accounts

### Listing Accounts

You can list accounts using the `/accounts/list` endpoint:

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

You can also use the POST method for more complex filtering:

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

### Getting an Account

You can get information about a specific account using the `/accounts/{acc_username}` endpoint:

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

### Creating an Account

You can create a new account using the `/accounts` endpoint:

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

### Updating an Account

You can update an account using the `/accounts/{acc_id}` endpoint:

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

### Deleting an Account

You can delete an account using the `/accounts/{acc_id}` endpoint:

```http
DELETE /accounts/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```
204 No Content
```

## Managing Hardware Profiles

### Listing Hardware Profiles

You can list hardware profiles using the `/hardware/list` endpoint:

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

### Getting a Hardware Profile

You can get information about a specific hardware profile using the `/hardware/{hw_id}` endpoint:

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

### Creating a Hardware Profile

You can create a new hardware profile using the `/hardware` endpoint:

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

### Updating a Hardware Profile

You can update a hardware profile using the `/hardware/{hw_id}` endpoint:

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

### Deleting a Hardware Profile

You can delete a hardware profile using the `/hardware/{hw_id}` endpoint:

```http
DELETE /hardware/{hw_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```
204 No Content
```

## Managing Cards

### Listing Cards

You can list cards using the `/cards/list` endpoint:

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

### Getting a Card

You can get information about a specific card using the `/cards/{card_id}` endpoint:

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

### Creating a Card

You can create a new card using the `/cards` endpoint:

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

### Updating a Card

You can update a card using the `/cards/{card_id}` endpoint:

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

### Deleting a Card

You can delete a card using the `/cards/{card_id}` endpoint:

```http
DELETE /cards/{card_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```
204 No Content
```

## Steam Authentication

### Generating a Steam Guard 2FA Code

You can generate a Steam Guard 2FA code using the `/steam-auth/generate-code/{acc_id}` endpoint:

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

### Getting Steam Authentication Status

You can get the Steam authentication status using the `/steam-auth/status/{acc_id}` endpoint:

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

## Account Status

### Listing Account Statuses

You can list account statuses using the `/account-status/list` endpoint:

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

### Getting Account Status

You can get the status of a specific account using the `/account-status/{acc_id}` endpoint:

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

### Creating Account Status

You can create a new account status using the `/account-status` endpoint:

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

### Updating Account Status

You can update the status of an account using the `/account-status/{acc_id}` endpoint:

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

## Bulk Operations

### Uploading Accounts for Bulk Creation

You can upload a file containing account information for bulk creation using the `/upload/accounts` endpoint:

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

The CSV file should have the following format:

```csv
acc_id,acc_username,acc_password,acc_email_address,acc_email_password,prime,lock,perm_lock
76561199123456789,steamuser1,password123,user1@example.com,emailpass123,true,false,false
76561199987654321,steamuser2,password456,user2@example.com,emailpass456,false,true,false
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request. In case of an error, the response body will contain an error message and additional details when appropriate.

Example error response:

```json
{
  "detail": "Account not found"
}
```

Common error status codes:

- `400 Bad Request`: The request was invalid.
- `401 Unauthorized`: Authentication is required.
- `403 Forbidden`: The authenticated user does not have permission to access the requested resource.
- `404 Not Found`: The requested resource was not found.
- `422 Unprocessable Entity`: The request was well-formed but was unable to be followed due to semantic errors.
- `500 Internal Server Error`: An error occurred on the server.

## Conclusion

This guide provides information about how to use the AccountDB API to manage Steam accounts, hardware profiles, cards, and user authentication. If you have any questions or need further assistance, please contact the API administrators.
