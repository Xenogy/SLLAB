# AccountDB Installation Guide

## Introduction

This guide provides step-by-step instructions for installing and setting up the AccountDB system. AccountDB is a comprehensive system for managing accounts, virtual machines through Proxmox integration, and includes a Windows VM Agent for monitoring and automation.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Options](#installation-options)
3. [Core System Installation](#core-system-installation)
   - [Docker Installation](#docker-installation)
   - [Manual Installation](#manual-installation)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Component Installation](#component-installation)
   - [Proxmox Host Agent Installation](#proxmox-host-agent-installation)
   - [Windows VM Agent Installation](#windows-vm-agent-installation)
7. [Starting the Application](#starting-the-application)
8. [Verifying the Installation](#verifying-the-installation)
9. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

- **CPU**: 2+ cores
- **RAM**: 4+ GB
- **Disk Space**: 10+ GB

### Software Requirements

- **Operating System**: Linux (Ubuntu 20.04 LTS or later recommended), macOS, or Windows
- **Docker**: Docker 20.10.0 or later (for Docker installation)
- **Python**: Python 3.9 or later (for manual installation)
- **PostgreSQL**: PostgreSQL 13 or later
- **Node.js**: Node.js 14 or later (for frontend)

## Installation Options

AccountDB consists of several components that can be installed separately or together:

1. **Core System**: The main AccountDB application with API, database, and frontend
2. **Proxmox Host Agent**: Agent for synchronizing VM information from Proxmox
3. **Windows VM Agent**: Agent for monitoring and automation on Windows VMs

Each component can be installed using one of the following methods:

1. **Docker Installation**: Recommended for production environments
2. **Manual Installation**: Recommended for development environments

### Deployment Scenarios

#### Full Installation

Install all components for a complete AccountDB system with Proxmox integration and Windows VM Agent support.

#### Core System Only

Install only the core AccountDB system without Proxmox integration or Windows VM Agent support.

#### Core System with Proxmox Integration

Install the core AccountDB system and the Proxmox Host Agent for VM management.

#### Core System with Windows VM Agent

Install the core AccountDB system and deploy the Windows VM Agent on your Windows VMs.

## Core System Installation

### Docker Installation

#### Prerequisites

- Docker 20.10.0 or later
- Docker Compose 2.0.0 or later

#### Steps

1. Clone the repository:

```bash
git clone https://github.com/xenogy/SLLAB.git
cd accountdb
```

2. Create a `.env` file with the required environment variables:

```bash
cp .env.example .env
```

3. Edit the `.env` file with your configuration:

```bash
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=accountdb
DB_USER=accountdb
DB_PASS=your_password

# JWT Configuration
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false
API_DEBUG=false

# Proxmox Configuration (if using Proxmox integration)
PROXMOX_HOST=https://proxmox.example.com:8006
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_proxmox_password
PROXMOX_VERIFY_SSL=true
PROXMOX_SYNC_INTERVAL=300

# Windows VM Agent Configuration (if using Windows VM Agent)
WINDOWS_VM_AGENT_API_KEY=your_api_key
WINDOWS_VM_AGENT_LOG_LEVEL=INFO
WINDOWS_VM_AGENT_POLL_INTERVAL=1
```

4. Build and start the core containers:

```bash
# Start only the core system
docker-compose up -d api frontend postgres

# Or start everything including Proxmox Host Agent
docker-compose up -d
```

(Optional: remove and rebuild, destroys all data):
```bash
docker compose down -v && docker compose up -d
```


### Manual Installation

#### Prerequisites

- Python 3.9 or later
- PostgreSQL 13 or later
- Node.js 14 or later (for frontend)

#### Steps

1. Clone the repository:

```bash
git clone https://github.com/xenogy/SLLAB.git
cd accountdb
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install the dependencies:

```bash
pip install -r backend/requirements.txt
```

4. Create a `.env` file with the required environment variables:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=accountdb
DB_USER=accountdb
DB_PASS=your_password

# JWT Configuration
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true
API_DEBUG=true

# Proxmox Configuration (if using Proxmox integration)
PROXMOX_HOST=https://proxmox.example.com:8006
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_proxmox_password
PROXMOX_VERIFY_SSL=true
PROXMOX_SYNC_INTERVAL=300

# Windows VM Agent Configuration (if using Windows VM Agent)
WINDOWS_VM_AGENT_API_KEY=your_api_key
WINDOWS_VM_AGENT_LOG_LEVEL=INFO
WINDOWS_VM_AGENT_POLL_INTERVAL=1
```

6. Initialize the database:

```bash
python -m scripts.init_db
```

7. Create an admin user:

```bash
python -m scripts.create_admin_user
```

8. Set up the frontend:

```bash
cd frontend
npm install
npm run build
```

9. Start the API server:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

10. Start the frontend server:

```bash
cd frontend
npm run start
```

## Database Setup

### Creating the Database

1. Connect to PostgreSQL:

```bash
sudo -u postgres psql
```

2. Create the database and user:

```sql
CREATE DATABASE accountdb;
CREATE USER accountdb WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE accountdb TO accountdb;
```

3. Enable the required extensions:

```sql
\c accountdb
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Database Migration

The database schema is automatically created when you run the initialization script:

```bash
# Docker
docker-compose exec api python -m scripts.init_db

# Manual
python -m scripts.init_db
```

## Configuration

### Environment Variables

AccountDB uses environment variables for configuration. The following variables are available:

#### Database Configuration

- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_NAME`: PostgreSQL database name (default: accountdb)
- `DB_USER`: PostgreSQL username (default: accountdb)
- `DB_PASS`: PostgreSQL password
- `DB_POOL_MIN`: Minimum number of connections in the pool (default: 1)
- `DB_POOL_MAX`: Maximum number of connections in the pool (default: 10)

#### JWT Configuration

- `JWT_SECRET`: Secret key for JWT tokens
- `JWT_ALGORITHM`: Algorithm for JWT tokens (default: HS256)
- `JWT_EXPIRATION`: Expiration time for JWT tokens in seconds (default: 86400)

#### API Configuration

- `API_HOST`: Host to bind the API server (default: 0.0.0.0)
- `API_PORT`: Port to bind the API server (default: 8000)
- `API_WORKERS`: Number of worker processes (default: 4)
- `API_RELOAD`: Enable auto-reload for development (default: false)
- `API_DEBUG`: Enable debug mode (default: false)

#### Logging Configuration

- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Logging format (default: %(asctime)s - %(name)s - %(levelname)s - %(message)s)
- `LOG_FILE`: Log file path (default: None, logs to stdout)

#### Proxmox Configuration

- `PROXMOX_HOST`: Proxmox API URL (e.g., https://proxmox.example.com:8006)
- `PROXMOX_USER`: Proxmox API username (e.g., root@pam)
- `PROXMOX_PASSWORD`: Proxmox API password
- `PROXMOX_VERIFY_SSL`: Whether to verify SSL certificates (default: true)
- `PROXMOX_SYNC_INTERVAL`: Interval in seconds for VM synchronization (default: 300)

#### Windows VM Agent Configuration

- `WINDOWS_VM_AGENT_API_KEY`: API key for Windows VM Agent authentication
- `WINDOWS_VM_AGENT_LOG_LEVEL`: Log level for the Windows VM Agent (default: INFO)
- `WINDOWS_VM_AGENT_POLL_INTERVAL`: Interval in seconds for log file polling (default: 1)

### Configuration File

Instead of using environment variables, you can also use a configuration file. Create a file named `config.yaml` in the root directory:

```yaml
database:
  host: localhost
  port: 5432
  name: accountdb
  user: accountdb
  password: your_password
  pool_min: 1
  pool_max: 10

jwt:
  secret: your_jwt_secret
  algorithm: HS256
  expiration: 86400

api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: false
  debug: false

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null

proxmox:
  host: https://proxmox.example.com:8006
  user: root@pam
  password: your_proxmox_password
  verify_ssl: true
  sync_interval: 300

windows_vm_agent:
  api_key: your_api_key
  log_level: INFO
  poll_interval: 1
```

### Proxmox Host Agent Configuration

The Proxmox Host Agent uses a separate configuration file. Create a file named `config.py` in the `proxmox_host` directory:

```python
# Proxmox API Configuration
PROXMOX_HOST = "https://your-proxmox-server:8006"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_proxmox_password"
PROXMOX_VERIFY_SSL = True

# AccountDB API Configuration
ACCOUNTDB_API_URL = "http://localhost:8000"
ACCOUNTDB_API_KEY = "your_api_key"

# Synchronization Configuration
SYNC_INTERVAL = 300  # seconds
```

### Windows VM Agent Configuration

The Windows VM Agent uses a YAML configuration file. Create a file named `config.yaml` in the Windows VM Agent installation directory:

```yaml
General:
  APIKey: "your_api_key"
  ManagerBaseURL: "http://accountdb.example.com:8000"
  LogLevel: "INFO"
  LogFilePath: "C:\\CsBotAgent\\logs\\windows_vm_agent.log"

EventMonitors:
  - Name: "AccountLoginMonitor"
    Type: "LogFileTail"
    LogFilePath: "C:\\Path\\To\\CSBot\\bot.log"
    PollInterval: 1

EventTriggers:
  - EventName: "AccountLoginDetected"
    Regex: 'User logged in:\s+(?P<account_id>\w+)'
    Action: "UpdateAccountStatus"
    ActionParams:
      ScriptPath: "C:\\CsBotAgent\\ActionScripts\\UpdateAccountStatus.ps1"
      AccountID: "{account_id}"
```

## Component Installation

### Proxmox Host Agent Installation

The Proxmox Host Agent is responsible for synchronizing VM information from Proxmox to AccountDB.

#### Prerequisites

- Python 3.9 or later
- Access to Proxmox API
- Access to AccountDB API

#### Docker Installation

1. Build and start the Proxmox Host Agent container:

```bash
docker-compose up -d proxmox-agent
```

#### Manual Installation

1. Navigate to the Proxmox Host Agent directory:

```bash
cd proxmox_host
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create a configuration file:

```bash
cp config.example.py config.py
```

5. Edit the configuration file with your Proxmox and AccountDB API details:

```python
# Proxmox API Configuration
PROXMOX_HOST = "https://your-proxmox-server:8006"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_proxmox_password"
PROXMOX_VERIFY_SSL = True

# AccountDB API Configuration
ACCOUNTDB_API_URL = "http://localhost:8000"
ACCOUNTDB_API_KEY = "your_api_key"

# Synchronization Configuration
SYNC_INTERVAL = 300  # seconds
```

6. Start the Proxmox Host Agent:

```bash
python main.py
```

### Windows VM Agent Installation

The Windows VM Agent is responsible for monitoring log files and executing actions on Windows VMs.

#### Prerequisites

- Windows 10 or Windows Server 2016 or later
- Python 3.9 or later
- PowerShell 5.1 or later
- Administrator access

#### Installation Steps

1. Download the Windows VM Agent installer from the releases page or copy it from the repository:

```bash
# From the repository root
cd windows_vm_agent
```

2. Copy the agent files to the Windows VM:

```bash
# Using SCP or other file transfer method
scp -r windows_vm_agent/* user@windows-vm:C:/CsBotAgent/
```

3. On the Windows VM, open PowerShell as Administrator and navigate to the agent directory:

```powershell
cd C:\CsBotAgent
```

4. Run the installation script:

```powershell
.\install.bat
```

5. Configure the agent by editing the `config.yaml` file:

```yaml
General:
  APIKey: "your_api_key"
  ManagerBaseURL: "http://accountdb.example.com:8000"
  LogLevel: "INFO"
  LogFilePath: "C:\\CsBotAgent\\logs\\windows_vm_agent.log"

EventMonitors:
  - Name: "AccountLoginMonitor"
    Type: "LogFileTail"
    LogFilePath: "C:\\Path\\To\\CSBot\\bot.log"
    PollInterval: 1

EventTriggers:
  - EventName: "AccountLoginDetected"
    Regex: 'User logged in:\s+(?P<account_id>\w+)'
    Action: "UpdateAccountStatus"
    ActionParams:
      ScriptPath: "C:\\CsBotAgent\\ActionScripts\\UpdateAccountStatus.ps1"
      AccountID: "{account_id}"
```

6. Start the agent service:

```powershell
Start-Service WindowsVMAgent
```

7. Verify the agent is running:

```powershell
Get-Service WindowsVMAgent
```

## Starting the Application

### Docker

```bash
docker-compose up -d
```

### Manual

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Verifying the Installation

### Core System Verification

1. Open a web browser and navigate to:

```
http://localhost:8000/api/docs
```

2. You should see the Swagger UI with the API documentation.

3. Try to authenticate using the admin user you created:

```http
POST /auth/token
Content-Type: application/json

{
  "username": "admin",
  "password": "your_admin_password"
}
```

4. You should receive a JWT token in the response.

5. Access the frontend application:

```
http://localhost:8084
```

6. Log in with the admin user credentials.

### Proxmox Integration Verification

1. Verify that the Proxmox Host Agent is running:

```bash
# Docker
docker-compose ps proxmox-agent

# Manual
ps aux | grep proxmox_host
```

2. Check if Proxmox nodes are registered in the system:

```http
GET /proxmox-nodes
Authorization: Bearer your_jwt_token
```

3. Trigger a manual synchronization:

```http
POST /proxmox-nodes/{node_id}/sync
Authorization: Bearer your_jwt_token
```

4. Verify that VMs are being synchronized:

```http
GET /vms
Authorization: Bearer your_jwt_token
```

### Windows VM Agent Verification

1. On the Windows VM, verify that the agent service is running:

```powershell
Get-Service WindowsVMAgent
```

2. Check the agent logs for any errors:

```powershell
cat "C:\CsBotAgent\logs\windows_vm_agent.log"
```

3. Verify that the agent is registered with AccountDB:

```http
GET /windows-vm-agent
Authorization: Bearer your_jwt_token
```

4. Test the agent by triggering a test event:

```powershell
# Create a test log entry that matches your configured regex pattern
Add-Content -Path "C:\Path\To\CSBot\bot.log" -Value "User logged in: test_account"
```

5. Check if the action was executed:

```powershell
# Check the agent logs
cat "C:\CsBotAgent\logs\windows_vm_agent.log"
```

## Troubleshooting

### Common Issues

#### Database Connection Issues

If you encounter database connection issues, check the following:

- Make sure the PostgreSQL server is running.
- Check the database connection parameters in the configuration.
- Make sure the database exists.
- Make sure the database user has the necessary permissions.

#### API Server Issues

If you encounter API server issues, check the following:

- Make sure the API server is running.
- Check the API server logs for errors.
- Make sure the API server is configured correctly.
- Make sure the API server has access to the database.

#### Authentication Issues

If you encounter authentication issues, check the following:

- Make sure the JWT secret is configured correctly.
- Make sure the JWT algorithm is configured correctly.
- Make sure the JWT expiration is configured correctly.
- Make sure the admin user exists in the database.

#### Proxmox Integration Issues

If you encounter Proxmox integration issues, check the following:

- Make sure the Proxmox server is accessible from the AccountDB server.
- Check the Proxmox API credentials in the configuration.
- Make sure the Proxmox API user has the necessary permissions.
- Check the Proxmox Host Agent logs for errors.
- Verify that the Proxmox nodes are registered in AccountDB.

#### Windows VM Agent Issues

If you encounter Windows VM Agent issues, check the following:

- Make sure the agent service is running on the Windows VM.
- Check the agent logs for errors.
- Verify the agent configuration, especially the API key and server URL.
- Make sure the log files being monitored exist and are accessible.
- Check if PowerShell execution policy allows running the action scripts.
- Verify network connectivity from the Windows VM to the AccountDB server.

### Logs

Check the logs for more information about errors:

```bash
# Core System Logs
# Docker
docker-compose logs api
docker-compose logs frontend
docker-compose logs postgres

# Manual
cat logs/api.log  # If LOG_FILE is configured

# Proxmox Host Agent Logs
# Docker
docker-compose logs proxmox-agent

# Manual
cat proxmox_host/logs/proxmox_agent.log

# Windows VM Agent Logs
# On the Windows VM
cat "C:\CsBotAgent\logs\windows_vm_agent.log"
```

### Common Error Messages

#### "Unable to connect to Proxmox API"

This error indicates that the Proxmox Host Agent cannot connect to the Proxmox API. Check the following:

- Verify the Proxmox API URL in the configuration.
- Check if the Proxmox server is accessible from the AccountDB server.
- Verify the Proxmox API credentials.

#### "Failed to set RLS context"

This error indicates that the Row-Level Security (RLS) context could not be set. Check the following:

- Make sure the database connection is using the correct RLS context manager.
- Verify that the user ID and role are being passed correctly.
- Check if the RLS policies are correctly defined in the database.

#### "Windows VM Agent registration failed"

This error indicates that the Windows VM Agent could not be registered with AccountDB. Check the following:

- Verify the API key in the agent configuration.
- Check if the VM ID exists in AccountDB.
- Ensure the user has permission to register the VM.

### Getting Help

If you need further assistance, please contact the AccountDB support team or open an issue on the GitHub repository.
