# AccountDB Development Setup Guide

## Introduction

This guide provides step-by-step instructions for setting up a development environment for the AccountDB project. It covers the installation of required tools, configuration of the development environment, and running the application locally.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting the Code](#getting-the-code)
3. [Setting Up the Development Environment](#setting-up-the-development-environment)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Running Tests](#running-tests)
8. [Development Workflow](#development-workflow)
9. [IDE Setup](#ide-setup)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, make sure you have the following tools installed:

### Required Tools

- **Git**: Version control system
- **Python**: Version 3.9 or later
- **PostgreSQL**: Version 13 or later
- **Docker** (optional): For containerized development

### Installation Instructions

#### Git

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install git
  ```

- **macOS**:
  ```bash
  brew install git
  ```

- **Windows**:
  Download and install from [git-scm.com](https://git-scm.com/download/win)

#### Python

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install python3.9 python3.9-venv python3.9-dev
  ```

- **macOS**:
  ```bash
  brew install python@3.9
  ```

- **Windows**:
  Download and install from [python.org](https://www.python.org/downloads/)

#### PostgreSQL

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install postgresql postgresql-contrib libpq-dev
  ```

- **macOS**:
  ```bash
  brew install postgresql
  brew services start postgresql
  ```

- **Windows**:
  Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Docker (Optional)

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install docker.io docker-compose
  sudo systemctl enable --now docker
  sudo usermod -aG docker $USER
  ```

- **macOS**:
  Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

- **Windows**:
  Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

## Getting the Code

1. Clone the repository:

```bash
git clone https://github.com/your-organization/accountdb.git
cd accountdb
```

2. Set up Git configuration:

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Setting Up the Development Environment

### Using Virtual Environment (Recommended)

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

- **Linux/macOS**:
  ```bash
  source venv/bin/activate
  ```

- **Windows**:
  ```bash
  venv\Scripts\activate
  ```

3. Install the dependencies:

```bash
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt  # Development dependencies
```

### Using Docker (Alternative)

1. Build the Docker image:

```bash
docker-compose build
```

2. Start the containers:

```bash
docker-compose up -d
```

## Database Setup

### Local PostgreSQL Setup

1. Create a database user and database:

```bash
sudo -u postgres psql
```

```sql
CREATE USER accountdb WITH PASSWORD 'accountdb';
CREATE DATABASE accountdb;
GRANT ALL PRIVILEGES ON DATABASE accountdb TO accountdb;
ALTER USER accountdb WITH SUPERUSER;  -- For development only
\c accountdb
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q
```

2. Initialize the database:

```bash
# Using virtual environment
python -m scripts.init_db

# Using Docker
docker-compose exec api python -m scripts.init_db
```

3. Create an admin user:

```bash
# Using virtual environment
python -m scripts.create_admin_user

# Using Docker
docker-compose exec api python -m scripts.create_admin_user
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following content:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=accountdb
DB_USER=accountdb
DB_PASS=accountdb
DB_POOL_MIN=1
DB_POOL_MAX=10

# JWT Configuration
JWT_SECRET=development_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true
API_DEBUG=true

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/api.log

# Rate Limiting Configuration
RATE_LIMIT_ENABLED=false

# Timeout Configuration
TIMEOUT_ENABLED=false

# Size Limit Configuration
SIZE_LIMIT_ENABLED=false
```

### Configuration File (Alternative)

Instead of using environment variables, you can create a `config.yaml` file in the root directory:

```yaml
database:
  host: localhost
  port: 5432
  name: accountdb
  user: accountdb
  password: accountdb
  pool_min: 1
  pool_max: 10

jwt:
  secret: development_secret_key
  algorithm: HS256
  expiration: 86400

api:
  host: 0.0.0.0
  port: 8000
  workers: 1
  reload: true
  debug: true

logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/api.log

rate_limit:
  enabled: false

timeout:
  enabled: false

size_limit:
  enabled: false
```

## Running the Application

### Using Virtual Environment

1. Make sure the virtual environment is activated:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

2. Start the API server:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. Access the API documentation:

```
http://localhost:8000/api/docs
```

### Using Docker

1. Start the containers:

```bash
docker-compose up -d
```

2. Access the API documentation:

```
http://localhost:8000/api/docs
```

## Running Tests

### Using Virtual Environment

1. Make sure the virtual environment is activated:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

2. Run the tests:

```bash
cd backend
pytest
```

3. Run tests with coverage:

```bash
cd backend
pytest --cov=.
```

### Using Docker

1. Run the tests:

```bash
docker-compose exec api pytest
```

2. Run tests with coverage:

```bash
docker-compose exec api pytest --cov=.
```

## Development Workflow

### Code Style

The project follows the PEP 8 style guide for Python code. We use the following tools to enforce code style:

- **Black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linter

To format your code:

```bash
# Using virtual environment
cd backend
black .
isort .

# Using Docker
docker-compose exec api black .
docker-compose exec api isort .
```

To check your code:

```bash
# Using virtual environment
cd backend
flake8 .

# Using Docker
docker-compose exec api flake8 .
```

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code style and run tests before committing. To set up pre-commit hooks:

```bash
# Using virtual environment
pip install pre-commit
pre-commit install

# Using Docker
docker-compose exec api pip install pre-commit
docker-compose exec api pre-commit install
```

### Git Workflow

1. Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:

```bash
git add .
git commit -m "Add your feature"
```

3. Push your changes to the remote repository:

```bash
git push origin feature/your-feature-name
```

4. Create a pull request on GitHub.

## IDE Setup

### Visual Studio Code

1. Install the following extensions:
   - Python
   - Pylance
   - Docker
   - PostgreSQL
   - YAML
   - EditorConfig
   - GitLens

2. Configure the Python interpreter:
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
   - Type "Python: Select Interpreter"
   - Select the Python interpreter from your virtual environment

3. Configure the settings:
   - Press `Ctrl+,` (Windows/Linux) or `Cmd+,` (macOS)
   - Add the following settings:
     ```json
     {
       "python.linting.enabled": true,
       "python.linting.flake8Enabled": true,
       "python.formatting.provider": "black",
       "editor.formatOnSave": true,
       "editor.codeActionsOnSave": {
         "source.organizeImports": true
       }
     }
     ```

### PyCharm

1. Open the project in PyCharm.

2. Configure the Python interpreter:
   - Go to File > Settings > Project > Python Interpreter
   - Click the gear icon and select "Add"
   - Select "Existing Environment" and choose the Python interpreter from your virtual environment

3. Configure the code style:
   - Go to File > Settings > Editor > Code Style > Python
   - Set the line length to 88 (Black's default)
   - Enable "Optimize imports on the fly"

4. Install and configure plugins:
   - Black
   - isort
   - flake8

## Troubleshooting

### Common Issues

#### Virtual Environment Issues

**Problem**: Unable to activate the virtual environment.

**Solution**:
1. Make sure you created the virtual environment correctly:
   ```bash
   python -m venv venv
   ```
2. Try recreating the virtual environment:
   ```bash
   rm -rf venv
   python -m venv venv
   ```

#### Database Connection Issues

**Problem**: Unable to connect to the database.

**Solution**:
1. Make sure PostgreSQL is running:
   ```bash
   # Linux
   sudo systemctl status postgresql
   
   # macOS
   brew services list
   ```
2. Check the database connection parameters in the `.env` file or `config.yaml`.
3. Try connecting to the database manually:
   ```bash
   psql -h localhost -p 5432 -U accountdb -d accountdb
   ```

#### API Server Issues

**Problem**: API server fails to start.

**Solution**:
1. Check the error message.
2. Make sure all dependencies are installed:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Check if the port is already in use:
   ```bash
   sudo lsof -i :8000
   ```
4. Try starting the server with a different port:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

#### Docker Issues

**Problem**: Docker containers fail to start.

**Solution**:
1. Check the Docker logs:
   ```bash
   docker-compose logs
   ```
2. Make sure Docker is running:
   ```bash
   docker info
   ```
3. Try rebuilding the containers:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

### Getting Help

If you need further assistance, please contact the development team or open an issue on the GitHub repository.

## Next Steps

Now that you have set up your development environment, you can start contributing to the AccountDB project. Check out the [Contribution Guide](contribution_guide.md) for more information on how to contribute to the project.
