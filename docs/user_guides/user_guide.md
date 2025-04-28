# AccountDB User Guide

## Introduction

Welcome to AccountDB, a comprehensive system for managing Steam accounts, hardware profiles, cards, and user authentication. This guide will help you understand how to use the AccountDB system effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Managing Accounts](#managing-accounts)
4. [Managing Hardware Profiles](#managing-hardware-profiles)
5. [Managing Cards](#managing-cards)
6. [Steam Authentication](#steam-authentication)
7. [Account Status](#account-status)
8. [Bulk Operations](#bulk-operations)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

## Getting Started

### System Requirements

To use the AccountDB API, you need:

- A modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- API credentials (username and password)

### Accessing the API

The AccountDB API is accessible at:

```
https://api.accountdb.example.com
```

For API documentation, visit:

```
https://api.accountdb.example.com/api/docs
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

### Token Expiration

Tokens expire after 24 hours. You'll need to get a new token when the current one expires.

### User Roles

The system has two user roles:

- **User**: Can access and manage their own accounts, hardware profiles, and cards.
- **Admin**: Can access and manage all accounts, hardware profiles, and cards.

## Managing Accounts

### Listing Accounts

You can list accounts using the `/accounts/list` endpoint:

```http
GET /accounts/list?limit=100&offset=0&sort_by=acc_id&sort_order=asc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Pagination

The list endpoint supports pagination with the following parameters:

- `limit`: Maximum number of accounts to return (default: 100)
- `offset`: Number of accounts to skip (default: 0)

#### Sorting

You can sort the results using the following parameters:

- `sort_by`: Field to sort by (default: acc_id)
- `sort_order`: Sort order (asc or desc) (default: asc)

#### Filtering

You can filter the results using the following parameters:

- `search`: Search term to filter accounts by username or email
- `filter_prime`: Filter by prime status (true/false)
- `filter_lock`: Filter by lock status (true/false)
- `filter_perm_lock`: Filter by permanent lock status (true/false)

#### Cursor-Based Pagination

For better performance with large datasets, you can use cursor-based pagination:

```http
GET /accounts/list/cursor?limit=100&sort_by=acc_id&sort_order=asc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The response includes a `next_cursor` that you can use for the next page:

```http
GET /accounts/list/cursor?cursor=eyJhY2NfaWQiOiI3NjU2MTE5OTEyMzQ1Njc4OSJ9&limit=100
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Field Selection

You can specify which fields to include in the response:

```http
GET /accounts/list/fields?fields=acc_id,acc_username,acc_email_address
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Streaming

For large datasets, you can stream the results:

```http
GET /accounts/list/stream?limit=1000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting an Account

You can get information about a specific account using the `/accounts/{acc_username}` endpoint:

```http
GET /accounts/{acc_username}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
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

### Deleting an Account

You can delete an account using the `/accounts/{acc_id}` endpoint:

```http
DELETE /accounts/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Managing Hardware Profiles

### Listing Hardware Profiles

You can list hardware profiles using the `/hardware/list` endpoint:

```http
GET /hardware/list?limit=100&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting a Hardware Profile

You can get information about a specific hardware profile using the `/hardware/{hw_id}` endpoint:

```http
GET /hardware/{hw_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
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

### Deleting a Hardware Profile

You can delete a hardware profile using the `/hardware/{hw_id}` endpoint:

```http
DELETE /hardware/{hw_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Managing Cards

### Listing Cards

You can list cards using the `/cards/list` endpoint:

```http
GET /cards/list?limit=100&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting a Card

You can get information about a specific card using the `/cards/{card_id}` endpoint:

```http
GET /cards/{card_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
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

### Deleting a Card

You can delete a card using the `/cards/{card_id}` endpoint:

```http
DELETE /cards/{card_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Steam Authentication

### Generating a Steam Guard 2FA Code

You can generate a Steam Guard 2FA code using the `/steam-auth/generate-code/{acc_id}` endpoint:

```http
GET /steam-auth/generate-code/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting Steam Authentication Status

You can get the Steam authentication status using the `/steam-auth/status/{acc_id}` endpoint:

```http
GET /steam-auth/status/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Account Status

### Listing Account Statuses

You can list account statuses using the `/account-status/list` endpoint:

```http
GET /account-status/list?limit=100&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting Account Status

You can get the status of a specific account using the `/account-status/{acc_id}` endpoint:

```http
GET /account-status/{acc_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
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

## Bulk Operations

### Uploading Accounts for Bulk Creation

You can upload a file containing account information for bulk creation using the `/upload/accounts` endpoint:

```http
POST /upload/accounts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

file=@accounts.csv
```

The CSV file should have the following format:

```csv
acc_id,acc_username,acc_password,acc_email_address,acc_email_password,prime,lock,perm_lock
76561199123456789,steamuser1,password123,user1@example.com,emailpass123,true,false,false
76561199987654321,steamuser2,password456,user2@example.com,emailpass456,false,true,false
```

## Troubleshooting

### Common Issues

#### Authentication Issues

If you encounter authentication issues, check the following:

- Make sure you are using a valid JWT token.
- Make sure the token has not expired.
- Make sure the token has the necessary permissions.

#### API Errors

If you encounter API errors, check the following:

- Check the API request parameters.
- Check the API request headers.
- Check the API request body.
- Check the API response status code.
- Check the API response body.

### Error Codes

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK`: The request was successful.
- `201 Created`: The resource was created successfully.
- `204 No Content`: The request was successful, but there is no content to return.
- `400 Bad Request`: The request was invalid.
- `401 Unauthorized`: Authentication is required.
- `403 Forbidden`: The authenticated user does not have permission to access the requested resource.
- `404 Not Found`: The requested resource was not found.
- `422 Unprocessable Entity`: The request was well-formed but was unable to be followed due to semantic errors.
- `429 Too Many Requests`: The user has sent too many requests in a given amount of time.
- `500 Internal Server Error`: An error occurred on the server.

## FAQ

### General Questions

#### What is AccountDB?

AccountDB is a system for managing Steam accounts, hardware profiles, cards, and user authentication.

#### How do I get access to AccountDB?

Contact your system administrator to get access to AccountDB.

### Account Management

#### How do I create a new account?

You can create a new account using the `/accounts` endpoint. See the [Creating an Account](#creating-an-account) section for details.

#### How do I update an account?

You can update an account using the `/accounts/{acc_id}` endpoint. See the [Updating an Account](#updating-an-account) section for details.

#### How do I delete an account?

You can delete an account using the `/accounts/{acc_id}` endpoint. See the [Deleting an Account](#deleting-an-account) section for details.

### Hardware Management

#### How do I create a new hardware profile?

You can create a new hardware profile using the `/hardware` endpoint. See the [Creating a Hardware Profile](#creating-a-hardware-profile) section for details.

#### How do I update a hardware profile?

You can update a hardware profile using the `/hardware/{hw_id}` endpoint. See the [Updating a Hardware Profile](#updating-a-hardware-profile) section for details.

#### How do I delete a hardware profile?

You can delete a hardware profile using the `/hardware/{hw_id}` endpoint. See the [Deleting a Hardware Profile](#deleting-a-hardware-profile) section for details.

### Card Management

#### How do I create a new card?

You can create a new card using the `/cards` endpoint. See the [Creating a Card](#creating-a-card) section for details.

#### How do I update a card?

You can update a card using the `/cards/{card_id}` endpoint. See the [Updating a Card](#updating-a-card) section for details.

#### How do I delete a card?

You can delete a card using the `/cards/{card_id}` endpoint. See the [Deleting a Card](#deleting-a-card) section for details.

### Steam Authentication

#### How do I generate a Steam Guard 2FA code?

You can generate a Steam Guard 2FA code using the `/steam-auth/generate-code/{acc_id}` endpoint. See the [Generating a Steam Guard 2FA Code](#generating-a-steam-guard-2fa-code) section for details.

#### How do I check the Steam authentication status?

You can check the Steam authentication status using the `/steam-auth/status/{acc_id}` endpoint. See the [Getting Steam Authentication Status](#getting-steam-authentication-status) section for details.

### Account Status

#### How do I check the status of an account?

You can check the status of an account using the `/account-status/{acc_id}` endpoint. See the [Getting Account Status](#getting-account-status) section for details.

#### How do I update the status of an account?

You can update the status of an account using the `/account-status/{acc_id}` endpoint. See the [Updating Account Status](#updating-account-status) section for details.

### Bulk Operations

#### How do I upload accounts for bulk creation?

You can upload accounts for bulk creation using the `/upload/accounts` endpoint. See the [Uploading Accounts for Bulk Creation](#uploading-accounts-for-bulk-creation) section for details.
