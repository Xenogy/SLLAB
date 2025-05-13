"""
Utility functions for Windows VM agent.

This module provides utility functions for Windows VM agent operations.
"""

import os
import logging
import base64
from typing import Dict, Any, Optional, Literal
from config import Config

logger = logging.getLogger(__name__)

def get_agent_download_url() -> str:
    """
    Get the download URL for the Windows VM agent.

    Returns:
        str: The download URL for the Windows VM agent.
    """
    # Use the configured download URL or default to a GitHub URL
    download_url = Config.get("WINDOWS_VM_AGENT_DOWNLOAD_URL", "")

    if not download_url:
        # If no download URL is configured, use a GitHub URL
        # This is a public repository that contains the Windows VM agent files
        download_url = "https://github.com/xenogy/sllab/archive/refs/heads/main.zip"

    return download_url

def get_server_base_url() -> str:
    """
    Get the base URL for the server.

    Returns:
        str: The base URL for the server.
    """
    # Always use the hardcoded public URL for reliability
    server_url = "https://cs2.drandex.org"

    # Log the server URL
    logger.info(f"Using server URL: {server_url}")

    return server_url

def generate_powershell_command(vm_id: str, vm_name: str, api_key: str) -> str:
    """
    Generate a PowerShell command to install the Windows VM agent.

    Args:
        vm_id (str): The VM ID.
        vm_name (str): The VM name.
        api_key (str): The API key.

    Returns:
        str: The PowerShell command.
    """
    # Get the server base URL
    server_url = get_server_base_url()

    # Get the agent download URL
    download_url = get_agent_download_url()

    # If the download URL is relative, make it absolute
    if download_url.startswith("/"):
        download_url = f"{server_url}{download_url}"

    # Log the URLs for debugging
    logger.info(f"Server URL: {server_url}")
    logger.info(f"Download URL: {download_url}")

    # Ensure we have default values for all parameters
    vm_id = vm_id or "default-vm-id"
    api_key = api_key or "default-api-key"
    server_url = server_url or "https://cs2.drandex.org"
    download_url = download_url or "https://github.com/xenogy/sllab/archive/refs/heads/main.zip"

    # Create a simpler, more robust command
    command = (
        f'powershell -ExecutionPolicy Bypass -Command "'
        f'$ErrorActionPreference = \'Stop\'; '
        f'[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; '
        f'$downloadUrl = \'{download_url}\'; '
        f'$vmId = \'{vm_id}\'; '
        f'$apiKey = \'{api_key}\'; '
        f'$serverUrl = \'{server_url}\'; '
        f'$installDir = \'C:\\CsBotAgent\'; '

        # Create installation directory
        f'if (-not (Test-Path $installDir)) {{ New-Item -ItemType Directory -Path $installDir -Force | Out-Null }}; '

        # Download agent
        f'Write-Host \'Downloading Windows VM Agent...\'; '
        f'try {{ '
        f'$webClient = New-Object System.Net.WebClient; '
        f'$agentZip = Join-Path $env:TEMP \'windows_vm_agent.zip\'; '
        f'$webClient.DownloadFile($downloadUrl, $agentZip); '
        f'Write-Host (\"Downloaded agent to \" + $agentZip); '
        f'}} catch {{ '
        f'Write-Host (\"Error downloading agent: \" + $_) -ForegroundColor Red; '
        f'exit 1; '
        f'}}; '

        # Extract files
        f'Write-Host \'Extracting...\'; '
        f'try {{ '
        f'$extractDir = Join-Path $env:TEMP \'vm_agent_extract\'; '
        f'if (Test-Path $extractDir) {{ Remove-Item -Path $extractDir -Recurse -Force }}; '
        f'New-Item -ItemType Directory -Path $extractDir -Force | Out-Null; '
        f'Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force; '
        f'Write-Host (\"Extracted to \" + $extractDir); '
        f'}} catch {{ '
        f'Write-Host (\"Error extracting archive: \" + $_) -ForegroundColor Red; '
        f'exit 1; '
        f'}}; '

        # Copy files
        f'Write-Host \'Copying files to installation directory...\'; '
        f'try {{ '
        f'$dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1; '
        f'if ($dirInfo) {{ '
        f'$agentDir = Join-Path $dirInfo.FullName \'windows_vm_agent\'; '
        f'if (Test-Path $agentDir) {{ '
        f'Write-Host \"Found windows_vm_agent directory, copying files...\"; '
        f'Copy-Item -Path (Join-Path $agentDir \'*\') -Destination $installDir -Recurse -Force; '
        f'}} else {{ '
        f'Write-Host \"No windows_vm_agent directory found, copying from repository root...\"; '
        f'Copy-Item -Path (Join-Path $dirInfo.FullName \'*\') -Destination $installDir -Recurse -Force; '
        f'}} '
        f'}} else {{ '
        f'Write-Host \"No directories found in extract location, copying all files...\"; '
        f'Copy-Item -Path (Join-Path $extractDir \'*\') -Destination $installDir -Recurse -Force; '
        f'}}; '
        f'Write-Host (\"Files copied to \" + $installDir); '
        f'}} catch {{ '
        f'Write-Host (\"Error copying files: \" + $_) -ForegroundColor Red; '
        f'exit 1; '
        f'}}; '

        # Create configuration
        f'Write-Host \'Creating config...\'; '
        f'try {{ '
        f'$configPath = Join-Path $installDir \'config.yaml\'; '
        f'$configContent = "General:`n"; '
        f'$configContent += "  VMIdentifier: `"$vmId`"`n"; '
        f'$configContent += "  APIKey: `"$apiKey`"`n"; '
        f'$configContent += "  ManagerBaseURL: `"$serverUrl`"`n"; '
        f'$configContent += "  ScriptsPath: `"$installDir\\\\ActionScripts`"`n"; '
        f'$configContent += "  LoggingEnabled: true`n"; '
        f'$configContent += "  LogLevel: `"INFO`"`n"; '
        f'Set-Content -Path $configPath -Value $configContent; '
        f'Write-Host (\'Configuration saved to \' + $configPath); '
        f'}} catch {{ '
        f'Write-Host (\'Error creating configuration: \' + $_) -ForegroundColor Red; '
        f'exit 1; '
        f'}}; '

        # Done
        f'Write-Host \'Windows VM Agent installed successfully!\' -ForegroundColor Green"'
    )

    return command

