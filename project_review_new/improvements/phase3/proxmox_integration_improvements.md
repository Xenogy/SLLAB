# Phase 3: Proxmox Integration Improvements

## Overview

This phase focuses on improving the Proxmox host agent and integration to ensure reliable VM synchronization and management.

## Key Objectives

1. Improve Proxmox host agent configuration and error handling
2. Enhance whitelist implementation
3. Improve Proxmox node management

## Improvements

### 1. Proxmox Host Agent Improvements

#### Configuration Management

- Move hardcoded values to environment variables
- Add command-line arguments for configuration overrides
- Create a centralized configuration module

```python
# proxmox_host/config.py
import os
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Proxmox Host Agent')
parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 8000)), help='Port to run the server on')
parser.add_argument('--debug', action='store_true', default=os.getenv('DEBUG', 'false').lower() == 'true', help='Enable debug mode')
parser.add_argument('--log-level', default=os.getenv('LOG_LEVEL', 'info'), help='Log level')
parser.add_argument('--update-interval', type=int, default=int(os.getenv('UPDATE_INTERVAL', 300)), help='Update interval in seconds')
args = parser.parse_args()

# Configuration
config = {
    'port': args.port,
    'debug': args.debug,
    'log_level': args.log_level,
    'update_interval': args.update_interval,
    'proxmox': {
        'host': os.getenv('PROXMOX_HOST', 'localhost'),
        'user': os.getenv('PROXMOX_USER', 'root@pam'),
        'password': os.getenv('PROXMOX_PASSWORD', ''),
        'verify_ssl': os.getenv('PROXMOX_VERIFY_SSL', 'true').lower() == 'true',
        'node_name': os.getenv('PROXMOX_NODE_NAME', 'pve'),
    },
    'accountdb': {
        'url': os.getenv('ACCOUNTDB_URL', 'http://localhost:8000'),
        'api_key': os.getenv('ACCOUNTDB_API_KEY', ''),
        'node_id': int(os.getenv('ACCOUNTDB_NODE_ID', '0')),
    }
}
```

#### Error Handling

- Add retry mechanism for transient errors
- Implement graceful degradation for non-critical components
- Improve error logging

```python
# proxmox_host/utils/retry.py
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    attempt += 1
                    current_delay *= backoff
        
        return wrapper
    return decorator
```

#### Reconnection Logic

- Add automatic reconnection to AccountDB
- Implement exponential backoff for reconnection attempts

```python
# proxmox_host/accountdb_client.py
from utils.retry import retry

class AccountDBClient:
    # ...
    
    @retry(max_attempts=5, delay=5, backoff=2)
    async def verify_connection(self):
        """Verify the connection to the AccountDB API with retry."""
        # Implementation
```

### 2. Whitelist Implementation Improvements

#### Efficient Whitelist Caching

- Implement time-based cache invalidation
- Add conditional requests for whitelist retrieval

```python
# proxmox_host/main.py
# Whitelist cache
whitelist_cache = {
    'data': [],
    'last_updated': 0,
    'ttl': 300  # 5 minutes
}

async def get_whitelist():
    """Get the whitelist with caching."""
    current_time = int(time.time())
    
    # Check if cache is valid
    if whitelist_cache['data'] and current_time - whitelist_cache['last_updated'] < whitelist_cache['ttl']:
        logger.debug(f"Using cached whitelist (age: {current_time - whitelist_cache['last_updated']} seconds)")
        return whitelist_cache['data']
    
    # Cache is invalid, fetch new whitelist
    try:
        whitelist = await accountdb_client.get_vmid_whitelist()
        whitelist_cache['data'] = whitelist
        whitelist_cache['last_updated'] = current_time
        logger.info(f"Updated whitelist cache with {len(whitelist)} VMIDs")
        return whitelist
    except Exception as e:
        logger.error(f"Error retrieving whitelist: {e}")
        # Return cached data if available, even if expired
        if whitelist_cache['data']:
            logger.warning(f"Using expired cached whitelist due to error")
            return whitelist_cache['data']
        # No cache available
        return []
```

#### Optimized Whitelist Filtering

- Improve whitelist filtering performance
- Use set operations for efficient filtering

```python
# proxmox_host/main.py
async def sync_vms():
    """Synchronize VMs between Proxmox and AccountDB."""
    try:
        # Get VMs from Proxmox
        vms = proxmox_client.get_vms()
        logger.info(f"Retrieved {len(vms)} VMs from Proxmox")
        
        # Get whitelist
        whitelist = await get_whitelist()
        whitelist_enabled = len(whitelist) > 0
        
        # Filter VMs based on whitelist if enabled
        if whitelist_enabled:
            # Convert whitelist to a set for O(1) lookups
            whitelist_set = set(whitelist)
            filtered_vms = [vm for vm in vms if vm.get('vmid') in whitelist_set]
            logger.info(f"Filtered VMs based on whitelist: {len(filtered_vms)} of {len(vms)} VMs will be synced")
            vms = filtered_vms
        
        # Sync with AccountDB
        await accountdb_client.sync_vms(vms)
    except Exception as e:
        logger.error(f"Error during VM synchronization: {e}")
```

### 3. Proxmox Node Management Improvements

#### Health Checks

- Add health check endpoint for Proxmox API
- Implement periodic health checks

```python
# proxmox_host/main.py
@app.get("/health/proxmox")
async def proxmox_health_check():
    """Health check for Proxmox API."""
    try:
        # Check if we can connect to Proxmox API
        vms = proxmox_client.get_vms()
        return {
            "status": "ok",
            "message": f"Successfully connected to Proxmox API and retrieved {len(vms)} VMs",
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to Proxmox API: {str(e)}",
            "timestamp": int(time.time())
        }
```

#### Improved Status Monitoring

- Add detailed status information
- Implement status history

```python
# proxmox_host/main.py
# Status tracking
status_history = []
max_history_entries = 10

def update_status(status, message):
    """Update status history."""
    status_entry = {
        "status": status,
        "message": message,
        "timestamp": int(time.time())
    }
    
    # Add to history
    status_history.append(status_entry)
    
    # Trim history if needed
    if len(status_history) > max_history_entries:
        status_history.pop(0)
    
    return status_entry

@app.get("/status")
async def get_status():
    """Get detailed status information."""
    return {
        "current": status_history[-1] if status_history else None,
        "history": status_history,
        "proxmox": {
            "host": config['proxmox']['host'],
            "node": config['proxmox']['node_name'],
            "connected": proxmox_client.is_connected()
        },
        "accountdb": {
            "url": config['accountdb']['url'],
            "node_id": config['accountdb']['node_id'],
            "connected": await accountdb_client.verify_connection()
        },
        "sync": {
            "last_sync_time": last_sync_time,
            "next_sync_time": last_sync_time + config['update_interval'],
            "update_interval": config['update_interval']
        }
    }
```

## Implementation Steps

1. Update Proxmox host agent configuration
   - Move hardcoded values to environment variables
   - Add command-line arguments
   - Create centralized configuration

2. Improve error handling
   - Add retry mechanism
   - Implement graceful degradation
   - Improve error logging

3. Add reconnection logic
   - Implement automatic reconnection
   - Add exponential backoff

4. Enhance whitelist implementation
   - Implement efficient caching
   - Optimize whitelist filtering

5. Improve Proxmox node management
   - Add health checks
   - Implement status monitoring

## Expected Outcomes

- More reliable Proxmox host agent
- Better error handling and recovery
- Improved performance with efficient whitelist implementation
- Better monitoring and status information
