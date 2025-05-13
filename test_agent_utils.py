#!/usr/bin/env python3
"""
Test script for the agent_utils module.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Test the function directly
vm_id = "123"
vm_name = "test-vm"
api_key = "test-api-key"

# Create a simpler, more robust command
command = (
    f'powershell -ExecutionPolicy Bypass -Command "'
    f'$ErrorActionPreference = \'Stop\'; '
    f'[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; '
    f'$downloadUrl = \'https://github.com/xenogy/sllab/archive/refs/heads/main.zip\'; '
    f'$vmId = \'{vm_id}\'; '
    f'$apiKey = \'{api_key}\'; '
    f'$serverUrl = \'https://cs2.drandex.org\'; '
    f'$installDir = \'C:\\CsBotAgent\'; '
    f'if (-not (Test-Path $installDir)) {{ New-Item -ItemType Directory -Path $installDir -Force | Out-Null }}; '
    f'Write-Host \'Downloading Windows VM Agent...\'; '
    f'$webClient = New-Object System.Net.WebClient; '
    f'$agentZip = Join-Path $env:TEMP \'windows_vm_agent.zip\'; '
    f'$webClient.DownloadFile($downloadUrl, $agentZip); '
    f'Write-Host \'Extracting...\'; '
    f'$extractDir = Join-Path $env:TEMP \'vm_agent_extract\'; '
    f'if (Test-Path $extractDir) {{ Remove-Item -Path $extractDir -Recurse -Force }}; '
    f'New-Item -ItemType Directory -Path $extractDir -Force | Out-Null; '
    f'Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force; '
    f'$dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1; '
    f'if ($dirInfo) {{ '
    f'$agentDir = Join-Path $dirInfo.FullName \'windows_vm_agent\'; '
    f'if (Test-Path $agentDir) {{ '
    f'Copy-Item -Path (Join-Path $agentDir \'*\') -Destination $installDir -Recurse -Force '
    f'}} else {{ '
    f'Copy-Item -Path (Join-Path $dirInfo.FullName \'*\') -Destination $installDir -Recurse -Force '
    f'}} '
    f'}} else {{ '
    f'Copy-Item -Path (Join-Path $extractDir \'*\') -Destination $installDir -Recurse -Force '
    f'}}; '
    f'Write-Host \'Creating config...\'; '
    f'$configContent = \'General:\\n  VMIdentifier: \"{0}\"\\n  APIKey: \"{1}\"\\n  ManagerBaseURL: \"{2}\"\\n  ScriptsPath: \"{3}\\\\ActionScripts\"\\n  LoggingEnabled: true\\n  LogLevel: \"INFO\"\'; '
    f'$formattedConfig = $configContent -f $vmId, $apiKey, $serverUrl, $installDir; '
    f'Set-Content -Path (Join-Path $installDir \'config.yaml\') -Value $formattedConfig; '
    f'Write-Host \'Windows VM Agent installed successfully!\' -ForegroundColor Green"'
)

print("Command generated successfully")
print("\nCommand preview (first 100 characters):")
print(command[:100] + "...")

print("\nDone!")