def generate_installation_command(
    vm_id: str,
    api_key: str,
    style: Literal["direct", "simple", "oneliner", "simplest", "super_simple"] = "direct",
    install_dir: str = "C:\\CsBotAgent",
    vm_name: str = ""
) -> str:
    """
    Generate a PowerShell command to install the Windows VM Agent.

    This function consolidates all the different installation command styles into a single function.

    Args:
        vm_id (str): The VM ID.
        api_key (str): The API key.
        style (str): The installation style ("direct", "simple", "oneliner", "simplest", "super_simple").
        install_dir (str): The installation directory.
        vm_name (str): The VM name (optional, used only in some templates).

    Returns:
        str: The PowerShell command to install the agent.
    """
    # Get the server base URL
    server_url = get_server_base_url()

    # Get the agent download URL
    download_url = get_agent_download_url()

    # If the download URL is relative, make it absolute
    if download_url.startswith("/"):
        download_url = f"{server_url}{download_url}"

    # Log the URLs for debugging
    logger.info(f"Server URL: {server_url}")
    logger.info(f"Download URL: {download_url}")

    # Base command that sets up variables and TLS
    base_vars = f"$downloadUrl = '{download_url}'; $vmId = '{vm_id}'; $apiKey = '{api_key}'; $serverUrl = '{server_url}'; $installDir = '{install_dir}';"
    base_setup = "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;"

    if style == "direct":
        # Direct installation by downloading and running the direct_installer.ps1 script
        # This is much more reliable than trying to create a complex one-liner
        installer_url = f"{server_url}/downloads/direct_installer.ps1"
        command = f'''powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '{installer_url}' -OutFile '$env:TEMP\\direct_installer.ps1'; & '$env:TEMP\\direct_installer.ps1' -DownloadUrl '{download_url}' -VMId '{vm_id}' -APIKey '{api_key}' -ServerURL '{server_url}' -InstallDir '{install_dir}'"'''

    elif style == "simple" or style == "oneliner":
        # Download and run the simple_install.ps1 script
        script_url = f"{server_url}/downloads/simple_install.ps1"
        command = f'''powershell -ExecutionPolicy Bypass -Command "{base_setup} {base_vars} $scriptUrl = '{script_url}'; Write-Host \\"Downloading installation script from $scriptUrl\\"; Invoke-WebRequest -Uri $scriptUrl -OutFile \\"$env:TEMP\\\\simple_install.ps1\\"; Write-Host \\"Running installation script\\"; & \\"$env:TEMP\\\\simple_install.ps1\\" -DownloadUrl $downloadUrl -VMId $vmId -APIKey $apiKey -ServerURL $serverUrl -InstallDir $installDir"'''

    elif style == "simplest":
        # Simplest possible command that downloads and runs the direct_installer.ps1 script
        # This is much more reliable than trying to create a complex one-liner
        installer_url = f"{server_url}/downloads/direct_installer.ps1"
        command = f'''powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '{installer_url}' -OutFile '$env:TEMP\\direct_installer.ps1'; & '$env:TEMP\\direct_installer.ps1' -DownloadUrl '{download_url}' -VMId '{vm_id}' -APIKey '{api_key}' -ServerURL '{server_url}' -InstallDir '{install_dir}'"'''

    elif style == "super_simple":
        # Download and run the super_simple.ps1 script
        super_simple_url = f"{server_url}/downloads/super_simple.ps1"
        command = f'''powershell -ExecutionPolicy Bypass -Command "{base_setup} {base_vars} $scriptUrl = '{super_simple_url}'; Invoke-WebRequest -Uri $scriptUrl -OutFile \\"$env:TEMP\\\\super_simple.ps1\\"; & \\"$env:TEMP\\\\super_simple.ps1\\" -DownloadUrl $downloadUrl -VMId $vmId -APIKey $apiKey -ServerURL $serverUrl -InstallDir $installDir"'''

    else:
        # Default to direct installation
        return generate_installation_command(vm_id, api_key, "direct", install_dir, vm_name)

    return command


