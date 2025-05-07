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

### API Key Authentication

Some endpoints, particularly those used by Proxmox nodes and Windows VM agents, use API key authentication instead of JWT tokens. API keys are managed through the `/settings/api-keys` endpoints and can be of different types:

- **User API Keys**: Used for general API access by users
- **Proxmox Node API Keys**: Used by Proxmox nodes to authenticate with the API
- **Windows VM API Keys**: Used by Windows VM agents to authenticate with the API

API keys are passed as a query parameter or in the request body, depending on the endpoint.

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

### Timeseries

#### List Available Metrics

```http
GET /timeseries/metrics
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "categories": [
    {
      "id": 1,
      "name": "system",
      "description": "System-wide metrics like CPU, memory, and disk usage",
      "metrics": [
        {
          "id": 1,
          "name": "cpu_usage",
          "display_name": "CPU Usage",
          "description": "System CPU usage percentage",
          "unit": "%",
          "data_type": "float"
        },
        {
          "id": 2,
          "name": "memory_usage",
          "display_name": "Memory Usage",
          "description": "System memory usage percentage",
          "unit": "%",
          "data_type": "float"
        }
      ]
    },
    {
      "id": 2,
      "name": "vm",
      "description": "Virtual machine metrics like status, CPU, and memory usage",
      "metrics": [
        {
          "id": 7,
          "name": "vm_count",
          "display_name": "VM Count",
          "description": "Total number of VMs",
          "unit": "count",
          "data_type": "integer"
        },
        {
          "id": 11,
          "name": "vm_cpu_usage",
          "display_name": "VM CPU Usage",
          "description": "VM CPU usage percentage",
          "unit": "%",
          "data_type": "float"
        }
      ]
    }
  ]
}
```

#### Get Metric Data

```http
GET /timeseries/data/{metric_name}?start_time=2023-01-01T00:00:00Z&end_time=2023-01-02T00:00:00Z&entity_type=system&entity_id=system&period=hourly
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "metric": "cpu_usage",
  "period": "hourly",
  "start_time": "2023-01-01T00:00:00Z",
  "end_time": "2023-01-02T00:00:00Z",
  "data": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "end_time": "2023-01-01T01:00:00Z",
      "min": 10.5,
      "max": 45.2,
      "avg": 25.7,
      "sum": 1542.0,
      "count": 60,
      "entity_type": "system",
      "entity_id": "system"
    },
    {
      "timestamp": "2023-01-01T01:00:00Z",
      "end_time": "2023-01-01T02:00:00Z",
      "min": 12.1,
      "max": 48.3,
      "avg": 27.9,
      "sum": 1674.0,
      "count": 60,
      "entity_type": "system",
      "entity_id": "system"
    }
  ],
  "count": 2
}
```

#### Get Latest Metric Value

```http
GET /timeseries/latest/{metric_name}?entity_type=system&entity_id=system
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "metric": "cpu_usage",
  "value": 32.5,
  "timestamp": "2023-01-02T12:34:56Z",
  "entity_type": "system",
  "entity_id": "system"
}
```

#### Get Metric Statistics

```http
GET /timeseries/statistics/{metric_name}?start_time=2023-01-01T00:00:00Z&end_time=2023-01-02T00:00:00Z&entity_type=system&entity_id=system
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "metric": "cpu_usage",
  "start_time": "2023-01-01T00:00:00Z",
  "end_time": "2023-01-02T00:00:00Z",
  "entity_type": "system",
  "entity_id": "system",
  "statistics": {
    "min": 10.5,
    "max": 85.2,
    "avg": 35.7,
    "sum": 30888.0,
    "count": 864
  }
}
```

#### Get System Overview

```http
GET /timeseries/system/overview?period=hourly&duration=day
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "period": "hourly",
  "duration": "day",
  "start_time": "2023-01-01T00:00:00Z",
  "end_time": "2023-01-02T00:00:00Z",
  "metrics": {
    "cpu_usage": {
      "latest": 32.5,
      "timestamp": "2023-01-02T12:34:56Z",
      "statistics": {
        "min": 10.5,
        "max": 85.2,
        "avg": 35.7,
        "sum": 30888.0,
        "count": 864
      },
      "data": [
        {
          "timestamp": "2023-01-01T00:00:00Z",
          "value": 25.7
        },
        {
          "timestamp": "2023-01-01T01:00:00Z",
          "value": 27.9
        }
      ]
    },
    "memory_usage": {
      "latest": 45.8,
      "timestamp": "2023-01-02T12:34:56Z",
      "statistics": {
        "min": 30.2,
        "max": 65.3,
        "avg": 48.5,
        "sum": 41904.0,
        "count": 864
      },
      "data": [
        {
          "timestamp": "2023-01-01T00:00:00Z",
          "value": 42.3
        },
        {
          "timestamp": "2023-01-01T01:00:00Z",
          "value": 44.1
        }
      ]
    }
  }
}
```

