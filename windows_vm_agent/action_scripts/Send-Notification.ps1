param(
    [Parameter(Mandatory=$true)]
    [string]$ErrorCode,
    
    [Parameter(Mandatory=$false)]
    [string]$AdditionalInfo = ""
)

<#
.SYNOPSIS
    Sends a notification about an error.
    
.DESCRIPTION
    This script sends a notification about an error, either via a local notification
    or by logging to a file. In a production environment, this could be extended to
    send emails, Slack messages, or other notifications.
    
.PARAMETER ErrorCode
    The error code that was detected.
    
.PARAMETER AdditionalInfo
    Additional information about the error.
    
.EXAMPLE
    .\Send-Notification.ps1 -ErrorCode "E1001" -AdditionalInfo "Connection timeout"
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
    Add-Content -Path "$logDir\error-notifications.log" -Value $logMessage
}

try {
    Write-Log "Processing error notification for code: $ErrorCode" -Level "WARNING"
    
    # Log the error
    $errorMessage = "Error code $ErrorCode detected"
    if ($AdditionalInfo) {
        $errorMessage += ": $AdditionalInfo"
    }
    
    Write-Log $errorMessage -Level "ERROR"
    
    # Display a toast notification (Windows 10/11)
    if ([Environment]::OSVersion.Version.Major -ge 10) {
        $appId = "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
        
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        
        $text = $xml.GetElementsByTagName("text")
        $text[0].AppendChild($xml.CreateTextNode("CSBot Error Detected")) | Out-Null
        $text[1].AppendChild($xml.CreateTextNode($errorMessage)) | Out-Null
        
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
        
        Write-Log "Toast notification displayed" -Level "INFO"
    }
    else {
        # Fallback for older Windows versions
        Write-Log "Toast notifications not supported on this Windows version" -Level "INFO"
    }
    
    # In a real implementation, you might want to:
    # 1. Send an email notification
    # 2. Send a message to a Slack/Teams channel
    # 3. Create a ticket in a ticketing system
    # 4. Log to a centralized logging system
    
    Write-Log "Error notification processed successfully" -Level "INFO"
    exit 0
}
catch {
    Write-Log "Error sending notification: $_" -Level "ERROR"
    exit 1
}
