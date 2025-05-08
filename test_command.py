#!/usr/bin/env python3
"""
Test script for generating Windows VM Agent installation commands.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the generate_installation_command function
try:
    from backend.utils.agent_utils import generate_installation_command
    print("Successfully imported generate_installation_command")
except ImportError as e:
    print(f"Error importing generate_installation_command: {e}")
    sys.exit(1)

# Generate commands for each style
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
