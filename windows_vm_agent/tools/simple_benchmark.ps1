#Requires -Version 5.0

<#
.SYNOPSIS
    Simple benchmark for Windows VM Agent download methods.
    
.DESCRIPTION
    This script benchmarks different download methods for the Windows VM Agent.
    
.PARAMETER DownloadUrl
    The URL to download the Windows VM Agent from.
    
.PARAMETER Method
    The download method to use: InvokeWebRequest, WebClient, or BITS.
    
.EXAMPLE
    .\simple_benchmark.ps1 -DownloadUrl "http://localhost:8000/downloads/windows_vm_agent.zip" -Method "BITS"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$DownloadUrl,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("InvokeWebRequest", "WebClient", "BITS")]
    [string]$Method
)

# Create temporary directory for downloads
$tempDir = Join-Path $env:TEMP "download_benchmark"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

$outputPath = Join-Path $tempDir "windows_vm_agent.zip"

# Clear any existing file
if (Test-Path $outputPath) {
    Remove-Item -Path $outputPath -Force
}

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

Write-Host "Starting download benchmark for $DownloadUrl using $Method" -ForegroundColor Green
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

try {
    switch ($Method) {
        "InvokeWebRequest" {
            Write-Host "Testing Invoke-WebRequest..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $outputPath -UseBasicParsing
        }
        "WebClient" {
            Write-Host "Testing System.Net.WebClient..." -ForegroundColor Cyan
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($DownloadUrl, $outputPath)
        }
        "BITS" {
            Write-Host "Testing BITS..." -ForegroundColor Cyan
            
            # Check if BITS module is available
            if (-not (Get-Module -ListAvailable -Name BitsTransfer)) {
                Write-Host "BITS module not available. Please install it or use a different method." -ForegroundColor Red
                exit 1
            }
            
            Import-Module BitsTransfer
            
            # Remove any existing BITS transfer with the same name
            Get-BitsTransfer -Name "BenchmarkDownload" -ErrorAction SilentlyContinue | Remove-BitsTransfer
            
            # Start the BITS transfer
            Start-BitsTransfer -Source $DownloadUrl -Destination $outputPath -DisplayName "BenchmarkDownload" -Description "Benchmark Download"
        }
    }
    
    $stopwatch.Stop()
    
    $fileSize = (Get-Item $outputPath).Length
    $downloadTime = $stopwatch.Elapsed.TotalSeconds
    $speed = $fileSize / $downloadTime
    
    Write-Host "Results:" -ForegroundColor Green
    Write-Host "========"
    Write-Host "Method: $Method"
    Write-Host "File Size: $(Format-FileSize -Size $fileSize)"
    Write-Host "Download Time: $($downloadTime.ToString("N2")) seconds"
    Write-Host "Speed: $(Format-Speed -BytesPerSecond $speed)"
    
    # Return the results as an object
    [PSCustomObject]@{
        Method = $Method
        FileSize = $fileSize
        FileSizeFormatted = Format-FileSize -Size $fileSize
        DownloadTime = $downloadTime
        DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
        Speed = $speed
        SpeedFormatted = Format-Speed -BytesPerSecond $speed
    }
}
catch {
    $stopwatch.Stop()
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Return error information
    [PSCustomObject]@{
        Method = $Method
        Error = $_.Exception.Message
        DownloadTime = $stopwatch.Elapsed.TotalSeconds
    }
}
finally {
    # Clean up
    if (Test-Path $outputPath) {
        Remove-Item -Path $outputPath -Force -ErrorAction SilentlyContinue
    }
}
