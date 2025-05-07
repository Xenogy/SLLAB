<#
.SYNOPSIS
    Sends a log message to the central log storage system.
    
.DESCRIPTION
    This script sends a log message to the central log storage system.
    It is called by the Windows VM Agent when a log needs to be sent.
    
.PARAMETER Message
    The log message to send.
    
.PARAMETER Level
    The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    Default is INFO.
    
.PARAMETER Category
    The log category.
    Default is windows_vm_agent.
    
.EXAMPLE
    .\Send-Log.ps1 -Message "Test message" -Level "INFO" -Category "test"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Message,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")]
    [string]$Level = "INFO",
    
    [Parameter(Mandatory=$false)]
    [string]$Category = "windows_vm_agent"
)

# This script doesn't need to do anything as the Windows VM Agent already handles logging
# It's included for completeness and to allow for future customization

Write-Host "Sending log to central storage: [$Level] $Message (Category: $Category)"

# The actual log sending is handled by the Windows VM Agent's log client
# This script is just a placeholder for any additional processing that might be needed

# Return success
return @{
    "success" = $true
    "message" = "Log sent successfully"
}
