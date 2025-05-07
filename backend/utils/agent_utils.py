"""
Utility functions for Windows VM agent.

This module provides utility functions for Windows VM agent operations.
"""

import os
import logging
import base64
from typing import Dict, Any, Optional
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
    # Use the configured server URL or default to a constructed URL from API_HOST and API_PORT
    server_url = Config.get("SERVER_BASE_URL", "")

    if not server_url:
        # If no server URL is configured, construct it from API_HOST and API_PORT
        api_host = Config.get("API_HOST", "localhost")
        api_port = Config.get("API_PORT", 8080)

        # Check if API_HOST is a loopback address and try to use a more accessible address
        if api_host in ["localhost", "127.0.0.1", "0.0.0.0"]:
            # Try to get the server's public/external IP
            try:
                import socket
                # First try to get the hostname
                hostname = socket.gethostname()
                # Then try to get the IP address
                api_host = socket.gethostbyname(hostname)

                # If we still have a loopback address, try a different approach
                if api_host in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    # Try to get the IP by connecting to a public DNS server
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    api_host = s.getsockname()[0]
                    s.close()
            except Exception as e:
                logger.warning(f"Failed to get server's IP address: {e}")
                # Fall back to a hardcoded value that's likely to work in most environments
                api_host = "cs2.drandex.org"
                logger.info(f"Using hardcoded server address: {api_host}")

        # Construct the server URL
        server_url = f"http://{api_host}:{api_port}"

    # Remove trailing slashes
    server_url = server_url.rstrip("/")

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

    # Read the PowerShell script template
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "windows_vm_agent_install.ps1")

    try:
        with open(template_path, "r") as f:
            template = f.read()
    except Exception as e:
        logger.error(f"Error reading PowerShell script template: {e}")
        # Return a simple command if the template can't be read
        return f'powershell -Command "Invoke-WebRequest -Uri {download_url} -OutFile windows_vm_agent.zip; Expand-Archive -Path windows_vm_agent.zip -DestinationPath C:\\CsBotAgent; Set-Content -Path C:\\CsBotAgent\\config.yaml -Value \\"General:\\n  VMIdentifier: \\"{vm_id}\\"\\n  APIKey: \\"{api_key}\\"\\n  ManagerBaseURL: \\"{server_url}\\"\\n\\""'

    # Replace placeholders in the template
    script = template.replace("{{vm_id}}", vm_id)
    script = script.replace("{{vm_name}}", vm_name)
    script = script.replace("{{api_key}}", api_key)
    script = script.replace("{{server_url}}", server_url)
    script = script.replace("{{download_url}}", download_url)

    # Encode the script as base64 for the PowerShell command
    script_bytes = script.encode("utf-16le")
    script_base64 = base64.b64encode(script_bytes).decode("ascii")

    # Generate the PowerShell command
    command = f'powershell -ExecutionPolicy Bypass -EncodedCommand {script_base64}'

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
