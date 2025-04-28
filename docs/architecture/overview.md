# AccountDB Architecture Overview

## Introduction

AccountDB is a system for managing Steam accounts, hardware profiles, cards, and user authentication. It provides a RESTful API for creating, reading, updating, and deleting these resources, as well as for authenticating users and managing account status.

This document provides an overview of the architecture of the AccountDB system, including its components, data model, and security features.

## System Components

The AccountDB system consists of the following components:

1. **API Server**: A FastAPI application that provides a RESTful API for managing accounts, hardware profiles, cards, and user authentication.
2. **Database**: A PostgreSQL database that stores account, hardware, card, and user data.
3. **Authentication System**: A JWT-based authentication system that provides secure access to the API.
4. **Row-Level Security (RLS)**: A PostgreSQL feature that ensures users can only access their own data.

### API Server

The API server is built using FastAPI, a modern, fast (high-performance) web framework for building APIs with Python. It provides the following features:

- **RESTful API**: The API follows REST principles, providing endpoints for creating, reading, updating, and deleting resources.
- **OpenAPI Documentation**: The API is documented using OpenAPI, providing interactive documentation for API consumers.
- **Request Validation**: The API validates incoming requests, ensuring that they contain the required fields and that the fields have the correct types.
- **Response Serialization**: The API serializes responses, ensuring that they have a consistent format.
- **Error Handling**: The API provides consistent error responses, making it easier for clients to handle errors.
- **Authentication**: The API uses JWT-based authentication, ensuring that only authorized users can access protected endpoints.
- **Authorization**: The API uses role-based access control, ensuring that users can only access resources they are authorized to access.

### Database

The database is built using PostgreSQL, a powerful, open-source object-relational database system. It provides the following features:

- **Data Storage**: The database stores account, hardware, card, and user data.
- **Data Integrity**: The database ensures data integrity through constraints, such as foreign keys and unique constraints.
- **Row-Level Security (RLS)**: The database uses RLS to ensure that users can only access their own data.
- **Transactions**: The database supports transactions, ensuring that operations are atomic, consistent, isolated, and durable (ACID).
- **Indexing**: The database uses indexes to improve query performance.
- **Connection Pooling**: The database uses connection pooling to improve performance and resource utilization.

### Authentication System

The authentication system is built using JWT (JSON Web Tokens), a compact, URL-safe means of representing claims to be transferred between two parties. It provides the following features:

- **User Authentication**: The system authenticates users using their username and password.
- **Token Generation**: The system generates JWT tokens for authenticated users.
- **Token Validation**: The system validates JWT tokens, ensuring that they are valid and have not expired.
- **Role-Based Access Control**: The system uses roles to control access to resources.
- **Password Hashing**: The system hashes passwords, ensuring that they are stored securely.

### Row-Level Security (RLS)

Row-Level Security (RLS) is a PostgreSQL feature that ensures users can only access their own data. It provides the following features:

- **Data Isolation**: RLS ensures that users can only access their own data.
- **Policy Enforcement**: RLS enforces policies at the database level, ensuring that they cannot be bypassed.
- **Role-Based Access**: RLS uses roles to control access to data.
- **Dynamic Policies**: RLS policies can be dynamic, allowing for complex access control rules.

## Data Model

The AccountDB system uses the following data model:

### Users

The `users` table stores information about users of the system. Each user has the following attributes:

- `id`: A unique identifier for the user.
- `username`: The username of the user.
- `email`: The email address of the user.
- `password_hash`: The hashed password of the user.
- `role`: The role of the user (e.g., "user", "admin").
- `is_active`: Whether the user is active.
- `created_at`: The timestamp when the user was created.

### Accounts

The `accounts` table stores information about Steam accounts. Each account has the following attributes:

- `acc_id`: A unique identifier for the account.
- `acc_username`: The username of the account.
- `acc_password`: The password of the account.
- `acc_email_address`: The email address associated with the account.
- `acc_email_password`: The password for the email account.
- `acc_created_at`: The timestamp when the account was created.
- `prime`: Whether the account has Prime status.
- `lock`: Whether the account is locked.
- `perm_lock`: Whether the account is permanently locked.
- `owner_id`: The ID of the user who owns the account.

### Hardware

The `hardware` table stores information about hardware profiles associated with accounts. Each hardware profile has the following attributes:

