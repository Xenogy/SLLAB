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

        # Check if BITS module is available
        $useBITS = $false
        try {
            # Check if BITS module is available
            if (Get-Module -ListAvailable -Name BitsTransfer) {
                $useBITS = $true
                Write-Host "Using BITS for optimal NSSM download performance..."
                Import-Module BitsTransfer
            } else {
                Write-Host "BITS module not available, falling back to WebClient for NSSM download..."
            }
        } catch {
            Write-Host "Error checking for BITS module, falling back to WebClient for NSSM download: $_"
        }

        if ($useBITS) {
            # Use BITS for fastest download with resume capability
            try {
                # Remove any existing BITS transfer with the same name
                Get-BitsTransfer -Name "NSSMDownload" -ErrorAction SilentlyContinue | Remove-BitsTransfer

                # Start the BITS transfer
                Start-BitsTransfer -Source $nssmUrl -Destination $nssmZip -DisplayName "NSSM Download" -Description "Downloading NSSM" -Asynchronous -TransferType Download -Priority High

                # Get the BITS transfer
                $bitsJob = Get-BitsTransfer -Name "NSSMDownload"

                # Wait for the download to complete with progress
                while ($bitsJob.JobState -eq "Transferring" -or $bitsJob.JobState -eq "Connecting") {
                    $percentComplete = 0
                    if ($bitsJob.BytesTotal -gt 0) {
                        $percentComplete = [int](($bitsJob.BytesTransferred * 100) / $bitsJob.BytesTotal)
                    }

                    Write-Progress -Activity "Downloading NSSM" -Status "$percentComplete% Complete" -PercentComplete $percentComplete
                    Start-Sleep -Seconds 1
                    $bitsJob = Get-BitsTransfer -Name "NSSMDownload"
                }

                # Complete the BITS transfer
                if ($bitsJob.JobState -eq "Transferred") {
                    Complete-BitsTransfer -BitsJob $bitsJob
                    Write-Progress -Activity "Downloading NSSM" -Completed
                    Write-Host "NSSM download completed successfully using BITS."
                } else {
                    Write-Host "BITS transfer failed with state: $($bitsJob.JobState)"
                    throw "BITS transfer failed: $($bitsJob.ErrorDescription)"
                }
            } catch {
                Write-Host "Error using BITS for NSSM download, falling back to WebClient: $_"
                $useBITS = $false
            }
        }

        if (-not $useBITS) {
            # Use System.Net.WebClient as fallback
            Write-Host "Using WebClient for NSSM download..."
            $webClient = New-Object System.Net.WebClient

            # Add event handler for download progress
            $webClient.DownloadProgressChanged = {
                $percent = $_.ProgressPercentage
                if ($percent % 10 -eq 0) {  # Only show every 10%
                    Write-Progress -Activity "Downloading NSSM" -Status "$percent% Complete" -PercentComplete $percent
                }
            }

            # Add event handler for download completion
            $webClient.DownloadFileCompleted = {
                Write-Progress -Activity "Downloading NSSM" -Completed
                Write-Host "NSSM download completed."
            }

            # Start the download
            $webClient.DownloadFileAsync($nssmUrl, $nssmZip)

            # Wait for download to complete
            while ($webClient.IsBusy) {
                Start-Sleep -Milliseconds 100
            }
        }

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
