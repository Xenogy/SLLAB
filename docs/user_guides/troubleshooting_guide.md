# AccountDB Troubleshooting Guide

## Introduction

This guide provides solutions to common issues you might encounter when using the AccountDB system. It covers installation problems, configuration issues, API errors, and performance concerns.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Database Issues](#database-issues)
4. [API Issues](#api-issues)
5. [Authentication Issues](#authentication-issues)
6. [Performance Issues](#performance-issues)
7. [Common Error Codes](#common-error-codes)
8. [Logging and Debugging](#logging-and-debugging)
9. [Getting Help](#getting-help)

## Installation Issues

### Docker Installation Issues

#### Docker Compose Not Found

**Problem**: `docker-compose` command not found.

**Solution**:
1. Install Docker Compose:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```
2. Verify installation:
   ```bash
   docker-compose --version
   ```

#### Container Fails to Start

**Problem**: Docker container fails to start.

**Solution**:
1. Check the container logs:
   ```bash
   docker-compose logs api
   ```
2. Verify that the required environment variables are set in the `.env` file.
3. Check if the ports are already in use:
   ```bash
   sudo lsof -i :8000
   ```
4. Ensure that the database container is running:
   ```bash
   docker-compose ps
   ```

### Manual Installation Issues

#### Python Version

**Problem**: Incompatible Python version.

**Solution**:
1. Check your Python version:
   ```bash
   python --version
   ```
2. Install Python 3.9 or later:
   ```bash
   # Ubuntu
   sudo apt update
   sudo apt install python3.9 python3.9-venv python3.9-dev
   
   # macOS
   brew install python@3.9
   
   # Windows
   # Download from https://www.python.org/downloads/
   ```

#### Package Installation Fails

**Problem**: Package installation fails with dependency errors.

**Solution**:
1. Update pip:
   ```bash
   pip install --upgrade pip
   ```
2. Install the required system packages:
   ```bash
   # Ubuntu
   sudo apt update
   sudo apt install build-essential libpq-dev
   
   # macOS
   brew install postgresql
   
   # Windows
   # Install Visual C++ Build Tools
   ```
3. Try installing the packages again:
   ```bash
   pip install -r backend/requirements.txt
   ```

## Configuration Issues

### Environment Variables Not Set

**Problem**: Environment variables are not being recognized.

**Solution**:
1. Check if the environment variables are set:
   ```bash
   # Linux/macOS
   echo $DB_HOST
   
   # Windows
   echo %DB_HOST%
   ```
2. Set the environment variables:
   ```bash
   # Linux/macOS
   export DB_HOST=localhost
   
   # Windows
   set DB_HOST=localhost
   ```
3. Alternatively, create a `.env` file in the root directory:
   ```bash
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=accountdb
   DB_USER=accountdb
   DB_PASS=your_password
   ```

### Configuration File Not Found

**Problem**: Configuration file not found.

**Solution**:
1. Create a `config.yaml` file in the root directory:
   ```yaml
   database:
     host: localhost
     port: 5432
     name: accountdb
     user: accountdb
     password: your_password
   
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
   ```
2. Make sure the file has the correct permissions:
   ```bash
   chmod 600 config.yaml
   ```

## Database Issues

### Connection Refused

**Problem**: Database connection refused.

**Solution**:
1. Check if the PostgreSQL server is running:
   ```bash
   # Ubuntu
   sudo systemctl status postgresql
   
   # macOS
   brew services list
   
   # Docker
   docker-compose ps
   ```
2. Start the PostgreSQL server if it's not running:
   ```bash
   # Ubuntu
   sudo systemctl start postgresql
   
   # macOS
   brew services start postgresql
   
   # Docker
   docker-compose up -d postgres
   ```
3. Check the database connection parameters:
   ```bash
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
   ```

### Authentication Failed

**Problem**: Database authentication failed.

**Solution**:
1. Check the database user and password:
   ```bash
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
   ```
2. Reset the database user password:
   ```bash
   sudo -u postgres psql
   ALTER USER accountdb WITH PASSWORD 'new_password';
   ```
3. Update the configuration with the new password.

### Database Does Not Exist

**Problem**: Database does not exist.

**Solution**:
1. Create the database:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE accountdb;
   GRANT ALL PRIVILEGES ON DATABASE accountdb TO accountdb;
   ```
2. Run the database initialization script:
   ```bash
   # Docker
   docker-compose exec api python -m scripts.init_db
   
   # Manual
   python -m scripts.init_db
   ```

### Migration Failed

**Problem**: Database migration failed.

**Solution**:
1. Check the migration logs:
   ```bash
   # Docker
   docker-compose logs api
   
   # Manual
   cat logs/api.log
   ```
2. Run the migration manually:
   ```bash
   # Docker
   docker-compose exec api python -m scripts.run_migration
   
   # Manual
   python -m scripts.run_migration
   ```
3. If the migration still fails, try resetting the database:
   ```bash
   sudo -u postgres psql
   DROP DATABASE accountdb;
   CREATE DATABASE accountdb;
   GRANT ALL PRIVILEGES ON DATABASE accountdb TO accountdb;
   ```
   Then run the initialization script again.

## API Issues

### API Server Not Starting

**Problem**: API server fails to start.

**Solution**:
1. Check the API server logs:
   ```bash
   # Docker
   docker-compose logs api
   
   # Manual
   cat logs/api.log
   ```
2. Verify that the required environment variables are set.
3. Check if the port is already in use:
   ```bash
   sudo lsof -i :8000
   ```
4. Try starting the API server with debug mode:
   ```bash
   # Docker
   docker-compose run --rm api uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   
   # Manual
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Endpoint Not Found

**Problem**: API endpoint returns 404 Not Found.

**Solution**:
1. Check the API documentation to verify the endpoint URL:
   ```
   http://localhost:8000/api/docs
   ```
2. Make sure you're using the correct HTTP method (GET, POST, PUT, DELETE).
3. Check if the API server is running:
   ```bash
   # Docker
   docker-compose ps
   
   # Manual
   ps aux | grep uvicorn
   ```

### Request Validation Error

**Problem**: API request returns 422 Unprocessable Entity.

**Solution**:
1. Check the request body against the API documentation.
2. Make sure all required fields are provided.
3. Make sure the field types are correct.
4. Check for any validation constraints (e.g., minimum length, pattern).

### Rate Limiting

**Problem**: API request returns 429 Too Many Requests.

**Solution**:
1. Reduce the frequency of requests.
2. Check the rate limit headers in the response:
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 0
   X-RateLimit-Reset: 30
   ```
3. Wait until the rate limit resets before making more requests.
4. If you need a higher rate limit, contact the API administrator.

### Request Timeout

**Problem**: API request returns 504 Gateway Timeout.

**Solution**:
1. Check if the request is taking too long to process.
2. Try breaking down the request into smaller chunks.
3. If you're uploading a large file, try using a smaller file or the streaming endpoint.
4. Check the server logs for any performance issues.

## Authentication Issues

### Token Generation Failed

**Problem**: Unable to generate a JWT token.

**Solution**:
1. Check the username and password:
   ```http
   POST /auth/token
   Content-Type: application/json
   
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```
2. Make sure the user exists in the database:
   ```bash
   sudo -u postgres psql -d accountdb
   SELECT * FROM users WHERE username = 'your_username';
   ```
3. Reset the user password if necessary:
   ```bash
   sudo -u postgres psql -d accountdb
   UPDATE users SET password_hash = 'new_password_hash' WHERE username = 'your_username';
   ```
   Note: The password hash should be generated using the same algorithm as the API server.

### Token Verification Failed

**Problem**: JWT token verification failed.

**Solution**:
1. Make sure you're including the token in the `Authorization` header:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
2. Check if the token has expired. Tokens expire after 24 hours by default.
3. Generate a new token if necessary.
4. Make sure the JWT secret is configured correctly on the server.

### Insufficient Permissions

**Problem**: API request returns 403 Forbidden.

**Solution**:
1. Check if the user has the necessary permissions.
2. Regular users can only access their own accounts, hardware profiles, and cards.
3. Administrators can access all accounts, hardware profiles, and cards.
4. If you need additional permissions, contact the API administrator.

## Performance Issues

### Slow API Responses

**Problem**: API responses are slow.

**Solution**:
1. Use cursor-based pagination for large datasets:
   ```http
   GET /accounts/list/cursor?limit=100
   ```
2. Use field selection to reduce the response size:
   ```http
   GET /accounts/list/fields?fields=acc_id,acc_username,acc_email_address
   ```
3. Use streaming for large datasets:
   ```http
   GET /accounts/list/stream?limit=1000
   ```
4. Check the server logs for any performance issues.
5. Consider increasing the number of API workers:
   ```bash
   # Docker
   docker-compose up -d --scale api=4
   
   # Manual
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Database Performance

**Problem**: Database queries are slow.

**Solution**:
1. Check if the database indexes are created:
   ```bash
   sudo -u postgres psql -d accountdb
   \d accounts
   ```
2. Run the performance indexes migration:
   ```bash
   # Docker
   docker-compose exec api python -m scripts.run_performance_migration
   
   # Manual
   python -m scripts.run_performance_migration
   ```
3. Analyze the database tables:
   ```bash
   sudo -u postgres psql -d accountdb
   ANALYZE accounts;
   ```
4. Check the database connection pool configuration:
   ```bash
   # Docker
   docker-compose exec api python -c "from db import get_pool_stats; print(get_pool_stats())"
   
   # Manual
   python -c "from db import get_pool_stats; print(get_pool_stats())"
   ```

### Memory Usage

**Problem**: High memory usage.

**Solution**:
1. Check the memory usage:
   ```bash
   # Docker
   docker stats
   
   # Manual
   ps aux | grep uvicorn
   ```
2. Use streaming for large datasets:
   ```http
   GET /accounts/list/stream?limit=1000
   ```
3. Reduce the number of API workers if necessary:
   ```bash
   # Docker
   docker-compose up -d --scale api=2
   
   # Manual
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
   ```
4. Increase the available memory if possible.

## Common Error Codes

### HTTP Status Codes

- `200 OK`: The request was successful.
- `201 Created`: The resource was created successfully.
- `204 No Content`: The request was successful, but there is no content to return.
- `400 Bad Request`: The request was invalid.
- `401 Unauthorized`: Authentication is required.
- `403 Forbidden`: The authenticated user does not have permission to access the requested resource.
- `404 Not Found`: The requested resource was not found.
- `422 Unprocessable Entity`: The request was well-formed but was unable to be followed due to semantic errors.
- `429 Too Many Requests`: The user has sent too many requests in a given amount of time.
- `500 Internal Server Error`: An error occurred on the server.
- `504 Gateway Timeout`: The server did not receive a timely response from an upstream server.

### API Error Responses

API error responses have the following format:

```json
{
  "detail": "Error message"
}
```

For validation errors, the response includes more details:

```json
{
  "detail": [
    {
      "loc": ["body", "acc_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Logging and Debugging

### Viewing Logs

#### Docker Logs

```bash
# View all logs
docker-compose logs

# View API logs
docker-compose logs api

# Follow API logs
docker-compose logs -f api

# View the last 100 lines of API logs
docker-compose logs --tail=100 api
```

#### Manual Logs

```bash
# View log file
cat logs/api.log

# Follow log file
tail -f logs/api.log

# View the last 100 lines of the log file
tail -n 100 logs/api.log
```

### Enabling Debug Mode

#### Docker

```bash
# Edit the .env file
echo "API_DEBUG=true" >> .env

# Restart the API container
docker-compose restart api
```

#### Manual

```bash
# Set the environment variable
export API_DEBUG=true

# Start the API server with reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Debugging Database Queries

#### Docker

```bash
# Enable query logging
docker-compose exec postgres psql -U accountdb -d accountdb -c "ALTER SYSTEM SET log_statement = 'all';"
docker-compose exec postgres psql -U accountdb -d accountdb -c "SELECT pg_reload_conf();"

# View query logs
docker-compose logs postgres
```

#### Manual

```bash
# Enable query logging
sudo -u postgres psql -d accountdb -c "ALTER SYSTEM SET log_statement = 'all';"
sudo -u postgres psql -d accountdb -c "SELECT pg_reload_conf();"

# View query logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

## Getting Help

If you need further assistance, please contact the AccountDB support team or open an issue on the GitHub repository.

### Support Channels

- **Email**: support@accountdb.example.com
- **GitHub Issues**: https://github.com/your-organization/accountdb/issues
- **Documentation**: https://docs.accountdb.example.com

### Reporting Issues

When reporting issues, please include the following information:

1. **Issue Description**: A clear and concise description of the issue.
2. **Steps to Reproduce**: Step-by-step instructions to reproduce the issue.
3. **Expected Behavior**: What you expected to happen.
4. **Actual Behavior**: What actually happened.
5. **Environment**: Information about your environment (OS, Docker version, Python version, etc.).
6. **Logs**: Relevant logs from the API server and database.
7. **Screenshots**: If applicable, add screenshots to help explain your problem.

### Feature Requests

If you have a feature request, please include the following information:

1. **Feature Description**: A clear and concise description of the feature.
2. **Use Case**: How this feature would be used.
3. **Alternatives**: Any alternative solutions or features you've considered.
4. **Additional Context**: Any other context or screenshots about the feature request.
