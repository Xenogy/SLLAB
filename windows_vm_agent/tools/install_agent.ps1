#Requires -Version 5.0

<#
.SYNOPSIS
    Install the Windows VM Agent.
    
.DESCRIPTION
    This script downloads and installs the Windows VM Agent using the optimal download method.
    
.PARAMETER DownloadUrl
    The URL to download the Windows VM Agent from.
    
.PARAMETER VMId
    The VM identifier.
    
.PARAMETER APIKey
    The API key for authentication.
    
.PARAMETER ServerURL
    The server URL.
    
.PARAMETER InstallDir
    The installation directory. Default is "C:\CsBotAgent".
    
.EXAMPLE
    .\install_agent.ps1 -DownloadUrl "http://localhost:8000/downloads/windows_vm_agent.zip" -VMId "vm123" -APIKey "api-key" -ServerURL "http://localhost:8000"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$DownloadUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$VMId,
    
    [Parameter(Mandatory=$true)]
    [string]$APIKey,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerURL,
    
    [Parameter(Mandatory=$false)]
    [string]$InstallDir = "C:\CsBotAgent"
)

# Create a function to write colored output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Show banner
Write-ColorOutput Green "
=============================================
Windows VM Agent Installation Script
=============================================
"

# Create installation directory
Write-Output "Creating installation directory: $InstallDir"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Create subdirectories
$ScriptsDir = Join-Path $InstallDir "ActionScripts"
$LogsDir = Join-Path $InstallDir "Logs"

if (-not (Test-Path $ScriptsDir)) {
    New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null
}
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

# Download the Windows VM Agent files
Write-Output "Downloading Windows VM Agent files..."
$agentZip = Join-Path $env:TEMP "windows_vm_agent.zip"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    
    # Check if BITS module is available
    $useBITS = $false
    try {
        # Check if BITS module is available
        if (Get-Module -ListAvailable -Name BitsTransfer) {
            $useBITS = $true
            Write-Output "Using BITS for optimal download performance..."
            Import-Module BitsTransfer
        } else {
            Write-Output "BITS module not available, falling back to WebClient..."
        }
    } catch {
        Write-Output "Error checking for BITS module, falling back to WebClient: $_"
    }
    
    if ($useBITS) {
        # Use BITS for fastest download with resume capability
        try {
            # Remove any existing BITS transfer with the same name
            Get-BitsTransfer -Name "WindowsVMAgentDownload" -ErrorAction SilentlyContinue | Remove-BitsTransfer
            
            # Start the BITS transfer
            Start-BitsTransfer -Source $DownloadUrl -Destination $agentZip -DisplayName "Windows VM Agent Download" -Description "Downloading Windows VM Agent"
            
            Write-Output "Download completed successfully using BITS."
        } catch {
            Write-Output "Error using BITS, falling back to WebClient: $_"
            $useBITS = $false
        }
    }
    
    if (-not $useBITS) {
        # Use System.Net.WebClient as fallback
        Write-Output "Using WebClient for download..."
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($DownloadUrl, $agentZip)
        Write-Output "Download completed."
    }
    
    Write-Output "Extracting Windows VM Agent files..."
    
    # Create a temporary directory for extraction
    $tempExtractDir = Join-Path $env:TEMP "windows_vm_agent_extract"
    if (Test-Path $tempExtractDir) {
        Remove-Item -Path $tempExtractDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempExtractDir -Force | Out-Null
    
    # Extract the ZIP file
    Expand-Archive -Path $agentZip -DestinationPath $tempExtractDir -Force
    
    # Check if this is a GitHub repository ZIP (which has a subdirectory)
    $githubRepoDir = Get-ChildItem -Path $tempExtractDir -Directory | Select-Object -First 1
    if ($githubRepoDir) {
        Write-Output "Detected GitHub repository structure..."
        
        # Find the windows_vm_agent directory in the repository
        $agentSourceDir = Join-Path $githubRepoDir.FullName "windows_vm_agent"
        if (Test-Path $agentSourceDir) {
            Write-Output "Found windows_vm_agent directory in repository..."
            
            # Copy all files from the windows_vm_agent directory to the installation directory
            Copy-Item -Path "$agentSourceDir\*" -Destination $InstallDir -Recurse -Force
        } else {
            # If windows_vm_agent directory doesn't exist, use the repository root
            Write-Output "Using repository root as agent source..."
            Copy-Item -Path "$($githubRepoDir.FullName)\*" -Destination $InstallDir -Recurse -Force
        }
    } else {
        # If not a GitHub repository ZIP, copy all files directly
        Copy-Item -Path "$tempExtractDir\*" -Destination $InstallDir -Recurse -Force
    }
    
    # Clean up temporary directory
    Remove-Item -Path $tempExtractDir -Recurse -Force
    
    Write-ColorOutput Green "Windows VM Agent files extracted successfully."
}
catch {
    Write-ColorOutput Red "Failed to download or extract Windows VM Agent files: $_"
    exit 1
}

# Create configuration file
Write-Output "Creating configuration file..."
$configContent = @"
General:
  VMIdentifier: "$VMId"  # VM ID from Proxmox or other virtualization platform
  # API key generated during registration
  APIKey: "$APIKey"
  # Base URL for the API - should be the root URL of the server, not including /api
  # The agent will automatically try both with and without /api if needed
  ManagerBaseURL: "$ServerURL"
  ScriptsPath: "$ScriptsDir"
  LoggingEnabled: true  # Enable logging to central storage
  LogLevel: "INFO"  # Minimum level for logs sent to central storage (DEBUG, INFO, WARNING, ERROR, CRITICAL)

EventMonitors:
  - Name: "AccountLoginMonitor"
    Type: "LogFileTail"
    LogFilePath: "./test_logs/bot.log"
    CheckIntervalSeconds: 1.0
    EventTriggers:
      - EventName: "AccountLoginDetected"
        # Regex to capture the account ID from a log line
        Regex: 'User logged in:\s+(?P<account_id>\w+)'
        # Action to perform when this regex matches
        Action: "UpdateProxyForAccount"

Actions:
  - Name: "UpdateProxyForAccount"
    # API endpoint to call to get data needed for the script
    APIDataEndpoint: "/windows-vm-agent/account-config?vm_id={VMIdentifier}&account_id={account_id}"  # Placeholders filled from event
    # Script to execute with data returned from API
    Script: "Set-Proxy.ps1"
    # Map API response fields to script parameters (case-sensitive)
    ParameterMapping:
      ProxyAddress: "proxy_server"  # Script param : API JSON key
      BypassList: "proxy_bypass"
"@

Set-Content -Path (Join-Path $InstallDir "config.yaml") -Value $configContent

# Install required Python packages
Write-Output "Installing required Python packages..."
try {
    python -m pip install --upgrade pip
    python -m pip install pyyaml requests
    Write-ColorOutput Green "Required Python packages installed successfully."
}
catch {
    Write-ColorOutput Red "Failed to install required Python packages: $_"
    exit 1
}

# Create a batch file to run the agent
$batchPath = Join-Path $InstallDir "run_agent.bat"
$batchContent = @"
@echo off
REM Run the Windows VM Agent
echo Starting Windows VM Agent...
cd "$InstallDir"
python run.py
"@

Set-Content -Path $batchPath -Value $batchContent

Write-ColorOutput Green "
=============================================
Windows VM Agent Installation Complete!
=============================================

Installation Directory: $InstallDir
VM ID: $VMId
API Key: $APIKey
Server URL: $ServerURL

To run the agent manually, use the run_agent.bat file in the installation directory.
"
