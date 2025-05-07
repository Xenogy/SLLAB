#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Installs the Windows VM Agent as a Windows service.
    
.DESCRIPTION
    This script installs the Windows VM Agent as a Windows service using NSSM.
    It downloads NSSM if it's not already installed, creates necessary directories,
    and configures the service to start automatically.
    
.PARAMETER ConfigPath
    Path to the configuration file. Default is "C:\CsBotAgent\config.yaml".
    
.PARAMETER ScriptsPath
    Path to the scripts directory. Default is "C:\CsBotAgent\ActionScripts".
    
.PARAMETER LogsPath
    Path to the logs directory. Default is "C:\CsBotAgent\Logs".
    
.PARAMETER ServiceName
    Name of the Windows service. Default is "WindowsVMAgent".
    
.PARAMETER NssmPath
    Path to the NSSM executable. If not provided, NSSM will be downloaded.
    
.EXAMPLE
    .\install_service.ps1
    
.EXAMPLE
    .\install_service.ps1 -ConfigPath "D:\Config\agent_config.yaml" -ServiceName "CustomAgentService"
#>

param(
    [string]$ConfigPath = "C:\CsBotAgent\config.yaml",
    [string]$ScriptsPath = "C:\CsBotAgent\ActionScripts",
    [string]$LogsPath = "C:\CsBotAgent\Logs",
    [string]$ServiceName = "WindowsVMAgent",
    [string]$NssmPath = $null
)

# Function to download NSSM if not provided
function Get-Nssm {
    if ($NssmPath -and (Test-Path $NssmPath)) {
        return $NssmPath
    }
    
    $nssmDir = Join-Path $env:TEMP "nssm"
    $nssmZip = Join-Path $env:TEMP "nssm.zip"
    $nssmExe = Join-Path $nssmDir "nssm-2.24\win64\nssm.exe"
    
    if (-not (Test-Path $nssmExe)) {
        Write-Host "Downloading NSSM..."
        
        # Create directory if it doesn't exist
        if (-not (Test-Path $nssmDir)) {
            New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
        }
        
        # Download NSSM
        $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        
        # Extract NSSM
        Expand-Archive -Path $nssmZip -DestinationPath $nssmDir -Force
    }
    
    return $nssmExe
}

# Function to create directories and copy files
function Initialize-Directories {
    # Create base directory
    $baseDir = Split-Path $ConfigPath -Parent
    if (-not (Test-Path $baseDir)) {
        New-Item -ItemType Directory -Path $baseDir -Force | Out-Null
        Write-Host "Created directory: $baseDir"
    }
    
    # Create scripts directory
    if (-not (Test-Path $ScriptsPath)) {
        New-Item -ItemType Directory -Path $ScriptsPath -Force | Out-Null
        Write-Host "Created directory: $ScriptsPath"
    }
    
    # Create logs directory
    if (-not (Test-Path $LogsPath)) {
        New-Item -ItemType Directory -Path $LogsPath -Force | Out-Null
        Write-Host "Created directory: $LogsPath"
    }
    
    # Copy configuration file if it doesn't exist
    if (-not (Test-Path $ConfigPath)) {
        $sampleConfig = Join-Path $PSScriptRoot "config.yaml"
        if (Test-Path $sampleConfig) {
            Copy-Item -Path $sampleConfig -Destination $ConfigPath
            Write-Host "Copied sample configuration to: $ConfigPath"
        }
        else {
            Write-Warning "Sample configuration not found at: $sampleConfig"
        }
    }
    
    # Copy action scripts if they don't exist
    $actionScriptsDir = Join-Path $PSScriptRoot "action_scripts"
    if (Test-Path $actionScriptsDir) {
        $scripts = Get-ChildItem -Path $actionScriptsDir -Filter "*.ps1"
        foreach ($script in $scripts) {
            $destPath = Join-Path $ScriptsPath $script.Name
            if (-not (Test-Path $destPath)) {
                Copy-Item -Path $script.FullName -Destination $destPath
                Write-Host "Copied script: $($script.Name) to $ScriptsPath"
            }
        }
    }
    else {
        Write-Warning "Action scripts directory not found at: $actionScriptsDir"
    }
}

# Function to install the service
function Install-AgentService {
    param(
        [string]$NssmExePath
    )
    
    # Check if Python is installed
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonPath) {
        Write-Error "Python is not installed or not in PATH. Please install Python 3.7 or later."
        exit 1
    }
    
    # Check if the service already exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Warning "Service '$ServiceName' already exists. Removing it first..."
        & $NssmExePath remove $ServiceName confirm
    }
    
    # Get the path to the main.py script
    $mainScript = Join-Path $PSScriptRoot "main.py"
    if (-not (Test-Path $mainScript)) {
        Write-Error "Agent main script not found at: $mainScript"
        exit 1
    }
    
    # Install the service
    Write-Host "Installing service '$ServiceName'..."
    & $NssmExePath install $ServiceName $pythonPath """$mainScript"" --config ""$ConfigPath"" --log-dir ""$LogsPath"""
    
    # Configure service details
    & $NssmExePath set $ServiceName DisplayName "Windows VM Agent"
    & $NssmExePath set $ServiceName Description "Dynamic Windows VM Agent for monitoring and executing actions"
    & $NssmExePath set $ServiceName Start SERVICE_AUTO_START
    
    # Configure stdout/stderr logging
    $logFile = Join-Path $LogsPath "service.log"
    & $NssmExePath set $ServiceName AppStdout $logFile
    & $NssmExePath set $ServiceName AppStderr $logFile
    
    # Start the service
    Write-Host "Starting service '$ServiceName'..."
    & $NssmExePath start $ServiceName
    
    # Check if service started successfully
    Start-Sleep -Seconds 2
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq 'Running') {
        Write-Host "Service '$ServiceName' installed and started successfully."
    }
    else {
        Write-Warning "Service '$ServiceName' installed but failed to start. Check logs at: $logFile"
    }
}

# Main script execution
try {
    Write-Host "Installing Windows VM Agent as a service..."
    
    # Get NSSM
    $nssmExe = Get-Nssm
    Write-Host "Using NSSM: $nssmExe"
    
    # Initialize directories and copy files
    Initialize-Directories
    
    # Install the service
    Install-AgentService -NssmExePath $nssmExe
    
    Write-Host "Installation completed."
}
catch {
    Write-Error "Error installing service: $_"
    exit 1
}
