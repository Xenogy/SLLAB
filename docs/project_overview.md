# AccountDB - Project Overview

## Introduction

AccountDB is a comprehensive web application designed to manage, track, and secure accounts for various services, with a focus on Steam accounts and virtual machine management through Proxmox integration. It provides a centralized platform for users to manage their accounts and virtual machines, with proper security controls and user separation.

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
   - Login attempt tracking and account lockout protection

3. **Security**
   - Row-Level Security (RLS) to ensure users can only access their own data
   - Secure storage of sensitive information
   - Authentication and authorization controls
   - Audit logging for security events
   - Token blacklisting for secure logout

4. **Integration**
   - Steam authentication support
   - Hardware profile management
   - Card management
   - Proxmox integration for VM management
   - Windows VM Agent for monitoring and automation

5. **Virtual Machine Management**
   - Create, read, update, and delete virtual machines
   - Monitor virtual machine status
   - Manage virtual machine access
   - Whitelist management for Proxmox nodes

6. **Monitoring and Automation**
   - Windows VM Agent for monitoring log files
   - Automated actions based on monitored events
   - Performance monitoring for the application
   - Health checks for the database and API

## Technology Stack

- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: Next.js (React)
- **Database**: PostgreSQL with Row-Level Security
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker and Docker Compose
- **VM Management**: Proxmox VE API
- **Monitoring**: Custom monitoring modules
- **Windows Agent**: Python-based agent with PowerShell integration

## System Components

1. **API Server**
   - FastAPI application providing RESTful endpoints
   - JWT-based authentication
   - Role-based access control
   - Error handling and logging

2. **Database**
   - PostgreSQL database with Row-Level Security
   - Normalized schema for efficient data storage
   - Indexes for performance optimization
   - Connection pooling for efficient resource usage

3. **Frontend**
   - Next.js web application
   - Responsive design for desktop and mobile
   - Dark/light mode support
   - Interactive data tables and charts

4. **Proxmox Host Agent**
   - Synchronizes VM information with AccountDB
   - Runs on Proxmox host nodes
   - Provides REST API for manual synchronization
   - Scheduled updates to keep information current

5. **Windows VM Agent**
   - Monitors log files for specific patterns
   - Executes PowerShell scripts based on events
   - Communicates with AccountDB API
   - Configurable through YAML files

## Key Features

1. **Secure Account Management**
   - Encrypted storage of sensitive information
   - Row-Level Security to ensure data isolation
   - Role-based access control
   - Audit logging for security events

2. **Virtual Machine Integration**
   - Proxmox integration for VM management
   - VM status monitoring
   - VM access control
   - Whitelist management for Proxmox nodes

3. **Windows VM Automation**
   - Log file monitoring
   - Event-based script execution
   - Dynamic API data retrieval
   - Configurable actions and triggers

4. **Performance Optimization**
   - Query optimization
   - Connection pooling
   - Caching
   - Asynchronous processing

5. **Monitoring and Reliability**
   - Health checks
   - Performance monitoring
   - Automatic recovery from common issues
   - Alerting for critical events

## Key Challenges

1. **Data Isolation**: Ensuring proper separation of user data
2. **Security**: Protecting sensitive account information
3. **Performance**: Handling large numbers of accounts and VMs efficiently
4. **Integration**: Seamless integration with Proxmox and Windows VMs
5. **Usability**: Providing a user-friendly interface for account and VM management

## Current Status

The system is fully operational with all core features implemented. Recent additions include:

1. **Windows VM Agent**: For monitoring and automation on Windows VMs
2. **Proxmox Integration**: For managing virtual machines
3. **Enhanced Security**: Improved Row-Level Security implementation
4. **Performance Improvements**: Query optimization and caching
5. **User Interface Enhancements**: Improved dashboard and VM management interface

This document provides a high-level overview of the project. For more detailed information, see the architecture, API, database, and component documentation.
