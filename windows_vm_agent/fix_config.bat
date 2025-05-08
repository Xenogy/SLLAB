@echo off
echo Fixing Windows VM Agent Config...

REM Define paths
set CONFIG_PATH=C:\CsBotAgent\config.yaml
set BACKUP_PATH=C:\CsBotAgent\config.yaml.bak
set FIXED_PATH=C:\CsBotAgent\config.yaml.fixed

REM Check if config file exists
if not exist "%CONFIG_PATH%" (
    echo Error: Config file not found at %CONFIG_PATH%
    exit /b 1
)

REM Create a backup of the original config
echo Creating backup of original config file...
copy "%CONFIG_PATH%" "%BACKUP_PATH%" /Y
echo Backup created at %BACKUP_PATH%

REM Create the fixed config file
echo Creating fixed config file...
echo General: > "%FIXED_PATH%"
echo   VMIdentifier: "TEST_VM"  # VM ID from Proxmox or other virtualization platform >> "%FIXED_PATH%"
echo   # API key generated from the Settings page in the web interface >> "%FIXED_PATH%"
echo   # Go to Settings ^> API Keys ^> Create API Key ^> Select "windows_vm" as key type and enter the VM ID >> "%FIXED_PATH%"
echo   APIKey: "f6Nk0DUz0D4nlo9mulQ4fI_VHJXnvcj4zuo3fOTAQPA" >> "%FIXED_PATH%"
echo   # Base URL for the API - should be the root URL of the server, not including /api >> "%FIXED_PATH%"
echo   # The agent will automatically try both with and without /api if needed >> "%FIXED_PATH%"
echo   ManagerBaseURL: "https://cs2.drandex.org" >> "%FIXED_PATH%"
echo   # Fixed path using forward slashes - Windows accepts these just fine >> "%FIXED_PATH%"
echo   ScriptsPath: "C:/CsBotAgent/action_scripts" >> "%FIXED_PATH%"
echo   LoggingEnabled: true  # Enable logging to central storage >> "%FIXED_PATH%"
echo   LogLevel: "INFO"  # Minimum level for logs sent to central storage (DEBUG, INFO, WARNING, ERROR, CRITICAL) >> "%FIXED_PATH%"
echo. >> "%FIXED_PATH%"
echo EventMonitors: >> "%FIXED_PATH%"
echo   - Name: "AccountLoginMonitor" >> "%FIXED_PATH%"
echo     Type: "LogFileTail" >> "%FIXED_PATH%"
echo     LogFilePath: "C:/CsBotAgent/logs/bot.log" >> "%FIXED_PATH%"
echo     CheckIntervalSeconds: 1.0 >> "%FIXED_PATH%"
echo     EventTriggers: >> "%FIXED_PATH%"
echo       - EventName: "AccountLoginDetected" >> "%FIXED_PATH%"
echo         # Regex to capture the account ID from a log line >> "%FIXED_PATH%"
echo         Regex: 'User logged in:\s+(?P<account_id>\w+)' >> "%FIXED_PATH%"
echo         # Action to perform when this regex matches >> "%FIXED_PATH%"
echo         Action: "UpdateProxyForAccount" >> "%FIXED_PATH%"
echo. >> "%FIXED_PATH%"
echo   - Name: "ErrorMonitor" >> "%FIXED_PATH%"
echo     Type: "LogFileTail" >> "%FIXED_PATH%"
echo     LogFilePath: "C:/CsBotAgent/logs/error.log" >> "%FIXED_PATH%"
echo     CheckIntervalSeconds: 1.0 >> "%FIXED_PATH%"
echo     EventTriggers: >> "%FIXED_PATH%"
echo       - EventName: "CriticalErrorDetected" >> "%FIXED_PATH%"
echo         Regex: 'CRITICAL ERROR CODE: (?P<error_code>\d+)' >> "%FIXED_PATH%"
echo         Action: "NotifyError"  # Example: Could trigger a script that POSTs to manager >> "%FIXED_PATH%"
echo. >> "%FIXED_PATH%"
echo Actions: >> "%FIXED_PATH%"
echo   - Name: "UpdateProxyForAccount" >> "%FIXED_PATH%"
echo     # API endpoint to call to get data needed for the script >> "%FIXED_PATH%"
echo     APIDataEndpoint: "/windows-vm-agent/account-config?vm_id={VMIdentifier}&account_id={account_id}"  # Placeholders filled from event >> "%FIXED_PATH%"
echo     # Script to execute with data returned from API >> "%FIXED_PATH%"
echo     Script: "Set-Proxy.ps1" >> "%FIXED_PATH%"
echo     # Map API response fields to script parameters (case-sensitive) >> "%FIXED_PATH%"
echo     ParameterMapping: >> "%FIXED_PATH%"
echo       ProxyAddress: "proxy_server"  # Script param : API JSON key >> "%FIXED_PATH%"
echo       BypassList: "proxy_bypass" >> "%FIXED_PATH%"
echo. >> "%FIXED_PATH%"
echo   - Name: "NotifyError" >> "%FIXED_PATH%"
echo     # This action might not need external data, just runs a script >> "%FIXED_PATH%"
echo     Script: "Send-Notification.ps1"  # This script might contain API call logic itself >> "%FIXED_PATH%"
echo     # Map event capture groups directly to script parameters >> "%FIXED_PATH%"
echo     ParameterMapping: >> "%FIXED_PATH%"
echo       ErrorCode: "error_code"  # Script param : Regex capture group name >> "%FIXED_PATH%"
echo. >> "%FIXED_PATH%"
echo   - Name: "SendLog" >> "%FIXED_PATH%"
echo     # API endpoint to call to send logs >> "%FIXED_PATH%"
echo     APIDataEndpoint: "/windows-vm-agent/logs"  # No placeholders needed >> "%FIXED_PATH%"
echo     # Script to execute with data returned from API >> "%FIXED_PATH%"
echo     Script: "Send-Log.ps1" >> "%FIXED_PATH%"
echo     # Map event capture groups directly to script parameters >> "%FIXED_PATH%"
echo     ParameterMapping: >> "%FIXED_PATH%"
echo       Message: "message"  # Script param : Log message >> "%FIXED_PATH%"

REM Replace the original config with the fixed one
echo Replacing original config with fixed version...
copy "%FIXED_PATH%" "%CONFIG_PATH%" /Y

echo Config file fixed successfully!
echo You can now run the agent using run_agent.bat

pause
