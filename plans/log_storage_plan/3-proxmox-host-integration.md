# Proxmox Host Agent Integration

## Objective

Enable the Proxmox host agent to send logs to the central log storage system.

## Tasks

### 1. Create a simple logging client

- Implement a basic HTTP client that sends logs to the backend API
- Use the existing API key system for authentication
- Focus on simplicity and reliability

#### Implementation Details

- Create a new module in `proxmox_host/log_client.py`
- Implement a `LogClient` class with methods for sending logs
- Use the existing API key configuration for authentication
- Integrate with the loguru library that's already used in the Proxmox host agent

```python
# Example implementation
class LogClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        
    def send_log(self, message, level="INFO", category=None, details=None):
        # Implementation details
        
    def create_loguru_sink(self):
        # Create a loguru sink that sends logs to the API
        def sink(message):
            record = message.record
            self.send_log(
                message=record["message"],
                level=record["level"].name,
                category="proxmox_host",
                details={
                    "function": record["function"],
                    "file": record["file"].name,
                    "line": record["line"],
                    "process": record["process"].id,
                    "exception": record["exception"]
                }
            )
        return sink
```

### 2. Update Proxmox host agent logging

- Send important events and errors to the central log system
- Maintain local logging for debugging
- Add configuration options for log forwarding

#### Implementation Details

- Update the configuration in `proxmox_host/config.py`
- Add configuration options for log forwarding:
  - `log_forwarding_enabled` (boolean)
  - `log_forwarding_level` (string: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

- Integrate the log client with the existing loguru setup in `proxmox_host/main.py`:

```python
# Example integration
from log_client import LogClient

# Configure logger with API sink
if config.log_forwarding_enabled:
    log_client = LogClient(config.api_url, config.api_key)
    log_level = getattr(logging, config.log_forwarding_level, logging.INFO)
    logger.add(
        log_client.create_loguru_sink(),
        level=config.log_forwarding_level,
        format="{message}"  # Simplified format since details are handled in the sink
    )
```

- Add error handling to ensure logging issues don't affect the main application
- Include Proxmox host information in log details (hostname, node ID, etc.)

## Timeline

- Logging client implementation: 0.5-1 day
- Proxmox host agent logging updates: 0.5-1 day
- Total estimated time: 1-2 days

## Dependencies

- Existing Proxmox host agent codebase
- Backend API endpoints for logs (already implemented)
- API key system for authentication

## Success Criteria

- Proxmox host agent successfully sends logs to the central system
- Logs include appropriate context (host ID, node name, etc.)
- Local logging continues to work for debugging
- System handles network interruptions gracefully
