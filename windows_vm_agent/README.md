# Dynamic Windows VM Agent

A configurable Windows agent that monitors for various predefined events within the VM (initially log file patterns), pulls necessary data from a central manager API when triggered, and executes corresponding predefined local scripts.

## Features

- **Configurable Event Monitoring**: Monitor log files for specific patterns using regular expressions.
- **Dynamic API Data Retrieval**: Pull data from a central manager API when events are triggered.
- **Flexible Script Execution**: Execute PowerShell scripts with parameters from API responses or event data.
- **Centralized Logging**: Send logs to the central log storage system for monitoring and troubleshooting.
- **Extensible Architecture**: Easily add new monitor types and action handlers.
- **API Key Authentication**: Uses the AccountDB centralized API key system for secure authentication.
- **User-Specific Data Access**: Respects Row-Level Security to ensure users only access their own data.

## Prerequisites

- Windows 7 or later (Windows 10/11 recommended)
- Python 3.7 or later
- PowerShell 3.0 or later

## Installation

### 1. Install Python

If Python is not already installed, download and install it from [python.org](https://www.python.org/downloads/windows/).

### 2. Clone or Download the Repository

```
git clone https://github.com/yourusername/windows_vm_agent.git
cd windows_vm_agent
```

### 3. Install the Agent

```
pip install -e .
```

### 4. Create Configuration

Copy the example configuration file and modify it for your environment:

```
copy config.yaml C:\CsBotAgent\config.yaml
```

Edit the configuration file to set your VM identifier, API key, manager URL, and configure monitors and actions.

#### Obtaining an API Key

To obtain an API key for the Windows VM agent:

1. Log in to the AccountDB web interface
2. Navigate to the Settings page
3. Go to the API Keys tab
4. Click "Create API Key"
5. Enter a name for the key (e.g., "Windows VM Agent - VM123")
6. Select "windows_vm" as the key type
7. Enter the VM ID in the Resource ID field
8. Click "Create"
9. Copy the generated API key (it will only be shown once)
10. Paste the API key into the `APIKey` field in the configuration file

### 5. Create Scripts Directory

Create a directory for action scripts:

```
mkdir C:\CsBotAgent\ActionScripts
```

Copy the sample scripts from the `action_scripts` directory to this location.

## Configuration

The agent is configured using a YAML file. Here's an example configuration:

```yaml
General:
  VMIdentifier: "VM_HOSTNAME_OR_ID"  # Or fetch dynamically
  APIKey: "YOUR_SECURE_API_KEY"  # Better: Load from env var or secure store
  ManagerBaseURL: "https://your-manager.com/api"
  ScriptsPath: "C:\\CsBotAgent\\ActionScripts"

EventMonitors:
  - Name: "AccountLoginMonitor"
    Type: "LogFileTail"
    LogFilePath: "C:\\Path\\To\\CSBot\\bot.log"
    EventTriggers:
      - EventName: "AccountLoginDetected"
        # Regex to capture the account ID from a log line
        Regex: 'User logged in:\s+(?P<account_id>\w+)'
        # Action to perform when this regex matches
        Action: "UpdateProxyForAccount"

  - Name: "ErrorMonitor"
    Type: "LogFileTail"
    LogFilePath: "C:\\Path\\To\\CSBot\\error.log"
    EventTriggers:
      - EventName: "CriticalErrorDetected"
        Regex: 'CRITICAL ERROR CODE: (?P<error_code>\d+)'
        Action: "NotifyError"  # Example: Could trigger a script that POSTs to manager

Actions:
  - Name: "UpdateProxyForAccount"
    # API endpoint to call to get data needed for the script
    APIDataEndpoint: "/account-config?vm_id={VMIdentifier}&account_id={account_id}"  # Placeholders filled from event
    # Script to execute with data returned from API
    Script: "Set-Proxy.ps1"
    # Map API response fields to script parameters (case-sensitive)
    ParameterMapping:
      ProxyAddress: "proxy_server"  # Script param : API JSON key
      BypassList: "proxy_bypass"

  - Name: "NotifyError"
    # This action might not need external data, just runs a script
    Script: "Send-Notification.ps1"  # This script might contain API call logic itself
    # Map event capture groups directly to script parameters
    ParameterMapping:
      ErrorCode: "error_code"  # Script param : Regex capture group name
```

## Running the Agent

### Manual Execution

Run the agent from the command line:

```
windows-vm-agent --config C:\CsBotAgent\config.yaml
```

### Install as a Windows Service

To run the agent as a Windows service, you can use NSSM (Non-Sucking Service Manager):

1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Install the service:

```
nssm install WindowsVMAgent "C:\Python310\python.exe" "-m windows_vm_agent.main --config C:\CsBotAgent\config.yaml"
nssm set WindowsVMAgent DisplayName "Windows VM Agent"
nssm set WindowsVMAgent Description "Dynamic Windows VM Agent for monitoring and executing actions"
nssm set WindowsVMAgent Start SERVICE_AUTO_START
nssm start WindowsVMAgent
```

## Creating Action Scripts

Action scripts are PowerShell scripts that are executed when events are triggered. They should:

1. Use the `param()` block to define parameters
2. Return exit code 0 for success, non-zero for failure
3. Include proper error handling and logging

Example script:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$ProxyAddress,

    [Parameter(Mandatory=$false)]
    [string]$BypassList = "localhost,127.0.0.1"
)

try {
    # Script logic here
    exit 0
}
catch {
    Write-Error "Error: $_"
    exit 1
}
```

## Security Considerations

- Store API keys securely (environment variables or Windows credential manager)
- Restrict access to the configuration file and scripts directory
- Validate all data received from the API before using it in scripts
- Only execute scripts from the designated scripts directory

## Centralized Logging

The agent automatically sends logs to the central log system.

### Log Types

- **INFO**: Normal operations (startup, configuration loaded)
- **WARNING**: Potential issues (high resource usage)
- **ERROR**: Problems that need attention
- **CRITICAL**: Severe issues requiring immediate action

### Using Logs in Scripts

```python
from utils.log_client import LogClient

# Get the log client from the agent
log_client = LogClient(api_url, api_key, vm_id)

# Log basic messages
log_client.log_info("Script started")
log_client.log_error("Script failed", exception=e)

# Log with additional details
log_client.log_warning("Resource usage high",
                      details={"cpu": 90, "memory": 85})
```

## Troubleshooting

Logs are stored in the `logs` directory within the agent installation directory. For more verbose logging, run the agent with the `--log-level DEBUG` option. Additionally, all logs are sent to the central log storage system and can be viewed in the web interface at `/logs`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