def generate_powershell_script(vm_id: str, vm_name: str, api_key: str) -> str:
    """
    Generate a PowerShell script to install the Windows VM agent.

    Args:
        vm_id (str): The VM ID.
        vm_name (str): The VM name.
        api_key (str): The API key.

    Returns:
        str: The PowerShell script.
    """
    # Get the server base URL
    server_url = get_server_base_url()

    # Get the agent download URL
    download_url = get_agent_download_url()

    # If the download URL is relative, make it absolute
    if download_url.startswith("/"):
        download_url = f"{server_url}{download_url}"

    # Log the URLs for debugging
    logger.info(f"Server URL (script): {server_url}")
    logger.info(f"Download URL (script): {download_url}")

    # Read the PowerShell script template
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "windows_vm_agent_install.ps1")

    try:
        with open(template_path, "r") as f:
            template = f.read()
    except Exception as e:
        logger.error(f"Error reading PowerShell script template: {e}")
        # Return a simple script if the template can't be read
        return f'''
# Windows VM Agent Installation Script
# Generated by AccountDB

# Create installation directory
$InstallDir = "C:\\CsBotAgent"
New-Item -ItemType Directory -Path $InstallDir -Force

# Download and extract the agent
Invoke-WebRequest -Uri "{download_url}" -OutFile "$env:TEMP\\windows_vm_agent.zip"
Expand-Archive -Path "$env:TEMP\\windows_vm_agent.zip" -DestinationPath $InstallDir -Force

# Create configuration file
$ConfigContent = @"
General:
  VMIdentifier: "{vm_id}"
  APIKey: "{api_key}"
  ManagerBaseURL: "{server_url}"
  ScriptsPath: "$InstallDir\\ActionScripts"
  LoggingEnabled: true
  LogLevel: "INFO"
"@

Set-Content -Path "$InstallDir\\config.yaml" -Value $ConfigContent

# Install required packages
pip install pyyaml requests

Write-Host "Windows VM Agent installed successfully!"
'''

    # Replace placeholders in the template
    script = template.replace("{{vm_id}}", vm_id)
    script = script.replace("{{vm_name}}", vm_name)
    script = script.replace("{{api_key}}", api_key)
    script = script.replace("{{server_url}}", server_url)
    script = script.replace("{{download_url}}", download_url)

    return script


# Test function for debugging
if __name__ == "__main__":
    # Test the generate_powershell_command function
    vm_id = "123"
    vm_name = "test-vm"
    api_key = "test-api-key"

    print("\nTesting generate_powershell_command:")
    command = generate_powershell_command(vm_id, vm_name, api_key)
    print(command)

    print("\nDone!")