#### Get VM Overview

```http
GET /timeseries/vm/overview?vm_id=1&period=hourly&duration=day
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "period": "hourly",
  "duration": "day",
  "start_time": "2023-01-01T00:00:00Z",
  "end_time": "2023-01-02T00:00:00Z",
  "vms": [
    {
      "id": 1,
      "vmid": 101,
      "name": "VM-01",
      "status": "running",
      "metrics": {
        "vm_cpu_usage": {
          "latest": 45.2,
          "timestamp": "2023-01-02T12:34:56Z",
          "statistics": {
            "min": 15.3,
            "max": 95.2,
            "avg": 42.7,
            "sum": 36892.8,
            "count": 864
          },
          "data": [
            {
              "timestamp": "2023-01-01T00:00:00Z",
              "value": 38.5
            },
            {
              "timestamp": "2023-01-01T01:00:00Z",
              "value": 42.1
            }
          ]
        },
        "vm_memory_usage": {
          "latest": 62.3,
          "timestamp": "2023-01-02T12:34:56Z",
          "statistics": {
            "min": 45.2,
            "max": 78.3,
            "avg": 65.8,
            "sum": 56851.2,
            "count": 864
          },
          "data": [
            {
              "timestamp": "2023-01-01T00:00:00Z",
              "value": 58.7
            },
            {
              "timestamp": "2023-01-01T01:00:00Z",
              "value": 62.4
            }
          ]
        }
      }
    }
  ]
}

#### Generate Sample Data (Admin Only)

```http
POST /timeseries/generate-sample-data
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "days": 7
}
```

Response:

```json
{
  "status": "success",
  "message": "Generated sample data for 7 days",
  "start_time": "2023-01-01T00:00:00Z",
  "end_time": "2023-01-08T00:00:00Z"
}
```

### API Keys

#### List API Keys

```http
GET /settings/api-keys?limit=10&offset=0&include_revoked=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "api_keys": [
    {
      "id": 1,
      "user_id": 1,
      "key_name": "My API Key",
      "api_key_prefix": "abcd1234",
      "scopes": ["read", "write"],
      "expires_at": null,
      "last_used_at": "2023-01-01T12:00:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "revoked": false,
      "key_type": "user",
      "resource_id": null
    }
  ],
  "total": 1
}
```

#### Create an API Key

```http
POST /settings/api-keys
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "key_name": "My API Key",
  "expires_in_days": 30,
  "scopes": ["read", "write"],
  "key_type": "user",
  "resource_id": null
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "key_name": "My API Key",
  "api_key_prefix": "abcd1234",
  "api_key": "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx",
  "scopes": ["read", "write"],
  "expires_at": "2023-02-01T00:00:00Z",
  "last_used_at": null,
  "created_at": "2023-01-01T00:00:00Z",
  "revoked": false,
  "key_type": "user",
  "resource_id": null
}
```

#### Get an API Key

```http
GET /settings/api-keys/{key_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "key_name": "My API Key",
  "api_key_prefix": "abcd1234",
  "scopes": ["read", "write"],
  "expires_at": "2023-02-01T00:00:00Z",
  "last_used_at": null,
  "created_at": "2023-01-01T00:00:00Z",
  "revoked": false,
  "key_type": "user",
  "resource_id": null
}
```

#### Revoke an API Key

```http
DELETE /settings/api-keys/{key_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "key_name": "My API Key",
  "api_key_prefix": "abcd1234",
  "scopes": ["read", "write"],
  "expires_at": "2023-02-01T00:00:00Z",
  "last_used_at": null,
  "created_at": "2023-01-01T00:00:00Z",
  "revoked": true,
  "key_type": "user",
  "resource_id": null
}
```

#### List Resource API Keys

```http
GET /settings/resource-api-keys?resource_type=proxmox_node&resource_id=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "api_keys": [
    {
      "id": 2,
      "user_id": 1,
      "key_name": "Proxmox Node 1",
      "api_key_prefix": "efgh5678",
      "scopes": ["read", "write"],
      "expires_at": null,
      "last_used_at": "2023-01-01T12:00:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "revoked": false,
      "key_type": "proxmox_node",
      "resource_id": 1
    }
  ],
  "total": 1
}
```

#### Create a Resource API Key

```http
POST /settings/resource-api-keys
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "resource_type": "proxmox_node",
  "resource_id": 1
}
```

Response:

```json
{
  "id": 2,
  "user_id": 1,
  "key_name": "Proxmox Node 1",
  "api_key_prefix": "efgh5678",
  "api_key": "efgh5678ijkl9012mnop3456qrst7890uvwxabcd1234",
  "scopes": ["read", "write"],
  "expires_at": null,
  "last_used_at": null,
  "created_at": "2023-01-01T00:00:00Z",
  "revoked": false,
  "key_type": "proxmox_node",
  "resource_id": 1
}
```

### Windows VM Agent

#### Get Account Configuration

```http
GET /windows-vm-agent/account-config?vm_id=TEST_VM&account_id=test123&api_key=your_api_key
```

Response:

```json
{
  "account_id": "test123",
  "vm_id": "TEST_VM",
  "proxy_server": "http://proxy.example.com:8080",
  "proxy_bypass": "localhost,127.0.0.1",
  "additional_settings": {
    "setting1": "value1",
    "setting2": "value2"
  }
}
```

#### Update Agent Status

```http
POST /windows-vm-agent/status?api_key=your_api_key
Content-Type: application/json

