# Windows VM Agent Integration

## Objective

Enable the Windows VM agent to send logs to the central log storage system.

## Tasks

### 1. Create a simple logging client

- Implement a basic HTTP client that sends logs to the backend API
- Use the existing API key system for authentication
- Support for basic retry logic in case of connection issues

#### Implementation Details

- Create a new module in `windows_vm_agent/utils/log_client.py`
- Implement a `LogClient` class with methods for sending logs
- Use the existing API key configuration for authentication
- Include the following methods:
  - `send_log(message, level, category, details)` - Send a single log
  - `send_logs(logs)` - Send multiple logs in a batch
  - `flush()` - Send any pending logs

```python
# Example implementation
class LogClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.pending_logs = []
        
    def send_log(self, message, level="INFO", category=None, details=None):
        # Implementation details
        
    def send_logs(self, logs):
        # Implementation details
        
    def flush(self):
        # Implementation details
```

### 2. Update Windows VM agent logging

- Modify the agent to send important logs to the central system
- Focus on errors, warnings, and significant events
- Maintain local file logging for debugging purposes

#### Implementation Details

- Update the logging configuration in `windows_vm_agent/config/config_loader.py`
- Add configuration options for log forwarding:
  - `log_forwarding_enabled` (boolean)
  - `log_forwarding_level` (string: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
  - `log_forwarding_batch_size` (integer)
  - `log_forwarding_interval` (integer, seconds)

- Create a custom log handler in `windows_vm_agent/utils/log_handler.py`:
  - Extend Python's `logging.Handler` class
  - Buffer logs and send them in batches
  - Include VM and agent information in log details

```python
# Example implementation
class ApiLogHandler(logging.Handler):
    def __init__(self, log_client, level=logging.INFO):
        super().__init__(level)
        self.log_client = log_client
        self.buffer = []
        
    def emit(self, record):
        # Implementation details
        
    def flush(self):
        # Implementation details
```

- Integrate the log handler with the existing logging setup
- Add periodic flushing of logs to ensure timely delivery

## Timeline

- Logging client implementation: 0.5-1 day
- Windows VM agent logging updates: 0.5-1 day
- Total estimated time: 1-2 days

## Dependencies

- Existing Windows VM agent codebase
- Backend API endpoints for logs (already implemented)
- API key system for authentication

## Success Criteria

- Windows VM agent successfully sends logs to the central system
- Logs include appropriate context (VM ID, agent version, etc.)
- Local logging continues to work for debugging
- System handles network interruptions gracefully
