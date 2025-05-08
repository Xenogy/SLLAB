# Windows VM Agent Direct Installation Script
# This script downloads and installs the Windows VM Agent directly

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

# Set security protocol to TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "Starting Windows VM Agent installation..." -ForegroundColor Cyan

# Define variables
$tempDir = $env:TEMP
$agentZip = Join-Path $tempDir "windows_vm_agent.zip"
$extractDir = Join-Path $tempDir "vm_agent_extract"

Write-Host "Installation parameters:" -ForegroundColor Cyan
Write-Host "  Download URL: $DownloadUrl"
Write-Host "  VM ID: $VMId"
Write-Host "  Server URL: $ServerURL"
Write-Host "  Installation Directory: $InstallDir"

Write-Host "Downloading Windows VM Agent..." -ForegroundColor Cyan
try {
    # Direct download using WebClient
    $webClient = New-Object System.Net.WebClient
    Write-Host "Downloading from $DownloadUrl to $agentZip"
    $webClient.DownloadFile($DownloadUrl, $agentZip)
    Write-Host "Download completed successfully." -ForegroundColor Green
} catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error downloading file: $errorMessage" -ForegroundColor Red
    exit 1
}

Write-Host "Extracting files..." -ForegroundColor Cyan
try {
    # Create installation directory
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        Write-Host "Created installation directory: $InstallDir"
    }

    # Clean up extract directory if it exists
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
        Write-Host "Removed existing extract directory: $extractDir"
    }
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    # Extract the ZIP file
    Write-Host "Extracting ZIP file to $extractDir"
    Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force

    # Find the agent directory
    $dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if ($null -ne $dirInfo) {
        $agentDir = Join-Path $dirInfo.FullName "windows_vm_agent"
        if (Test-Path $agentDir) {
            Write-Host "Found windows_vm_agent directory in ZIP."
            Copy-Item -Path "$agentDir\*" -Destination $InstallDir -Recurse -Force
        } else {
            Write-Host "Using repository root directory."
            Copy-Item -Path "$($dirInfo.FullName)\*" -Destination $InstallDir -Recurse -Force
        }
    } else {
        Write-Host "Using extract directory root."
        Copy-Item -Path "$extractDir\*" -Destination $InstallDir -Recurse -Force
    }

    Write-Host "Files extracted successfully." -ForegroundColor Green
} catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error extracting files: $errorMessage" -ForegroundColor Red
    exit 1
}

Write-Host "Creating configuration file..." -ForegroundColor Cyan
try {
    # Create config content using here-string for better reliability
    $configContent = @"
General:
  VMIdentifier: "$VMId"
  APIKey: "$APIKey"
  ManagerBaseURL: "$ServerURL"
  ScriptsPath: "$InstallDir\ActionScripts"
  LoggingEnabled: true
  LogLevel: "INFO"
"@

    $configPath = Join-Path $InstallDir "config.yaml"
    Set-Content -Path $configPath -Value $configContent
    Write-Host "Configuration file created successfully at $configPath" -ForegroundColor Green
} catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error creating configuration file: $errorMessage" -ForegroundColor Red
    exit 1
}

# Create a batch file to run the agent
try {
    $batchPath = Join-Path $InstallDir "run_agent.bat"
    $batchContent = @"
@echo off
REM Run the Windows VM Agent
echo Starting Windows VM Agent...
cd "$InstallDir"
python run.py
"@

    Set-Content -Path $batchPath -Value $batchContent
    Write-Host "Created batch file for running the agent: $batchPath" -ForegroundColor Green
} catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error creating batch file: $errorMessage" -ForegroundColor Red
    # Not exiting here as this is not critical
}

Write-Host "Windows VM Agent installed successfully!" -ForegroundColor Green
Write-Host "Installation Directory: $InstallDir" -ForegroundColor Green
Write-Host "VM ID: $VMId" -ForegroundColor Green
Write-Host "Server URL: $ServerURL" -ForegroundColor Green
Write-Host "To run the agent manually, use the run_agent.bat file in the installation directory." -ForegroundColor Cyan
