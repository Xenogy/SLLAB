# Fix Windows VM Agent Config Script
# This script fixes the YAML escape character issue in the config.yaml file

# Define paths
$configPath = "C:\CsBotAgent\config.yaml"
$backupPath = "C:\CsBotAgent\config.yaml.bak"

# Check if config file exists
if (-not (Test-Path $configPath)) {
    Write-Host "Error: Config file not found at $configPath" -ForegroundColor Red
    exit 1
}

# Create a backup of the original config
Write-Host "Creating backup of original config file..." -ForegroundColor Yellow
Copy-Item -Path $configPath -Destination $backupPath -Force
Write-Host "Backup created at $backupPath" -ForegroundColor Green

# Read the config file
$content = Get-Content -Path $configPath -Raw

# Replace backslashes with forward slashes in paths
$fixedContent = $content -replace '(?<=["]:?\s+")([A-Z]:\\[^"]+)(?=")', { $args[0].Groups[1].Value -replace '\\', '/' }

# Write the fixed content back to the file
Set-Content -Path $configPath -Value $fixedContent

# Verify the fix
try {
    # Try to parse the YAML
    $yaml = ConvertFrom-Yaml -Path $configPath
    Write-Host "Config file fixed successfully!" -ForegroundColor Green
    Write-Host "You can now run the agent using run_agent.bat" -ForegroundColor Green
}
catch {
    Write-Host "Error: The config file may still have issues." -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "You can restore the backup using: Copy-Item -Path $backupPath -Destination $configPath -Force" -ForegroundColor Yellow
}

# Note: If the ConvertFrom-Yaml command is not available, you may need to install the PowerShell-Yaml module:
# Install-Module -Name PowerShell-Yaml -Scope CurrentUser -Force
