# Security Model

## Overview

The security model of the Account Management System is designed to protect sensitive account information while providing appropriate access to authorized users. It implements multiple layers of security to ensure data confidentiality, integrity, and availability.

## Authentication

### User Authentication

1. **JWT-based Authentication**
   - JSON Web Tokens (JWT) are used for authenticating users
   - Tokens include user ID, username, and role information
   - Tokens are signed with a secret key to prevent tampering
   - Tokens have a configurable expiration time

2. **Login Process**
   - Users provide username and password
   - Password is verified against hashed value in database
   - Upon successful verification, a JWT token is generated and returned
   - Token is stored in localStorage on the client side

3. **Public Endpoints**
   - Some endpoints (e.g., `/auth/signup-status`, `/auth/register`) are public and don't require authentication
   - All other endpoints require a valid JWT token

## Authorization

### Role-Based Access Control

1. **User Roles**
   - **Admin**: Full access to all accounts and system features
   - **User**: Access only to their own accounts and limited features

2. **Permission Model**
   - Admins can view, create, update, and delete any account
   - Regular users can only view, create, update, and delete their own accounts

## Data Protection

### Row-Level Security (RLS)

1. **Database-Level Security**
   - PostgreSQL Row-Level Security (RLS) policies restrict data access
   - Each database table has RLS policies that filter rows based on user ID
   - Session variables (`app.current_user_id` and `app.current_user_role`) control access

2. **RLS Policies**
   - **User Policy**: Users can only access rows where `owner_id` matches their user ID
   - **Admin Policy**: Admins can access all rows regardless of `owner_id`

3. **Implementation**
   - RLS is enabled on `accounts`, `hardware`, and `cards` tables
   - Each database connection sets the appropriate session variables
   - All database operations respect RLS policies

### Data Ownership

1. **Owner Assignment**
   - Each record in protected tables has an `owner_id` field
   - When a user creates a record, their user ID is automatically assigned as the owner
   - Ownership cannot be transferred except by admins

## Secure Communication

1. **HTTPS**
   - All API communication should use HTTPS to encrypt data in transit
   - API endpoints should reject non-HTTPS connections in production

2. **Secure Headers**
   - Appropriate security headers should be set to prevent common web vulnerabilities
   - CORS (Cross-Origin Resource Sharing) should be properly configured

## Current Issues and Improvement Areas

1. **RLS Implementation**
   - Non-admin users can currently see accounts they don't own
   - Database connection management is inconsistent
   - Some endpoints bypass RLS by using the global connection

2. **Token Management**
   - Token storage in localStorage is vulnerable to XSS attacks
   - No token refresh mechanism is implemented
   - No token revocation capability

3. **Password Security**
   - Password strength requirements could be improved
   - No multi-factor authentication support

## Recommended Security Improvements

1. **Fix RLS Implementation**
   - Ensure all database operations use the user-specific connection with RLS
   - Verify RLS policies are correctly defined and applied
   - Add comprehensive testing for RLS

2. **Enhance Token Security**
   - Consider using HTTP-only cookies instead of localStorage
   - Implement token refresh mechanism
   - Add token revocation capability

3. **Strengthen Authentication**
   - Add multi-factor authentication support
   - Implement password strength requirements
   - Add account lockout after failed login attempts

4. **Improve Audit Logging**
   - Log all security-relevant events
   - Implement a secure audit trail
   - Add monitoring and alerting for suspicious activities
