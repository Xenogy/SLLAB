# AccountDB Configuration Guide

## Introduction

This guide provides detailed information about configuring the AccountDB system. It covers all available configuration options, their default values, and how to customize them for your specific needs.

## Table of Contents

1. [Configuration Methods](#configuration-methods)
2. [Environment Variables](#environment-variables)
3. [Configuration File](#configuration-file)
4. [Database Configuration](#database-configuration)
5. [JWT Configuration](#jwt-configuration)
6. [API Configuration](#api-configuration)
7. [Logging Configuration](#logging-configuration)
8. [Rate Limiting Configuration](#rate-limiting-configuration)
9. [Timeout Configuration](#timeout-configuration)
10. [Size Limit Configuration](#size-limit-configuration)
11. [CORS Configuration](#cors-configuration)
12. [Advanced Configuration](#advanced-configuration)

## Configuration Methods

AccountDB supports two methods of configuration:

1. **Environment Variables**: Set environment variables before starting the application.
2. **Configuration File**: Create a YAML configuration file.

The configuration file takes precedence over environment variables.

## Environment Variables

### Database Configuration

- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_NAME`: PostgreSQL database name (default: accountdb)
- `DB_USER`: PostgreSQL username (default: accountdb)
- `DB_PASS`: PostgreSQL password
- `DB_POOL_MIN`: Minimum number of connections in the pool (default: 1)
- `DB_POOL_MAX`: Maximum number of connections in the pool (default: 10)
- `DB_POOL_TIMEOUT`: Connection timeout in seconds (default: 30)
- `DB_SSL`: Enable SSL for database connection (default: false)
- `DB_SSL_CA`: Path to SSL CA certificate (default: None)
- `DB_SSL_CERT`: Path to SSL client certificate (default: None)
- `DB_SSL_KEY`: Path to SSL client key (default: None)

### JWT Configuration

- `JWT_SECRET`: Secret key for JWT tokens
- `JWT_ALGORITHM`: Algorithm for JWT tokens (default: HS256)
- `JWT_EXPIRATION`: Expiration time for JWT tokens in seconds (default: 86400)
- `JWT_REFRESH_EXPIRATION`: Expiration time for refresh tokens in seconds (default: 604800)
- `JWT_AUDIENCE`: Audience for JWT tokens (default: None)
- `JWT_ISSUER`: Issuer for JWT tokens (default: None)

### API Configuration

- `API_HOST`: Host to bind the API server (default: 0.0.0.0)
- `API_PORT`: Port to bind the API server (default: 8000)
- `API_WORKERS`: Number of worker processes (default: 4)
- `API_RELOAD`: Enable auto-reload for development (default: false)
- `API_DEBUG`: Enable debug mode (default: false)
- `API_DOCS_URL`: URL for the Swagger UI (default: /api/docs)
- `API_REDOC_URL`: URL for the ReDoc UI (default: /api/redoc)
- `API_OPENAPI_URL`: URL for the OpenAPI schema (default: /openapi.json)
- `API_ROOT_PATH`: Root path for the API (default: /)

### Logging Configuration

- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Logging format (default: %(asctime)s - %(name)s - %(levelname)s - %(message)s)
- `LOG_FILE`: Log file path (default: None, logs to stdout)
- `LOG_ROTATION`: Enable log rotation (default: false)
- `LOG_ROTATION_SIZE`: Maximum size of log file before rotation in bytes (default: 10485760)
- `LOG_ROTATION_COUNT`: Number of rotated log files to keep (default: 5)

### Rate Limiting Configuration

- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_WINDOW`: Time window for rate limiting in seconds (default: 60)
- `RATE_LIMIT_MAX_REQUESTS`: Maximum number of requests per window (default: 100)
- `RATE_LIMIT_EXCLUDE_PATHS`: Comma-separated list of paths to exclude from rate limiting (default: /health,/api/docs,/api/redoc,/openapi.json)

### Timeout Configuration

- `TIMEOUT_ENABLED`: Enable request timeouts (default: true)
- `TIMEOUT_SECONDS`: Request timeout in seconds (default: 30)
- `TIMEOUT_EXCLUDE_PATHS`: Comma-separated list of paths to exclude from timeouts (default: /upload,/accounts/list/stream)

### Size Limit Configuration

- `SIZE_LIMIT_ENABLED`: Enable request size limiting (default: true)
- `SIZE_LIMIT_MAX_SIZE`: Maximum request size in bytes (default: 10485760)
- `SIZE_LIMIT_EXCLUDE_PATHS`: Comma-separated list of paths to exclude from size limiting (default: /upload)

### CORS Configuration

- `CORS_ENABLED`: Enable CORS (default: true)
- `CORS_ALLOW_ORIGINS`: Comma-separated list of allowed origins (default: *)
- `CORS_ALLOW_METHODS`: Comma-separated list of allowed methods (default: GET,POST,PUT,DELETE,OPTIONS)
- `CORS_ALLOW_HEADERS`: Comma-separated list of allowed headers (default: *)
- `CORS_ALLOW_CREDENTIALS`: Allow credentials (default: true)
- `CORS_MAX_AGE`: Maximum age of CORS preflight requests in seconds (default: 600)

## Configuration File

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
  pool_timeout: 30
  ssl: false
  ssl_ca: null
  ssl_cert: null
  ssl_key: null

jwt:
  secret: your_jwt_secret
  algorithm: HS256
  expiration: 86400
  refresh_expiration: 604800
  audience: null
  issuer: null

api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: false
  debug: false
  docs_url: /api/docs
  redoc_url: /api/redoc
  openapi_url: /openapi.json
  root_path: /

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null
  rotation: false
  rotation_size: 10485760
  rotation_count: 5

rate_limit:
  enabled: true
  window: 60
  max_requests: 100
  exclude_paths:
    - /health
    - /api/docs
    - /api/redoc
    - /openapi.json

timeout:
  enabled: true
  seconds: 30
  exclude_paths:
    - /upload
    - /accounts/list/stream

size_limit:
  enabled: true
  max_size: 10485760
  exclude_paths:
    - /upload

cors:
  enabled: true
  allow_origins:
    - "*"
  allow_methods:
    - GET
    - POST
    - PUT
    - DELETE
    - OPTIONS
  allow_headers:
    - "*"
  allow_credentials: true
  max_age: 600
```

## Database Configuration

### Connection Pool

The database connection pool is configured with the following parameters:

- `DB_POOL_MIN`: Minimum number of connections in the pool (default: 1)
- `DB_POOL_MAX`: Maximum number of connections in the pool (default: 10)
- `DB_POOL_TIMEOUT`: Connection timeout in seconds (default: 30)

For production environments, it's recommended to set `DB_POOL_MIN` to at least 5 and `DB_POOL_MAX` to at least 20.

### SSL Configuration

To enable SSL for the database connection, set `DB_SSL` to `true` and provide the paths to the SSL certificates:

```bash
DB_SSL=true
DB_SSL_CA=/path/to/ca.crt
DB_SSL_CERT=/path/to/client.crt
DB_SSL_KEY=/path/to/client.key
```

Or in the configuration file:

```yaml
database:
  # ...
  ssl: true
  ssl_ca: /path/to/ca.crt
  ssl_cert: /path/to/client.crt
  ssl_key: /path/to/client.key
```

## JWT Configuration

### Secret Key

The JWT secret key is used to sign and verify JWT tokens. It should be a strong, random string. You can generate a random string using the following command:

```bash
openssl rand -hex 32
```

Set the secret key using the `JWT_SECRET` environment variable or in the configuration file.

### Algorithm

The JWT algorithm is used to sign and verify JWT tokens. The default algorithm is HS256, which is a symmetric algorithm that uses the same secret key for signing and verification.

Other supported algorithms include:

- HS384
- HS512
- RS256
- RS384
- RS512
- ES256
- ES384
- ES512

For asymmetric algorithms (RS*, ES*), you need to provide the public and private keys:

```bash
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY=/path/to/private.pem
JWT_PUBLIC_KEY=/path/to/public.pem
```

Or in the configuration file:

```yaml
jwt:
  # ...
  algorithm: RS256
  private_key: /path/to/private.pem
  public_key: /path/to/public.pem
```

### Expiration

The JWT expiration time is specified in seconds. The default is 86400 seconds (24 hours).

For production environments, it's recommended to set a shorter expiration time (e.g., 3600 seconds) and implement token refresh.

## API Configuration

### Workers

The number of worker processes is configured with the `API_WORKERS` environment variable or in the configuration file. The default is 4 workers.

For production environments, it's recommended to set the number of workers to the number of CPU cores available.

### Debug Mode

Debug mode is configured with the `API_DEBUG` environment variable or in the configuration file. The default is `false`.

In debug mode, the API server provides more detailed error messages and enables auto-reload.

For production environments, it's recommended to set `API_DEBUG` to `false`.

### Documentation

The API documentation is configured with the following parameters:

- `API_DOCS_URL`: URL for the Swagger UI (default: /api/docs)
- `API_REDOC_URL`: URL for the ReDoc UI (default: /api/redoc)
- `API_OPENAPI_URL`: URL for the OpenAPI schema (default: /openapi.json)

To disable the API documentation, set these parameters to `null`:

```bash
API_DOCS_URL=null
API_REDOC_URL=null
API_OPENAPI_URL=null
```

Or in the configuration file:

```yaml
api:
  # ...
  docs_url: null
  redoc_url: null
  openapi_url: null
```

## Logging Configuration

### Log Level

The log level is configured with the `LOG_LEVEL` environment variable or in the configuration file. The default is `INFO`.

Available log levels:

- `DEBUG`: Detailed information, typically of interest only when diagnosing problems.
- `INFO`: Confirmation that things are working as expected.
- `WARNING`: An indication that something unexpected happened, or indicative of some problem in the near future.
- `ERROR`: Due to a more serious problem, the software has not been able to perform some function.
- `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running.

### Log Format

The log format is configured with the `LOG_FORMAT` environment variable or in the configuration file. The default is `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

Available format specifiers:

- `%(asctime)s`: Human-readable time when the log record was created.
- `%(created)f`: Time when the log record was created (as returned by time.time()).
- `%(filename)s`: Filename portion of pathname.
- `%(funcName)s`: Name of function containing the logging call.
- `%(levelname)s`: Text logging level for the message ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
- `%(levelno)s`: Numeric logging level for the message (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- `%(lineno)d`: Source line number where the logging call was issued (if available).
- `%(message)s`: The logged message.
- `%(module)s`: Module (name portion of filename).
- `%(name)s`: Name of the logger used to log the call.
- `%(pathname)s`: Full pathname of the source file where the logging call was issued (if available).
- `%(process)d`: Process ID (if available).
- `%(processName)s`: Process name (if available).
- `%(thread)d`: Thread ID (if available).
- `%(threadName)s`: Thread name (if available).

### Log File

The log file is configured with the `LOG_FILE` environment variable or in the configuration file. The default is `null`, which means logs are written to stdout.

To write logs to a file, set `LOG_FILE` to the path of the log file:

```bash
LOG_FILE=/var/log/accountdb/api.log
```

Or in the configuration file:

```yaml
logging:
  # ...
  file: /var/log/accountdb/api.log
```

### Log Rotation

Log rotation is configured with the following parameters:

- `LOG_ROTATION`: Enable log rotation (default: false)
- `LOG_ROTATION_SIZE`: Maximum size of log file before rotation in bytes (default: 10485760)
- `LOG_ROTATION_COUNT`: Number of rotated log files to keep (default: 5)

To enable log rotation, set `LOG_ROTATION` to `true`:

```bash
LOG_ROTATION=true
LOG_ROTATION_SIZE=10485760
LOG_ROTATION_COUNT=5
```

Or in the configuration file:

```yaml
logging:
  # ...
  rotation: true
  rotation_size: 10485760
  rotation_count: 5
```

## Rate Limiting Configuration

### Enabling Rate Limiting

Rate limiting is enabled by default. To disable rate limiting, set `RATE_LIMIT_ENABLED` to `false`:

```bash
RATE_LIMIT_ENABLED=false
```

Or in the configuration file:

```yaml
rate_limit:
  enabled: false
```

### Rate Limit Parameters

The rate limit parameters are configured with the following environment variables:

- `RATE_LIMIT_WINDOW`: Time window for rate limiting in seconds (default: 60)
- `RATE_LIMIT_MAX_REQUESTS`: Maximum number of requests per window (default: 100)

For production environments, it's recommended to set a lower rate limit (e.g., 60 requests per minute).

### Excluding Paths

You can exclude certain paths from rate limiting using the `RATE_LIMIT_EXCLUDE_PATHS` environment variable or in the configuration file. The default is `/health,/api/docs,/api/redoc,/openapi.json`.

To exclude additional paths, add them to the list:

```bash
RATE_LIMIT_EXCLUDE_PATHS=/health,/api/docs,/api/redoc,/openapi.json,/custom/path
```

Or in the configuration file:

```yaml
rate_limit:
  # ...
  exclude_paths:
    - /health
    - /api/docs
    - /api/redoc
    - /openapi.json
    - /custom/path
```

## Timeout Configuration

### Enabling Timeouts

Request timeouts are enabled by default. To disable timeouts, set `TIMEOUT_ENABLED` to `false`:

```bash
TIMEOUT_ENABLED=false
```

Or in the configuration file:

```yaml
timeout:
  enabled: false
```

### Timeout Parameters

The timeout parameters are configured with the following environment variables:

- `TIMEOUT_SECONDS`: Request timeout in seconds (default: 30)

For production environments, it's recommended to set a shorter timeout (e.g., 10 seconds) for most endpoints.

### Excluding Paths

You can exclude certain paths from timeouts using the `TIMEOUT_EXCLUDE_PATHS` environment variable or in the configuration file. The default is `/upload,/accounts/list/stream`.

To exclude additional paths, add them to the list:

```bash
TIMEOUT_EXCLUDE_PATHS=/upload,/accounts/list/stream,/custom/path
```

Or in the configuration file:

```yaml
timeout:
  # ...
  exclude_paths:
    - /upload
    - /accounts/list/stream
    - /custom/path
```

## Size Limit Configuration

### Enabling Size Limits

Request size limits are enabled by default. To disable size limits, set `SIZE_LIMIT_ENABLED` to `false`:

```bash
SIZE_LIMIT_ENABLED=false
```

Or in the configuration file:

```yaml
size_limit:
  enabled: false
```

### Size Limit Parameters

The size limit parameters are configured with the following environment variables:

- `SIZE_LIMIT_MAX_SIZE`: Maximum request size in bytes (default: 10485760)

For production environments, it's recommended to set a lower size limit (e.g., 1MB) for most endpoints.

### Excluding Paths

You can exclude certain paths from size limits using the `SIZE_LIMIT_EXCLUDE_PATHS` environment variable or in the configuration file. The default is `/upload`.

To exclude additional paths, add them to the list:

```bash
SIZE_LIMIT_EXCLUDE_PATHS=/upload,/custom/path
```

Or in the configuration file:

```yaml
size_limit:
  # ...
  exclude_paths:
    - /upload
    - /custom/path
```

## CORS Configuration

### Enabling CORS

CORS is enabled by default. To disable CORS, set `CORS_ENABLED` to `false`:

```bash
CORS_ENABLED=false
```

Or in the configuration file:

```yaml
cors:
  enabled: false
```

### CORS Parameters

The CORS parameters are configured with the following environment variables:

- `CORS_ALLOW_ORIGINS`: Comma-separated list of allowed origins (default: *)
- `CORS_ALLOW_METHODS`: Comma-separated list of allowed methods (default: GET,POST,PUT,DELETE,OPTIONS)
- `CORS_ALLOW_HEADERS`: Comma-separated list of allowed headers (default: *)
- `CORS_ALLOW_CREDENTIALS`: Allow credentials (default: true)
- `CORS_MAX_AGE`: Maximum age of CORS preflight requests in seconds (default: 600)

For production environments, it's recommended to set specific allowed origins instead of using the wildcard (*).

## Advanced Configuration

### Custom Middleware

You can add custom middleware to the API server by creating a Python module and adding it to the `middleware` directory. The module should define a class that inherits from `starlette.middleware.base.BaseHTTPMiddleware` and implements the `dispatch` method.

Example:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Do something before the request is processed
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Do something after the request is processed
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
```

Then, add the middleware to the API server in the `main.py` file:

```python
from middleware.custom import CustomMiddleware

app.add_middleware(CustomMiddleware)
```

### Custom Error Handlers

You can add custom error handlers to the API server by creating a Python module and adding it to the `error_handling` directory. The module should define a function that takes an exception and a request as parameters and returns a response.

Example:

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_404_NOT_FOUND

async def not_found_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=HTTP_404_NOT_FOUND,
        content={"detail": "The requested resource was not found"}
    )
```

Then, add the error handler to the API server in the `main.py` file:

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from error_handling.custom import not_found_error_handler

app.add_exception_handler(HTTP_404_NOT_FOUND, not_found_error_handler)
```

### Custom Logging

You can add custom logging by creating a Python module and adding it to the `logging` directory. The module should define a function that configures the logging system.

Example:

```python
import logging
import sys

def configure_logging(level=logging.INFO, format=None, file=None):
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Configure formatter
    formatter = logging.Formatter(format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Configure handlers
    handlers = []
    
    # Add stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    handlers.append(stdout_handler)
    
    # Add file handler if specified
    if file:
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Add handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)
    
    return root_logger
```

Then, use the custom logging configuration in the `main.py` file:

```python
from logging_config.custom import configure_logging

configure_logging(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    file=Config.LOG_FILE
)
```
