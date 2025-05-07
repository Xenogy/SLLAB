@echo off
REM Installation script for Windows VM Agent

echo Installing Windows VM Agent...

REM Install required Python packages
echo Installing required Python packages...
pip install pyyaml requests

echo Installation completed!
echo.
echo To run the agent, use run_agent.bat or python run.py
echo.
pause
