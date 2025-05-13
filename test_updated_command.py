#!/usr/bin/env python3
"""
Test script for the updated PowerShell command generation.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

try:
    from utils.agent_utils import generate_powershell_command
    print("Successfully imported generate_powershell_command")
except ImportError as e:
    print(f"Error importing generate_powershell_command: {e}")
    sys.exit(1)

# Test the function
vm_id = "123"
vm_name = "test-vm"
api_key = "test-api-key"

try:
    command = generate_powershell_command(vm_id, vm_name, api_key)
    print("Command generated successfully")
    
    # Write the command to a file
    with open("updated_powershell_command.txt", "w") as f:
        f.write(command)
    
    print("Command written to updated_powershell_command.txt")
except Exception as e:
    print(f"Error generating command: {e}")
    sys.exit(1)

print("\nDone!")
