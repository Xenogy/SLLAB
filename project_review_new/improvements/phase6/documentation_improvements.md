# Phase 6: Documentation Improvements

## Overview

This phase focuses on creating comprehensive documentation for the API, setup process, and architecture to facilitate easier onboarding and maintenance.

## Key Objectives

1. Create API documentation
2. Write setup and deployment guides
3. Document system architecture
4. Add code documentation

## Improvements

### 1. API Documentation

#### OpenAPI/Swagger Documentation

- Configure FastAPI to generate comprehensive OpenAPI documentation
- Add examples and descriptions for all endpoints

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="AccountDB API",
    description="API for managing accounts, hardware, virtual machines, and Proxmox nodes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="AccountDB API",
        version="1.0.0",
        description="API for managing accounts, hardware, virtual machines, and Proxmox nodes",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Apply security to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

#### API Reference

- Create a comprehensive API reference
- Document all endpoints, parameters, and responses

```markdown
# API Reference

## Authentication

All API requests require authentication using a JWT token.

### Request Headers

```
Authorization: Bearer <token>
```

### Authentication Endpoints

#### POST /auth/login

Log in and get an access token.

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "string"
}
```

## Proxmox Nodes

### GET /proxmox-nodes

Get a list of Proxmox nodes.

**Query Parameters:**

- `limit` (integer, default: 10): Maximum number of nodes to return
- `offset` (integer, default: 0): Number of nodes to skip
- `search` (string, optional): Search term for filtering nodes
- `status` (string, optional): Filter by node status

**Response:**

```json
{
  "items": [
    {
      "id": 1,
      "name": "pve1",
      "hostname": "proxmox.example.com",
      "port": 8006,
      "status": "connected",
      "api_key": "string",
      "last_seen": "2023-04-26T12:34:56Z",
      "created_at": "2023-04-25T10:20:30Z",
      "updated_at": "2023-04-26T12:34:56Z",
      "owner_id": 1
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```
```

### 2. Setup and Deployment Guides

#### Development Setup Guide

- Document the development environment setup process
- Include all dependencies and configuration

```markdown
# Development Setup Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 16+
- Python 3.9+
- PostgreSQL 13+ (for local development without Docker)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/accountdb.git
cd accountdb
```

### 2. Environment Configuration

Copy the example environment files:

```bash
cp .env.example .env
cp frontend/nextjs/.env.example frontend/nextjs/.env.local
```

Edit the `.env` file to configure your environment.

### 3. Start the Development Environment

Using Docker Compose:

```bash
docker compose up -d
```

This will start:
- PostgreSQL database
- Backend API
- Frontend development server

### 4. Access the Application

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development Workflow

### Backend Development

The backend code is in the `backend` directory. To run it locally:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

The frontend code is in the `frontend/nextjs` directory. To run it locally:

```bash
cd frontend/nextjs
npm install
npm run dev
```
```

#### Production Deployment Guide

- Document the production deployment process
- Include security considerations

```markdown
# Production Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Domain name with DNS configured
- SSL certificate

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/accountdb.git
cd accountdb
```

### 2. Environment Configuration

Copy the example environment files:

```bash
cp .env.example .env.prod
```

Edit the `.env.prod` file to configure your production environment:

