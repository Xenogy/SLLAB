param(
    [Parameter(Mandatory=$true)]
    [string]$ProxyAddress,
    
    [Parameter(Mandatory=$false)]
    [string]$BypassList = "localhost,127.0.0.1"
)

<#
.SYNOPSIS
    Sets the system proxy settings.
    
.DESCRIPTION
    This script sets the system proxy settings for the current user and optionally for the system.
    
.PARAMETER ProxyAddress
    The proxy server address and port (e.g., "http://proxy.example.com:8080").
    
.PARAMETER BypassList
    A semicolon-separated list of addresses that should bypass the proxy.
    Default is "localhost,127.0.0.1".
    
.EXAMPLE
    .\Set-Proxy.ps1 -ProxyAddress "http://proxy.example.com:8080" -BypassList "localhost;127.0.0.1;*.local"
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
    
    # You could also write to a log file
    # Add-Content -Path "C:\CsBotAgent\Logs\proxy-settings.log" -Value $logMessage
}

try {
    Write-Log "Setting proxy to $ProxyAddress with bypass list: $BypassList"
    
    # Format the bypass list (replace commas with semicolons if needed)
    $formattedBypassList = $BypassList -replace ',', ';'
    
    # Set WinHTTP proxy settings (system-wide)
    $command = "netsh winhttp set proxy proxy-server=`"$ProxyAddress`" bypass-list=`"$formattedBypassList`""
    Write-Log "Executing: $command" -Level "DEBUG"
    Invoke-Expression $command
    
    # Set Internet Explorer proxy settings (user-specific)
    $regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    
    # Enable proxy
    Set-ItemProperty -Path $regKey -Name ProxyEnable -Value 1 -Type DWord
    
    # Set proxy address
    Set-ItemProperty -Path $regKey -Name ProxyServer -Value $ProxyAddress
    
    # Set bypass list
    Set-ItemProperty -Path $regKey -Name ProxyOverride -Value $formattedBypassList
    
    # Refresh system settings
    $signature = @'
[DllImport("wininet.dll", SetLastError = true, CharSet=CharSet.Auto)]
public static extern bool InternetSetOption(IntPtr hInternet, int dwOption, IntPtr lpBuffer, int dwBufferLength);
'@
    
    $type = Add-Type -MemberDefinition $signature -Name WinInet -Namespace PInvoke -PassThru
    $INTERNET_OPTION_SETTINGS_CHANGED = 39
    $INTERNET_OPTION_REFRESH = 37
    $type::InternetSetOption(0, $INTERNET_OPTION_SETTINGS_CHANGED, 0, 0) | Out-Null
    $type::InternetSetOption(0, $INTERNET_OPTION_REFRESH, 0, 0) | Out-Null
    
    Write-Log "Proxy settings applied successfully" -Level "INFO"
    exit 0
}
catch {
    Write-Log "Error setting proxy: $_" -Level "ERROR"
    exit 1
}
