# Test PowerShell command for Windows VM Agent installation

# Set security protocol to TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Define variables
$downloadUrl = 'https://github.com/xenogy/sllab/archive/refs/heads/main.zip'
$vmId = 'test-vm'
$apiKey = 'test-api-key'
$serverUrl = 'https://cs2.drandex.org'
$installDir = 'C:\CsBotAgent'

# Create installation directory
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# Download the Windows VM Agent
Write-Host 'Downloading Windows VM Agent...'
$webClient = New-Object System.Net.WebClient
$agentZip = Join-Path $env:TEMP 'windows_vm_agent.zip'
$webClient.DownloadFile($downloadUrl, $agentZip)

# Extract the ZIP file
Write-Host 'Extracting...'
$extractDir = Join-Path $env:TEMP 'vm_agent_extract'
if (Test-Path $extractDir) {
    Remove-Item -Path $extractDir -Recurse -Force
}
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force

# Find and copy the agent files
$dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
if ($null -ne $dirInfo) {
    $agentDir = Join-Path $dirInfo.FullName 'windows_vm_agent'
    if (Test-Path $agentDir) {
        Write-Host 'Found windows_vm_agent directory in ZIP.'
        Copy-Item -Path (Join-Path $agentDir '*') -Destination $installDir -Recurse -Force
    } else {
        Write-Host 'Using repository root directory.'
        Copy-Item -Path (Join-Path $dirInfo.FullName '*') -Destination $installDir -Recurse -Force
    }
} else {
    Write-Host 'Using extract directory root.'
    Copy-Item -Path (Join-Path $extractDir '*') -Destination $installDir -Recurse -Force
}

# Create configuration file
Write-Host 'Creating config...'
$configContent = @"
General:
  VMIdentifier: "$vmId"
  APIKey: "$apiKey"
  ManagerBaseURL: "$serverUrl"
  ScriptsPath: "$installDir\ActionScripts"
  LoggingEnabled: true
  LogLevel: "INFO"
"@
Set-Content -Path (Join-Path $installDir 'config.yaml') -Value $configContent

Write-Host 'Windows VM Agent installed successfully!' -ForegroundColor Green
