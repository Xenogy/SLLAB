# Account Management System - Project Overview

## Introduction

The Account Management System is a web application designed to manage, track, and secure accounts for various services. It provides a centralized platform for users to manage their accounts, with proper security controls and user separation.

## Core Capabilities

1. **Account Management**
   - Store and manage account credentials securely
   - Track account status (locked, prime, etc.)
   - Associate accounts with specific users
   - Provide secure access to account details

2. **User Management**
   - User registration and authentication
   - Role-based access control (admin, regular user)
   - User profile management

3. **Security**
   - Row-Level Security (RLS) to ensure users can only access their own data
   - Secure storage of sensitive information
   - Authentication and authorization controls
   - Audit logging for security events

4. **Integration**
   - Steam authentication support
   - Hardware profile management
   - Card management

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (React)
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker

## Key Challenges

1. **Data Isolation**: Ensuring proper separation of user data
2. **Security**: Protecting sensitive account information
3. **Performance**: Handling large numbers of accounts efficiently
4. **Usability**: Providing a user-friendly interface for account management

## Current Issues

1. **Row-Level Security (RLS)**: Non-admin users can see accounts they don't own
2. **Authentication Flow**: Issues with public endpoints requiring authentication
3. **Database Connection Management**: Inconsistent use of connection context managers

This document provides a high-level overview of the project. For more detailed information, see the architecture, requirements, and security model documents.
