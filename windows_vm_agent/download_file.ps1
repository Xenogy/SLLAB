#Requires -Version 5.0

<#
.SYNOPSIS
    Download a file using the most efficient method available.
    
.DESCRIPTION
    This script downloads a file using the most efficient method available on the system.
    It will try BITS first, then fall back to WebClient, and finally Invoke-WebRequest.
    
.PARAMETER Url
    The URL to download the file from.
    
.PARAMETER OutputPath
    The path where the downloaded file should be saved.
    
.PARAMETER ShowProgress
    Whether to show download progress. Default is $true.
    
.EXAMPLE
    .\download_file.ps1 -Url "http://example.com/file.zip" -OutputPath "C:\temp\file.zip"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Url,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    
    [Parameter(Mandatory=$false)]
    [bool]$ShowProgress = $true
)

# Set TLS 1.2 for secure downloads
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Function to format file size
function Format-FileSize {
    param([long]$Size)
    
    if ($Size -ge 1GB) {
        return "{0:N2} GB" -f ($Size / 1GB)
    } elseif ($Size -ge 1MB) {
        return "{0:N2} MB" -f ($Size / 1MB)
    } elseif ($Size -ge 1KB) {
        return "{0:N2} KB" -f ($Size / 1KB)
    } else {
        return "$Size bytes"
    }
}

# Function to format speed
function Format-Speed {
    param([double]$BytesPerSecond)
    
    if ($BytesPerSecond -ge 1GB) {
        return "{0:N2} GB/s" -f ($BytesPerSecond / 1GB)
    } elseif ($BytesPerSecond -ge 1MB) {
        return "{0:N2} MB/s" -f ($BytesPerSecond / 1MB)
    } elseif ($BytesPerSecond -ge 1KB) {
        return "{0:N2} KB/s" -f ($BytesPerSecond / 1KB)
    } else {
        return "$BytesPerSecond bytes/s"
    }
}

# Create directory for the output file if it doesn't exist
$outputDir = Split-Path -Parent $OutputPath
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Start measuring download time
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Try BITS first (fastest with resume capability)
$useBITS = $false
try {
    if (Get-Module -ListAvailable -Name BitsTransfer) {
        $useBITS = $true
        Write-Host "Using BITS for optimal download performance..." -ForegroundColor Cyan
        Import-Module BitsTransfer
        
        # Remove any existing BITS transfer with the same name
        Get-BitsTransfer -Name "FileDownload" -ErrorAction SilentlyContinue | Remove-BitsTransfer
        
        # Start the BITS transfer
        Start-BitsTransfer -Source $Url -Destination $OutputPath -DisplayName "FileDownload" -Description "Downloading File" -Asynchronous -TransferType Download -Priority High
        
        # Get the BITS transfer
        $bitsJob = Get-BitsTransfer -Name "FileDownload"
        
        # Wait for the download to complete with progress
        while ($bitsJob.JobState -eq "Transferring" -or $bitsJob.JobState -eq "Connecting") {
            $percentComplete = 0
            if ($bitsJob.BytesTotal -gt 0) {
                $percentComplete = [int](($bitsJob.BytesTransferred * 100) / $bitsJob.BytesTotal)
            }
            
            if ($ShowProgress) {
                Write-Progress -Activity "Downloading File" -Status "$percentComplete% Complete" -PercentComplete $percentComplete
            }
            Start-Sleep -Milliseconds 500
            $bitsJob = Get-BitsTransfer -Name "FileDownload"
        }
        
        # Complete the BITS transfer
        if ($bitsJob.JobState -eq "Transferred") {
            Complete-BitsTransfer -BitsJob $bitsJob
            if ($ShowProgress) {
                Write-Progress -Activity "Downloading File" -Completed
            }
            Write-Host "Download completed successfully using BITS." -ForegroundColor Green
        } else {
            Write-Host "BITS transfer failed with state: $($bitsJob.JobState)" -ForegroundColor Red
            throw "BITS transfer failed: $($bitsJob.ErrorDescription)"
        }
    }
} catch {
    Write-Host "Error using BITS, falling back to WebClient: $_" -ForegroundColor Yellow
    $useBITS = $false
}

# If BITS failed or is not available, try WebClient
if (-not $useBITS) {
    try {
        Write-Host "Using WebClient for download..." -ForegroundColor Cyan
        $webClient = New-Object System.Net.WebClient
        
        if ($ShowProgress) {
            # Add event handler for download progress
            $webClient.DownloadProgressChanged = {
                $percent = $_.ProgressPercentage
                Write-Progress -Activity "Downloading File" -Status "$percent% Complete" -PercentComplete $percent
            }
            
            # Add event handler for download completion
            $webClient.DownloadFileCompleted = {
                Write-Progress -Activity "Downloading File" -Completed
                Write-Host "Download completed." -ForegroundColor Green
            }
            
            # Start the download asynchronously
            $webClient.DownloadFileAsync([Uri]$Url, $OutputPath)
            
            # Wait for download to complete
            while ($webClient.IsBusy) {
                Start-Sleep -Milliseconds 100
            }
        } else {
            # Download synchronously without progress
            $webClient.DownloadFile($Url, $OutputPath)
            Write-Host "Download completed." -ForegroundColor Green
        }
    } catch {
        Write-Host "Error using WebClient, falling back to Invoke-WebRequest: $_" -ForegroundColor Yellow
        
        try {
            Write-Host "Using Invoke-WebRequest for download..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
            Write-Host "Download completed using Invoke-WebRequest." -ForegroundColor Green
        } catch {
            Write-Host "Error downloading file: $_" -ForegroundColor Red
            exit 1
        }
    }
}

$stopwatch.Stop()

# Display download statistics
if (Test-Path $OutputPath) {
    $fileSize = (Get-Item $OutputPath).Length
    $downloadTime = $stopwatch.Elapsed.TotalSeconds
    $speed = $fileSize / $downloadTime
    
    Write-Host "Download Statistics:" -ForegroundColor Cyan
    Write-Host "  File Size: $(Format-FileSize -Size $fileSize)"
    Write-Host "  Download Time: $($downloadTime.ToString("N2")) seconds"
    Write-Host "  Average Speed: $(Format-Speed -BytesPerSecond $speed)"
    
    # Return success
    return $true
} else {
    Write-Host "Download failed: Output file not found." -ForegroundColor Red
    return $false
}
