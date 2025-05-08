# Simple Windows VM Agent Installation Script
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

# Set security protocol to TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Create installation directory
Write-Host "Creating installation directory: $InstallDir"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Download the Windows VM Agent
Write-Host "Downloading Windows VM Agent from $DownloadUrl"
$agentZip = "$env:TEMP\windows_vm_agent.zip"

# Check if BITS is available
if (Get-Module -ListAvailable -Name BitsTransfer) {
    Write-Host "Using BITS for download..."
    Import-Module BitsTransfer
    Start-BitsTransfer -Source $DownloadUrl -Destination $agentZip
} else {
    Write-Host "Using WebClient for download..."
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($DownloadUrl, $agentZip)
}

# Extract the ZIP file
Write-Host "Extracting files..."
$extractDir = "$env:TEMP\vm_agent_extract"
if (Test-Path $extractDir) {
    Remove-Item -Path $extractDir -Recurse -Force
}
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force

# Find and copy the agent files
$dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
if ($dirInfo) {
    $agentDir = Join-Path $dirInfo.FullName "windows_vm_agent"
    if (Test-Path $agentDir) {
        Copy-Item -Path "$agentDir\*" -Destination $InstallDir -Recurse -Force
    } else {
        Copy-Item -Path "$($dirInfo.FullName)\*" -Destination $InstallDir -Recurse -Force
    }
} else {
    Copy-Item -Path "$extractDir\*" -Destination $InstallDir -Recurse -Force
}

# Create configuration file
Write-Host "Creating configuration file..."
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

Write-Host "Windows VM Agent installed successfully!"
Write-Host "Installation Directory: $InstallDir"
Write-Host "VM ID: $VMId"
Write-Host "Server URL: $ServerURL"
Write-Host "To run the agent manually, use the run_agent.bat file in the installation directory."
