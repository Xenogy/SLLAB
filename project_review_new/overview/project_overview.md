# AccountDB Project Overview

## Project Purpose

AccountDB is a comprehensive system designed to manage accounts, hardware, virtual machines, and Proxmox nodes. It provides a centralized platform for tracking and managing various IT resources with a focus on security and multi-user support.

## Key Components

### Backend

The backend is built using FastAPI, a modern, high-performance web framework for building APIs with Python. It provides RESTful endpoints for managing all resources in the system.

**Key Features:**
- RESTful API endpoints for all resources
- JWT-based authentication
- Row-Level Security (RLS) for data isolation
- Integration with Proxmox API

**Technologies:**
- FastAPI
- PostgreSQL
- JWT for authentication
- Pydantic for data validation

### Frontend

The frontend is built using Next.js, a React framework that enables server-side rendering and static site generation. It provides a user-friendly interface for interacting with the API.

**Key Features:**
- Dashboard for resource overview
- Management interfaces for accounts, hardware, VMs, and Proxmox nodes
- Responsive design
- Authentication and authorization

**Technologies:**
- Next.js
- React
- Tailwind CSS
- ShadcnUI components

### Database

The database is PostgreSQL with Row-Level Security (RLS) implemented to ensure data isolation between users.

**Key Features:**
- Row-Level Security (RLS) for data isolation
- Comprehensive schema with relationships between resources
- Optimized indexes for performance

**Tables:**
- users
- accounts
- hardware
- cards
- vms
- proxmox_nodes

### Proxmox Host Agent

The Proxmox Host Agent is a Python application that runs on Proxmox hosts to sync VM information with AccountDB.

**Key Features:**
- Automatic VM discovery
- Synchronization with AccountDB
- VMID whitelist for controlling which VMs are synced
- API key authentication

**Technologies:**
- Python
- FastAPI
- Proxmox API

## System Architecture

The system follows a modern architecture with clear separation of concerns:

1. **Client Layer**: Next.js frontend application
2. **API Layer**: FastAPI backend application
3. **Data Layer**: PostgreSQL database with RLS
4. **Integration Layer**: Proxmox Host Agent

## Deployment

The system is deployed using Docker Compose, with separate containers for:
- Frontend
- Backend
- Database
- Proxmox Host Agent (deployed on Proxmox hosts)

## Security Model

The security model is based on:
- JWT authentication for API access
- Row-Level Security (RLS) for data isolation
- API keys for Proxmox Host Agent authentication
- Owner-based access control for all resources
