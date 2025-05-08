# Windows VM Agent Direct Installer
# This script downloads and installs the Windows VM Agent

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

# Set error action preference to stop on any error
$ErrorActionPreference = 'Stop'

# Set security protocol to TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "Starting Windows VM Agent installation..." -ForegroundColor Cyan
Write-Host "  VM ID: $VMId"
Write-Host "  Server URL: $ServerURL"
Write-Host "  Installation Directory: $InstallDir"

# Create installation directory
if (-not (Test-Path $InstallDir)) {
    Write-Host "Creating installation directory: $InstallDir"
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Download the Windows VM Agent
Write-Host "Downloading Windows VM Agent from $DownloadUrl"
$agentZip = Join-Path $env:TEMP "windows_vm_agent.zip"
try {
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($DownloadUrl, $agentZip)
    Write-Host "Download completed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error downloading file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Extract the ZIP file
Write-Host "Extracting files..."
$extractDir = Join-Path $env:TEMP "vm_agent_extract"
try {
    # Clean up extract directory if it exists
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    # Extract the ZIP file
    Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force
    Write-Host "Extraction completed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error extracting files: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Find and copy the agent files
try {
    $dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if ($null -ne $dirInfo) {
        $agentDir = Join-Path $dirInfo.FullName "windows_vm_agent"
        if (Test-Path $agentDir) {
            Write-Host "Found windows_vm_agent directory in ZIP."
            Copy-Item -Path (Join-Path $agentDir "*") -Destination $InstallDir -Recurse -Force
        } else {
            Write-Host "Using repository root directory."
            Copy-Item -Path (Join-Path $dirInfo.FullName "*") -Destination $InstallDir -Recurse -Force
        }
    } else {
        Write-Host "Using extract directory root."
        Copy-Item -Path (Join-Path $extractDir "*") -Destination $InstallDir -Recurse -Force
    }
    Write-Host "Files copied successfully." -ForegroundColor Green
} catch {
    Write-Host "Error copying files: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create configuration file
Write-Host "Creating configuration file..."
try {
    $configContent = @"
General:
  VMIdentifier: "$VMId"
  APIKey: "$APIKey"
  ManagerBaseURL: "$ServerURL"
  ScriptsPath: "$InstallDir\ActionScripts"
  LoggingEnabled: true
  LogLevel: "INFO"
"@

    Set-Content -Path (Join-Path $InstallDir "config.yaml") -Value $configContent
    Write-Host "Configuration file created successfully." -ForegroundColor Green
} catch {
    Write-Host "Error creating configuration file: $($_.Exception.Message)" -ForegroundColor Red
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

Write-Host "Windows VM Agent installed successfully!" -ForegroundColor Green
Write-Host "Installation Directory: $InstallDir" -ForegroundColor Green
Write-Host "VM ID: $VMId" -ForegroundColor Green
Write-Host "Server URL: $ServerURL" -ForegroundColor Green
Write-Host "To run the agent manually, use the run_agent.bat file in the installation directory." -ForegroundColor Cyan