```
# Database
PG_HOST=postgres
PG_PORT=5432
DB_NAME=accountdb
SU_USER=postgres
SU_PASSWORD=<strong-password>

# API
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET=<strong-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 3. Create Docker Compose Production File

Create a `docker-compose.prod.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    restart: always
    environment:
      POSTGRES_USER: ${SU_USER}
      POSTGRES_PASSWORD: ${SU_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    depends_on:
      - postgres
    environment:
      - PG_HOST=${PG_HOST}
      - PG_PORT=${PG_PORT}
      - DB_NAME=${DB_NAME}
      - SU_USER=${SU_USER}
      - SU_PASSWORD=${SU_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=${JWT_ALGORITHM}
      - JWT_EXPIRATION=${JWT_EXPIRATION}
    networks:
      - backend
      - frontend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    restart: always
    depends_on:
      - api
    networks:
      - frontend

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api
      - frontend
    networks:
      - frontend

networks:
  backend:
  frontend:

volumes:
  postgres_data:
```

### 4. Configure Nginx

Create an Nginx configuration file at `nginx/conf/default.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Start the Production Environment

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 6. Security Considerations

- Use strong passwords and secrets
- Keep the system updated
- Set up a firewall
- Configure SSL/TLS
- Implement rate limiting
- Set up monitoring and logging
```

### 3. System Architecture Documentation

#### Architecture Diagrams

- Create architecture diagrams
- Document system components and interactions

```markdown
# System Architecture

## Overview

AccountDB is a comprehensive system for managing accounts, hardware, virtual machines, and Proxmox nodes. It consists of the following components:

- **Frontend**: Next.js web application
- **Backend API**: FastAPI application
- **Database**: PostgreSQL with Row-Level Security
- **Proxmox Host Agent**: Python application for Proxmox integration

## Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│   Frontend  │────▶│  Backend API│────▶│  Database   │
│  (Next.js)  │     │  (FastAPI)  │     │ (PostgreSQL)│
│             │◀────│             │◀────│             │
└─────────────┘     └─────────────┘     └─────────────┘
                          ▲
                          │
                          ▼
                    ┌─────────────┐
                    │             │
                    │Proxmox Host │
                    │   Agent     │
                    │             │
                    └─────────────┘
                          ▲
                          │
                          ▼
                    ┌─────────────┐
                    │             │
                    │  Proxmox    │
                    │    API      │
                    │             │
                    └─────────────┘
```

## Component Descriptions

### Frontend

The frontend is a Next.js web application that provides a user interface for interacting with the API. It includes:

- User authentication
- Dashboard for resource overview
- Management interfaces for accounts, hardware, VMs, and Proxmox nodes

### Backend API

The backend is a FastAPI application that provides RESTful endpoints for managing all resources in the system. It includes:

- RESTful API endpoints
- JWT-based authentication
- Row-Level Security (RLS) for data isolation
- Integration with Proxmox API

### Database

The database is PostgreSQL with Row-Level Security (RLS) implemented to ensure data isolation between users. It includes:

- Tables for accounts, hardware, VMs, and Proxmox nodes
- RLS policies for data isolation
- Indexes for performance optimization

### Proxmox Host Agent

The Proxmox Host Agent is a Python application that runs on Proxmox hosts to sync VM information with AccountDB. It includes:

- VM discovery and synchronization
- VMID whitelist for controlling which VMs are synced
- API key authentication
```

#### Data Flow Documentation

- Document data flows between components
- Include sequence diagrams for key operations

```markdown
# Data Flow Documentation

## VM Synchronization Flow

This diagram shows the flow of data during VM synchronization from Proxmox to AccountDB.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│  Proxmox    │────▶│Proxmox Host │────▶│  Backend API│────▶│  Database   │
│    API      │     │   Agent     │     │  (FastAPI)  │     │ (PostgreSQL)│
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Sequence Diagram

```
┌─────────┐          ┌─────────┐          ┌─────────┐          ┌─────────┐
│ Proxmox │          │ Host    │          │ Backend │          │ Database│
│ API     │          │ Agent   │          │ API     │          │         │
└────┬────┘          └────┬────┘          └────┬────┘          └────┬────┘
     │                     │                    │                    │
     │  1. Get VMs         │                    │                    │
     │◀────────────────────│                    │                    │
     │                     │                    │                    │
     │  2. VM List         │                    │                    │
     │─────────────────────▶                    │                    │
     │                     │                    │                    │
     │                     │  3. Get Whitelist  │                    │
     │                     │────────────────────▶                    │
     │                     │                    │                    │
     │                     │  4. Whitelist      │                    │
     │                     │◀────────────────────                    │
     │                     │                    │                    │
     │                     │  5. Filter VMs     │                    │
     │                     │───┐                │                    │
     │                     │   │                │                    │
     │                     │◀──┘                │                    │
     │                     │                    │                    │
     │                     │  6. Sync VMs       │                    │
     │                     │────────────────────▶                    │
     │                     │                    │                    │
     │                     │                    │  7. Update VMs     │
     │                     │                    │────────────────────▶
     │                     │                    │                    │
     │                     │                    │  8. Success        │
     │                     │                    │◀────────────────────
     │                     │                    │                    │
     │                     │  9. Success        │                    │
     │                     │◀────────────────────                    │
     │                     │                    │                    │
```

### Steps

1. **Host Agent requests VMs from Proxmox API**
   - The Host Agent queries the Proxmox API for all VMs on the node

2. **Proxmox API returns VM list**
   - The Proxmox API returns a list of all VMs with their details

3. **Host Agent requests whitelist from Backend API**
   - The Host Agent queries the Backend API for the VMID whitelist

4. **Backend API returns whitelist**
   - The Backend API returns the list of whitelisted VMIDs

5. **Host Agent filters VMs**
   - The Host Agent filters the VM list based on the whitelist

6. **Host Agent sends filtered VMs to Backend API**
   - The Host Agent sends the filtered VM list to the Backend API for synchronization

7. **Backend API updates VMs in Database**
   - The Backend API updates the VM information in the database

8. **Database confirms success**
   - The database confirms the update was successful

9. **Backend API confirms success to Host Agent**
   - The Backend API confirms the synchronization was successful
```

### 4. Code Documentation

#### Code Comments

- Add comprehensive comments to all code
- Document complex logic and algorithms

```python
def sync_vms():
    """
    Synchronize VMs between Proxmox and AccountDB.
    
    This function performs the following steps:
    1. Get VMs from Proxmox API
    2. Get whitelist from AccountDB
    3. Filter VMs based on whitelist
    4. Sync filtered VMs to AccountDB
    
    If any step fails, the function will log the error and continue with the next sync cycle.
    """
    try:
        # Step 1: Get VMs from Proxmox
        vms = proxmox_client.get_vms()
        logger.info(f"Retrieved {len(vms)} VMs from Proxmox")
        
        # Step 2: Get whitelist
        whitelist = await get_whitelist()
        whitelist_enabled = len(whitelist) > 0
        
        # Step 3: Filter VMs based on whitelist if enabled
        if whitelist_enabled:
            # Convert whitelist to a set for O(1) lookups
            whitelist_set = set(whitelist)
            filtered_vms = [vm for vm in vms if vm.get('vmid') in whitelist_set]
            logger.info(f"Filtered VMs based on whitelist: {len(filtered_vms)} of {len(vms)} VMs will be synced")
            vms = filtered_vms
        
        # Step 4: Sync with AccountDB
        await accountdb_client.sync_vms(vms)
    except Exception as e:
        logger.error(f"Error during VM synchronization: {e}")
```

#### README Files

- Create README files for all components
- Include setup instructions and usage examples

```markdown
# Proxmox Host Agent

## Overview

The Proxmox Host Agent is a Python application that runs on Proxmox hosts to sync VM information with AccountDB. It discovers VMs on the Proxmox host and synchronizes them with the AccountDB API.

## Features

- Automatic VM discovery
- Synchronization with AccountDB
- VMID whitelist for controlling which VMs are synced
- API key authentication
- Automatic reconnection to AccountDB

## Installation

### Prerequisites

- Python 3.9+
- Proxmox VE 7.0+
- Access to the Proxmox API
- AccountDB API key

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/accountdb.git
cd accountdb/proxmox_host
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file:

```bash
cp .env.example .env
```

5. Edit the `.env` file to configure your environment:

```
# Proxmox configuration
PROXMOX_HOST=your-proxmox-host.example.com
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your-password
PROXMOX_VERIFY_SSL=true
PROXMOX_NODE_NAME=pve

# AccountDB configuration
ACCOUNTDB_URL=https://accountdb.example.com
ACCOUNTDB_API_KEY=your-api-key
ACCOUNTDB_NODE_ID=1

# Agent configuration
PORT=8000
DEBUG=false
LOG_LEVEL=info
UPDATE_INTERVAL=300
```

## Usage

### Running the Agent

```bash
python main.py
```

### Command Line Options

- `--port`: Port to run the server on (default: 8000)
- `--debug`: Enable debug mode (default: false)
- `--log-level`: Log level (default: info)
- `--update-interval`: Update interval in seconds (default: 300)

Example:

```bash
python main.py --port 8001 --debug --log-level debug --update-interval 60
```

### API Endpoints

- `GET /health`: Health check endpoint
- `GET /health/proxmox`: Proxmox API health check
- `GET /status`: Get detailed status information
- `GET /sync/status`: Get synchronization status
- `POST /sync/trigger`: Trigger a manual synchronization
- `GET /vms`: Get all VMs from Proxmox
- `GET /vms/{vm_id}`: Get a specific VM from Proxmox
- `GET /whitelist`: Get the VMID whitelist
- `POST /whitelist/refresh`: Force refresh the whitelist cache

## Systemd Service

To run the agent as a systemd service, create a service file:

```bash
sudo nano /etc/systemd/system/proxmox-agent.service
```

Add the following content:

```
[Unit]
Description=Proxmox Host Agent
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/accountdb/proxmox_host
ExecStart=/path/to/accountdb/proxmox_host/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable proxmox-agent
sudo systemctl start proxmox-agent
```
```

## Implementation Steps

1. Create API documentation
   - Configure OpenAPI/Swagger
   - Create API reference
   - Add examples and descriptions

2. Write setup and deployment guides
   - Create development setup guide
   - Create production deployment guide
   - Document environment configuration

3. Document system architecture
   - Create architecture diagrams
   - Document component interactions
   - Create data flow diagrams

4. Add code documentation
   - Add comprehensive code comments
   - Create README files for all components
   - Document complex logic and algorithms

## Expected Outcomes

- Comprehensive API documentation
- Clear setup and deployment guides
- Well-documented system architecture
- Improved code documentation
