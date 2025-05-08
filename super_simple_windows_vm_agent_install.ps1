# Super-Simple Windows VM Agent Installation Script
# This script is designed to be as simple as possible to avoid PowerShell parsing errors

param(
    [string]$DownloadUrl = "https://github.com/xenogy/sllab/archive/refs/heads/main.zip",
    [string]$VMId = "2",
    [string]$APIKey = "PQaZWQD1ZBLRtyMr2bBx4OpXNMq69OXGEhrpkwFjciM",
    [string]$ServerURL = "https://cs2.drandex.org"
)

# Set TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Create installation directory
$InstallDir = "C:\CsBotAgent"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Download and extract in one step
try {
    # Download
    Write-Host "Downloading from $DownloadUrl"
    $tempFile = "$env:TEMP\windows_vm_agent.zip"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $tempFile -UseBasicParsing
    
    # Extract
    Write-Host "Extracting to temporary location"
    $extractDir = "$env:TEMP\vm_agent_extract"
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
    Expand-Archive -Path $tempFile -DestinationPath $extractDir -Force
    
    # Find and copy files
    $dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if ($dirInfo) {
        $agentDir = Join-Path $dirInfo.FullName "windows_vm_agent"
        if (Test-Path $agentDir) {
            Write-Host "Found windows_vm_agent directory in ZIP"
            Copy-Item -Path "$agentDir\*" -Destination $InstallDir -Recurse -Force
        } else {
            Write-Host "Using repository root directory"
            Copy-Item -Path "$($dirInfo.FullName)\*" -Destination $InstallDir -Recurse -Force
        }
    } else {
        Write-Host "Using extract directory root"
        Copy-Item -Path "$extractDir\*" -Destination $InstallDir -Recurse -Force
    }
    
    # Create config
    Write-Host "Creating configuration file"
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
    
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    Write-Host "Installation Directory: $InstallDir"
    Write-Host "VM ID: $VMId"
    Write-Host "Server URL: $ServerURL"
}
catch {
    Write-Host "Error during installation: $($_.Exception.Message)" -ForegroundColor Red
}
