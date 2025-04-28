# Credential Management

## Overview

This document describes the credential management approach used in the AccountDB project. The project uses environment variables to manage credentials, which provides several benefits:

1. **Security**: Credentials are not hardcoded in the source code
2. **Flexibility**: Credentials can be changed without modifying the source code
3. **Environment-specific configuration**: Different environments (development, staging, production) can use different credentials

## Implementation

### Configuration Module

The project uses a centralized configuration module (`config.py`) to load and validate environment variables. This module provides a single source of truth for all configuration values, including credentials.

```python
# config.py
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

class Config:
    """Application configuration."""
    
    # Database configuration
    DB_HOST: str = os.getenv('PG_HOST', 'localhost')
    DB_PORT: str = os.getenv('PG_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'accountdb')
    DB_USER: str = os.getenv('PG_USER', 'postgres')
    DB_PASS: str = os.getenv('PG_PASSWORD')
    
    # JWT configuration
    JWT_SECRET: str = os.getenv('JWT_SECRET_KEY')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))
    
    # API configuration
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8080'))
    API_TOKEN: str = os.getenv('API_TOKEN')
    X_TOKEN: str = os.getenv('X_TOKEN')
    
    # CORS configuration
    CORS_ORIGINS: list = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8084').split(',')
    
    # Registration settings
    SIGNUPS_ENABLED: bool = os.getenv('SIGNUPS_ENABLED', 'true').lower() == 'true'
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """
        Validate the configuration.
        
        Returns:
            Dict[str, Any]: A dictionary of validation errors or an empty dictionary if valid
        """
        errors = {}
        
        # Check required values
        if not cls.DB_PASS:
            errors['PG_PASSWORD'] = 'Database password is required'
        
        if not cls.JWT_SECRET:
            errors['JWT_SECRET_KEY'] = 'JWT secret is required'
        
        if not cls.API_TOKEN:
            errors['API_TOKEN'] = 'API token is required'
            
        if not cls.X_TOKEN:
            errors['X_TOKEN'] = 'X token is required'
        
        return errors
```

### Environment Variables

The project uses a `.env` file to store environment variables. This file is not committed to the repository for security reasons. Instead, a `.env.example` file is provided as a template.

```
# .env.example
# Frontend configuration
NEXT_PUBLIC_API_URL=http://localhost:8084

# API configuration
API_HOST=0.0.0.0
API_PORT=8080
API_DEBUG=False

# Security tokens
X_TOKEN=CHANGEME  # Used for API authentication
API_TOKEN=CHANGEME  # Used for API authentication

# CORS configuration
CORS_ALLOWED_ORIGINS=http://localhost:8084

# Database connection parameters
PG_HOST=postgres
PG_PORT=5432
DB_NAME=accountdb
PG_USER=postgres
PG_PASSWORD=CHANGEME  # Change this to a secure password

# JWT configuration
JWT_SECRET_KEY=your-secure-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# User registration
SIGNUPS_ENABLED=true  # Set to false to disable new user registrations

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

### Usage

The configuration module is used throughout the application to access credentials:

```python
# Example: Database connection
from config import Config

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min and max connections
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    dbname=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASS,
    target_session_attrs="read-write"
)

# Example: JWT authentication
from config import Config

SECRET_KEY = Config.JWT_SECRET
ALGORITHM = Config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.JWT_EXPIRATION
```

## Security Considerations

### Environment Variables

Environment variables are a secure way to manage credentials, but they have some limitations:

1. **Process visibility**: Environment variables are visible to all processes running under the same user
2. **Child processes**: Environment variables are inherited by child processes
3. **Logging**: Environment variables might be accidentally logged

To mitigate these risks, the project:

1. Uses a dedicated user for running the application
2. Minimizes the use of child processes
3. Masks sensitive values in logs

### Secrets Management

For production environments, consider using a secrets management solution such as:

1. **Docker Secrets**: For Docker Swarm deployments
2. **Kubernetes Secrets**: For Kubernetes deployments
3. **AWS Secrets Manager**: For AWS deployments
4. **HashiCorp Vault**: For a more general solution

## Best Practices

1. **Never commit credentials to the repository**
2. **Use strong, unique passwords for each environment**
3. **Rotate credentials regularly**
4. **Limit access to credentials on a need-to-know basis**
5. **Monitor for unauthorized access attempts**
6. **Use the principle of least privilege when granting access**
7. **Validate environment variables at startup**
8. **Provide clear error messages when required variables are missing**