- `id`: A unique identifier for the hardware profile.
- `acc_id`: The ID of the account associated with the hardware profile.
- `hw_id`: The hardware ID.
- `hw_name`: The name of the hardware.
- `hw_type`: The type of hardware.
- `hw_created_at`: The timestamp when the hardware profile was created.

### Cards

The `cards` table stores information about Steam gift cards. Each card has the following attributes:

- `id`: A unique identifier for the card.
- `acc_id`: The ID of the account associated with the card.
- `card_id`: The card ID.
- `card_name`: The name of the card.
- `card_type`: The type of card.
- `card_created_at`: The timestamp when the card was created.
- `owner_id`: The ID of the user who owns the card.

### Account Status

The `account_status` table stores information about the status of accounts. Each account status has the following attributes:

- `id`: A unique identifier for the account status.
- `acc_id`: The ID of the account.
- `status`: The status of the account (e.g., "active", "inactive", "suspended").
- `last_updated`: The timestamp when the account status was last updated.

## Security

The AccountDB system uses the following security features:

### Authentication

The system uses JWT-based authentication to ensure that only authorized users can access protected endpoints. When a user logs in, the system generates a JWT token that the user can use to access protected endpoints. The token contains the user's ID, username, and role, as well as an expiration time.

### Authorization

The system uses role-based access control to ensure that users can only access resources they are authorized to access. The system has two roles:

- **User**: Users can access their own accounts, hardware profiles, and cards.
- **Admin**: Administrators can access all accounts, hardware profiles, and cards.

### Row-Level Security (RLS)

The system uses PostgreSQL's Row-Level Security (RLS) feature to ensure that users can only access their own data. RLS policies are defined for each table, ensuring that users can only access rows that they own.

### Password Hashing

The system hashes passwords using bcrypt, a secure password hashing algorithm. This ensures that passwords are stored securely and cannot be recovered if the database is compromised.

### HTTPS

The system uses HTTPS to encrypt data in transit, ensuring that sensitive information cannot be intercepted.

### Input Validation

The system validates all input, ensuring that it conforms to expected formats and types. This helps prevent injection attacks and other security vulnerabilities.

### Error Handling

The system provides consistent error responses, making it easier for clients to handle errors. Error responses include a status code, an error message, and additional details when appropriate.

## API Endpoints

The AccountDB API provides the following endpoints:

### Authentication

- `POST /auth/token`: Get a JWT token for authentication.
- `POST /auth/register`: Register a new user.
- `GET /auth/me`: Get information about the current user.

### Accounts

- `GET /accounts/list`: Get a list of accounts.
- `POST /accounts/list`: Get a list of accounts with more complex filtering.
- `GET /accounts/{acc_username}`: Get information about a specific account.
- `POST /accounts`: Create a new account.
- `PUT /accounts/{acc_id}`: Update an existing account.
- `DELETE /accounts/{acc_id}`: Delete an account.

### Hardware

- `GET /hardware/list`: Get a list of hardware profiles.
- `GET /hardware/{hw_id}`: Get information about a specific hardware profile.
- `POST /hardware`: Create a new hardware profile.
- `PUT /hardware/{hw_id}`: Update an existing hardware profile.
- `DELETE /hardware/{hw_id}`: Delete a hardware profile.

### Cards

- `GET /cards/list`: Get a list of cards.
- `GET /cards/{card_id}`: Get information about a specific card.
- `POST /cards`: Create a new card.
- `PUT /cards/{card_id}`: Update an existing card.
- `DELETE /cards/{card_id}`: Delete a card.

### Steam Authentication

- `GET /steam-auth/generate-code/{acc_id}`: Generate a Steam Guard 2FA code for an account.
- `GET /steam-auth/status/{acc_id}`: Get the Steam authentication status for an account.

### Account Status

- `GET /account-status/list`: Get a list of account statuses.
- `GET /account-status/{acc_id}`: Get the status of a specific account.
- `POST /account-status`: Create a new account status.
- `PUT /account-status/{acc_id}`: Update the status of an account.

### Upload

- `POST /upload/accounts`: Upload a file containing account information for bulk creation.

## Conclusion

The AccountDB system provides a secure and efficient way to manage Steam accounts, hardware profiles, cards, and user authentication. Its architecture is designed to ensure data integrity, security, and performance, while providing a user-friendly API for clients.

For more detailed information about specific components, please refer to the following documents:

- [API Documentation](../api/README.md)
- [Database Schema](../database/schema.md)
- [Authentication System](../auth/README.md)
- [Row-Level Security](../security/rls.md)
- [Error Handling](../error-handling/README.md)
