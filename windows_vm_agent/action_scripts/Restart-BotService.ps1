param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [Parameter(Mandatory=$false)]
    [int]$TimeoutSeconds = 60
)

<#
.SYNOPSIS
    Restarts a Windows service.
    
.DESCRIPTION
    This script restarts a Windows service and waits for it to start.
    
.PARAMETER ServiceName
    The name of the service to restart.
    
.PARAMETER TimeoutSeconds
    The number of seconds to wait for the service to start.
    Default is 60 seconds.
    
.EXAMPLE
    .\Restart-BotService.ps1 -ServiceName "CSBot" -TimeoutSeconds 30
#>

# Log function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp [$Level] $Message"
    Write-Output $logMessage
    
    # Create logs directory if it doesn't exist
    $logDir = "C:\CsBotAgent\Logs"
    if (-not (Test-Path -Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # Write to log file
    Add-Content -Path "$logDir\service-restarts.log" -Value $logMessage
}

try {
    Write-Log "Attempting to restart service: $ServiceName" -Level "INFO"
    
    # Check if the service exists
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if (-not $service) {
        Write-Log "Service '$ServiceName' not found" -Level "ERROR"
        exit 1
    }
    
    # Check current service status
    $initialStatus = $service.Status
    Write-Log "Current service status: $initialStatus" -Level "INFO"
    
    # Restart the service
    Restart-Service -Name $ServiceName -Force
    
    # Wait for the service to start
    $startTime = Get-Date
    $serviceStarted = $false
    
    while (-not $serviceStarted -and ((Get-Date) - $startTime).TotalSeconds -lt $TimeoutSeconds) {
        Start-Sleep -Seconds 2
        $service = Get-Service -Name $ServiceName
        
        if ($service.Status -eq 'Running') {
            $serviceStarted = $true
            Write-Log "Service '$ServiceName' restarted successfully" -Level "INFO"
        }
        else {
            Write-Log "Waiting for service to start... Current status: $($service.Status)" -Level "INFO"
        }
    }
    
    if (-not $serviceStarted) {
        Write-Log "Service '$ServiceName' failed to start within $TimeoutSeconds seconds" -Level "ERROR"
        exit 1
    }
    
    exit 0
}
catch {
    Write-Log "Error restarting service: $_" -Level "ERROR"
    exit 1
}
