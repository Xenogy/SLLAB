"""
Script executor for the Windows VM Agent.

This module handles executing PowerShell scripts with parameters.
"""
import os
import sys
import platform
import logging
import subprocess
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class ScriptExecutor:
    """Executes PowerShell scripts with parameters."""

    def __init__(self, scripts_path: str):
        """
        Initialize the script executor.

        Args:
            scripts_path: Path to the directory containing the scripts.
        """
        self.scripts_path = scripts_path

        # Ensure scripts directory exists
        if not os.path.exists(scripts_path):
            logger.warning(f"Scripts directory {scripts_path} does not exist, creating it")
            try:
                os.makedirs(scripts_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create scripts directory: {str(e)}")

    def execute_script(self, script_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Execute a PowerShell script with the given parameters.

        Args:
            script_name: Name of the script file.
            parameters: Dictionary of parameter names and values.

        Returns:
            Tuple of (success, stdout, stderr)
        """
        script_path = os.path.join(self.scripts_path, script_name)

        # Security check: Ensure the script is within the scripts directory
        if not os.path.normpath(script_path).startswith(os.path.normpath(self.scripts_path)):
            logger.error(f"Security violation: Script path {script_path} is outside scripts directory")
            return False, "", "Security violation: Script path is outside scripts directory"

        # Check if script exists
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return False, "", f"Script not found: {script_name}"

        # Build PowerShell command
        powershell_args = self._build_powershell_args(script_path, parameters)

        try:
            logger.info(f"Executing script: {script_name} with parameters: {parameters}")

            # Execute PowerShell with the script and parameters
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True
            }

            # Add Windows-specific flags if running on Windows
            if platform.system() == 'Windows':
                popen_kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

            process = subprocess.Popen(powershell_args, **popen_kwargs)

            stdout, stderr = process.communicate(timeout=300)  # 5-minute timeout
            exit_code = process.returncode

            if exit_code == 0:
                logger.info(f"Script {script_name} executed successfully")
                return True, stdout, stderr
            else:
                logger.error(f"Script {script_name} failed with exit code {exit_code}")
                logger.error(f"Script stderr: {stderr}")
                return False, stdout, stderr

        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_name} timed out after 300 seconds")
            return False, "", "Script execution timed out"
        except Exception as e:
            logger.error(f"Error executing script {script_name}: {str(e)}")
            return False, "", f"Error executing script: {str(e)}"

    def _build_powershell_args(self, script_path: str, parameters: Dict[str, Any]) -> List[str]:
        """
        Build the PowerShell command arguments.

        Args:
            script_path: Full path to the script.
            parameters: Dictionary of parameter names and values.

        Returns:
            List of command arguments.
        """
        # Base PowerShell command
        # Use different command based on platform
        if platform.system() == 'Windows':
            args = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", script_path
            ]
        else:
            # For testing on non-Windows platforms, use echo to simulate PowerShell
            logger.warning(f"Running on non-Windows platform, simulating PowerShell with echo")
            args = [
                "echo",
                f"Simulating PowerShell execution of {script_path}"
            ]

        # Add parameters
        for name, value in parameters.items():
            # Format the parameter value based on its type
            if value is None:
                # Skip None values
                continue
            elif isinstance(value, bool):
                # Convert boolean to PowerShell $true/$false
                param_value = "$true" if value else "$false"
            elif isinstance(value, (int, float)):
                # Numbers don't need quotes
                param_value = str(value)
            else:
                # Strings need to be quoted and escaped
                # Replace double quotes with escaped double quotes
                escaped_value = str(value).replace('"', '`"')
                param_value = f'"{escaped_value}"'

            args.append(f"-{name}")
            args.append(param_value)

        return args
