# Super-Simple One-Line Windows VM Agent Installation Script
# This script is designed to be as simple as possible to avoid PowerShell parsing errors

param(
    [Parameter(Mandatory=$true)]
    [string]$DownloadUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$VMId,
    
    [Parameter(Mandatory=$true)]
    [string]$APIKey,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerURL
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
    Write-Host "Extracting to $InstallDir"
    Expand-Archive -Path $tempFile -DestinationPath $InstallDir -Force
    
    # Create config
    Write-Host "Creating configuration file"
    $configContent = "General:`n  VMIdentifier: `"$VMId`"`n  APIKey: `"$APIKey`"`n  ManagerBaseURL: `"$ServerURL`"`n  LoggingEnabled: true`n  LogLevel: `"INFO`""
    Set-Content -Path "$InstallDir\config.yaml" -Value $configContent
    
    Write-Host "Installation completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "Error during installation: $($_.Exception.Message)" -ForegroundColor Red
}
