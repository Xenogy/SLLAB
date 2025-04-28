# Database Monitoring and Health Checks

This directory contains modules for monitoring database performance and health.

## Overview

The database monitoring and health checks include:

1. **Query Analysis**: Analyzing query performance and identifying slow queries
2. **Query Caching**: Caching query results to improve performance
3. **Database Monitoring**: Monitoring database performance and resource usage
4. **Health Checks**: Checking database health and performing automatic recovery

## Modules

### Query Analyzer

The `query_analyzer.py` module provides functions for analyzing query performance and identifying slow queries.

```python
from db.query_analyzer import query_analyzer

# Use the query_analyzer context manager to track query performance
with query_analyzer(query, params):
    cursor.execute(query, params)
```

### Query Cache

The `query_cache.py` module provides functions for caching query results to improve performance.

```python
from db.query_cache import cached_query

# Use the cached_query decorator to cache query results
@cached_query()
def get_data(query, params):
    # Execute query and return results
```

### Database Monitoring

The `monitoring.py` module provides functions for monitoring database performance and resource usage.

```python
from db.monitoring import get_monitoring_data, get_alerts

# Get monitoring data
data = get_monitoring_data()

# Get alerts
alerts = get_alerts()
```

### Health Checks

The `health_checks.py` module provides functions for checking database health and performing automatic recovery.

```python
from db.health_checks import get_health_check_data, get_health_check_report

# Get health check data
data = get_health_check_data()

# Get health check report
report = get_health_check_report()
```

## API Endpoints

The monitoring and health checks are exposed through the following API endpoints:

- `/monitoring/health`: Check the health of the database (public)
- `/monitoring/health/details`: Get detailed health check information (admin only)
- `/monitoring/health/report`: Get a health check report (admin only)
- `/monitoring/database`: Get database monitoring data (admin only)
- `/monitoring/database/report`: Get a database monitoring report (admin only)
- `/monitoring/alerts`: Get monitoring alerts (admin only)
- `/monitoring/queries`: Get query statistics (admin only)
- `/monitoring/queries/slow`: Get slow queries (admin only)
- `/monitoring/queries/report`: Get a query performance report (admin only)
- `/monitoring/cache`: Get cache statistics (admin only)
- `/monitoring/cache/report`: Get a cache report (admin only)

## Configuration

The monitoring and health checks can be configured through environment variables:

- `ENABLE_QUERY_ANALYSIS`: Enable or disable query analysis (default: `true`)
- `SLOW_QUERY_THRESHOLD`: Threshold for slow queries in seconds (default: `0.5`)
- `VERY_SLOW_QUERY_THRESHOLD`: Threshold for very slow queries in seconds (default: `2.0`)
- `ENABLE_QUERY_CACHE`: Enable or disable query caching (default: `true`)
- `QUERY_CACHE_TTL`: Time-to-live for cached queries in seconds (default: `60`)
- `QUERY_CACHE_SIZE`: Maximum number of cached queries (default: `100`)
- `ENABLE_MONITORING`: Enable or disable database monitoring (default: `true`)
- `MONITORING_INTERVAL`: Monitoring interval in seconds (default: `60`)
- `ENABLE_HEALTH_CHECKS`: Enable or disable health checks (default: `true`)
- `HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: `60`)
- `ENABLE_AUTO_RECOVERY`: Enable or disable automatic recovery (default: `true`)
- `MAX_RECOVERY_ATTEMPTS`: Maximum number of recovery attempts (default: `3`)
- `RECOVERY_COOLDOWN`: Recovery cooldown period in seconds (default: `300`)

## Automatic Initialization

The monitoring and health checks are automatically initialized during application startup:

```python
# Initialize database monitoring and health checks
from db.monitoring import init_monitoring
from db.health_checks import init_health_checks
init_monitoring()
init_health_checks()
```

## Automatic Shutdown

The monitoring and health checks are automatically shutdown during application shutdown:

```python
# Shutdown database monitoring and health checks
from db.monitoring import shutdown_monitoring
from db.health_checks import shutdown_health_checks
shutdown_monitoring()
shutdown_health_checks()
```

## Integration with Repository Pattern

The query analyzer and query cache are integrated with the repository pattern through the `DatabaseAccess` class:

```python
class DatabaseAccess:
    @cached_query()
    def execute_query(self, query, params=None, with_rls=True):
        with self.get_connection(with_rls) as conn:
            cursor = conn.cursor()
            try:
                with query_analyzer(query, params):
                    cursor.execute(query, params or ())
                # Process results and return
            finally:
                cursor.close()
```

This ensures that all database operations are automatically analyzed and cached.