{
  "vm_id": "TEST_VM",
  "status": "running",
  "ip_address": "192.168.1.100",
  "cpu_usage_percent": 25.5,
  "memory_usage_percent": 45.2,
  "disk_usage_percent": 65.8,
  "uptime_seconds": 3600
}
```

Response:

```json
{
  "success": true,
  "message": "Agent status updated successfully"
}
```

#### Register Agent

```http
POST /windows-vm-agent/register?vm_id=TEST_VM&vm_name=Test%20VM
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "vm_id": "TEST_VM",
  "api_key": "f6Nk0DUz0D4nlo9mulQ4fI_VHJXnvcj4zuo3fOTAQPA",
  "message": "Agent registered successfully"
}
```

#### Send Logs

```http
POST /windows-vm-agent/logs?api_key=your_api_key
Content-Type: application/json

{
  "message": "Agent started successfully",
  "level": "INFO",
  "category": "windows_vm_agent",
  "source": "windows_vm_agent",
  "details": {
    "vm_info": {
      "vm_identifier": "TEST_VM",
      "hostname": "WIN-TEST-VM",
      "platform": "Windows",
      "platform_version": "10.0.19044"
    }
  },
  "entity_type": "vm",
  "entity_id": "TEST_VM",
  "timestamp": "2025-05-05T17:18:39.084Z"
}
```

Response:

```json
{
  "success": true,
  "message": "Log entry created successfully"
}
```

#### Get Agent Status

```http
GET /windows-vm-agent/status/{vm_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "vm_id": "TEST_VM",
  "vm_name": "Test VM",
  "status": "running",
  "ip_address": "192.168.1.100",
  "cpu_usage_percent": 25.5,
  "memory_usage_percent": 45.2,
  "disk_usage_percent": 65.8,
  "uptime_seconds": 3600,
  "last_seen": "2025-05-05T17:18:39.084Z",
  "created_at": "2025-05-01T12:00:00.000Z",
  "updated_at": "2025-05-05T17:18:39.084Z"
}
```

#### List Agents

```http
GET /windows-vm-agent/agents?limit=10&offset=0&status=running
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:

```json
{
  "agents": [
    {
      "vm_id": "TEST_VM",
      "vm_name": "Test VM",
      "status": "running",
      "ip_address": "192.168.1.100",
      "cpu_usage_percent": 25.5,
      "memory_usage_percent": 45.2,
      "disk_usage_percent": 65.8,
      "uptime_seconds": 3600,
      "last_seen": "2025-05-05T17:18:39.084Z",
      "created_at": "2025-05-01T12:00:00.000Z",
      "updated_at": "2025-05-05T17:18:39.084Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## Conclusion

The AccountDB API provides a comprehensive set of endpoints for managing Steam accounts, hardware profiles, cards, user authentication, virtual machines, and timeseries data for performance metrics and statistics. It follows REST principles, provides consistent error handling, and uses JWT-based authentication to ensure that only authorized users can access protected endpoints.

The API also supports API key authentication for specific resources like Proxmox nodes and Windows VM agents, providing a flexible and secure way to authenticate different types of clients.

For more detailed information about the API, please refer to the OpenAPI documentation.
