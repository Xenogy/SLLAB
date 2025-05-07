Windows VM Agent
================

This is a dynamic Windows VM agent that monitors for various predefined events within the VM,
pulls necessary data from a central manager API when triggered, and executes corresponding
predefined local scripts.

Installation Instructions
------------------------

1. Make sure Python 3.7 or later is installed on your Windows VM.
   You can download Python from https://www.python.org/downloads/windows/

2. Install the required Python packages:
   Open a command prompt and run:
   pip install pyyaml requests

3. Edit the config.yaml file to set your API key, manager URL, and configure monitors and actions.

Running the Agent
----------------

1. Simple Method:
   Double-click the run_agent.bat file to start the agent.

2. Command Line Method:
   Open a command prompt, navigate to the windows_vm_agent directory, and run:
   python run.py

   You can specify additional options:
   python run.py --log-level DEBUG
   python run.py --config custom_config.yaml

Installing as a Windows Service
------------------------------

To run the agent as a Windows service:

1. Install NSSM (Non-Sucking Service Manager) from https://nssm.cc/download

2. Open a command prompt as Administrator and navigate to the windows_vm_agent directory

3. Run the following commands:
   nssm install WindowsVMAgent "C:\Path\To\Python.exe" "run.py"
   nssm set WindowsVMAgent DisplayName "Windows VM Agent"
   nssm set WindowsVMAgent Description "Dynamic Windows VM Agent for monitoring and executing actions"
   nssm set WindowsVMAgent Start SERVICE_AUTO_START
   nssm start WindowsVMAgent

Configuration
------------

The agent is configured using the config.yaml file. See the file for examples and documentation.

Logs
----

Logs are stored in the 'logs' directory within the agent installation directory.

Troubleshooting
--------------

1. Check the log files in the 'logs' directory for error messages.

2. Run the agent with debug logging:
   python run.py --log-level DEBUG

3. Make sure the API key and manager URL are correctly configured in config.yaml.

4. Verify that the log files being monitored exist and are accessible.

5. Check that PowerShell scripts in the action_scripts directory have the correct permissions.

For more detailed documentation, see the README.md file.
