# AccountDB Installation Guide

## Introduction

This guide provides step-by-step instructions for installing and setting up the AccountDB system. AccountDB is a comprehensive system for managing Steam accounts, hardware profiles, cards, and user authentication.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Options](#installation-options)
3. [Docker Installation](#docker-installation)
4. [Manual Installation](#manual-installation)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
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

AccountDB can be installed using one of the following methods:

1. **Docker Installation**: Recommended for production environments
2. **Manual Installation**: Recommended for development environments

## Docker Installation

### Prerequisites

- Docker 20.10.0 or later
- Docker Compose 2.0.0 or later

### Steps

1. Clone the repository:

```bash
git clone https://github.com/your-organization/accountdb.git
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
```

4. Build and start the containers:

```bash
docker-compose up -d
```

5. Initialize the database:

```bash
docker-compose exec api python -m scripts.init_db
```

6. Create an admin user:

```bash
docker-compose exec api python -m scripts.create_admin_user
```

## Manual Installation

### Prerequisites

- Python 3.9 or later
- PostgreSQL 13 or later
- Node.js 14 or later (for frontend)

### Steps

1. Clone the repository:

```bash
git clone https://github.com/your-organization/accountdb.git
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
```

6. Initialize the database:

```bash
python -m scripts.init_db
```

7. Create an admin user:

```bash
python -m scripts.create_admin_user
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

### Logs

Check the logs for more information about errors:

```bash
# Docker
docker-compose logs api

# Manual
cat logs/api.log  # If LOG_FILE is configured
```

### Getting Help

If you need further assistance, please contact the AccountDB support team or open an issue on the GitHub repository.
