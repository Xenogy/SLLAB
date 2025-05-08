# Ultra-Simple Windows VM Agent Installation Script
# This script downloads and installs the Windows VM Agent with absolute minimal complexity

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

# Create installation directory
Write-Host "Creating installation directory: $InstallDir"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Download the Windows VM Agent
Write-Host "Downloading Windows VM Agent from $DownloadUrl"
$agentZip = "$env:TEMP\windows_vm_agent.zip"

# Simple direct download using Invoke-WebRequest (more reliable than WebClient)
try {
    Write-Host "Downloading from: $DownloadUrl"
    Write-Host "Saving to: $agentZip"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $agentZip -UseBasicParsing
    Write-Host "Download completed successfully."
}
catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error downloading file: $errorMessage"
    exit 1
}

# Extract the ZIP file
Write-Host "Extracting files..."
$extractDir = "$env:TEMP\vm_agent_extract"
if (Test-Path $extractDir) {
    Remove-Item -Path $extractDir -Recurse -Force
}
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

try {
    Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force
    Write-Host "Extraction completed successfully."
}
catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error extracting files: $errorMessage"
    exit 1
}

# Find and copy the agent files
try {
    $dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if ($dirInfo) {
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
    Write-Host "Files copied successfully."
}
catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error copying files: $errorMessage"
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

    Set-Content -Path "$InstallDir\config.yaml" -Value $configContent
    Write-Host "Configuration file created successfully."
}
catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error creating configuration file: $errorMessage"
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
Write-Host "Installation Directory: $InstallDir"
Write-Host "VM ID: $VMId"
Write-Host "Server URL: $ServerURL"
Write-Host "To run the agent manually, use the run_agent.bat file in the installation directory."
