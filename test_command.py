#!/usr/bin/env python3
"""
Test script for generating Windows VM Agent installation commands.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the functions
try:
    from backend.utils.agent_utils import generate_installation_command, generate_powershell_command
    print("Successfully imported agent utility functions")
except ImportError as e:
    print(f"Error importing agent utility functions: {e}")
    sys.exit(1)

# Test the fixed generate_powershell_command function
print("\n\n" + "=" * 80)
print("Testing generate_powershell_command")
print("=" * 80)
try:
    vm_id = "123"
    vm_name = "test-vm"
    api_key = "test-api-key"
    command = generate_powershell_command(vm_id, vm_name, api_key)
    print(command)
except Exception as e:
    print(f"Error generating PowerShell command: {e}")

# Generate commands for each style
print("\n\n" + "=" * 80)
print("Testing generate_installation_command with different styles")
print("=" * 80)
styles = ["direct", "simple", "oneliner", "simplest", "super_simple"]
vm_id = "test-vm"
api_key = "test-api-key"

for style in styles:
    print(f"\n\n{'=' * 80}")
    print(f"Style: {style}")
    print(f"{'=' * 80}")
    try:
        command = generate_installation_command(vm_id, api_key, style=style)
        print(command)
    except Exception as e:
        print(f"Error generating command for style '{style}': {e}")

print("\nDone!")
