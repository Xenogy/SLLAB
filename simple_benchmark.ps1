#Requires -Version 5.0

<#
.SYNOPSIS
    Simple benchmark for Windows VM Agent download methods.
    
.DESCRIPTION
    This script benchmarks different download methods for the Windows VM Agent.
    
.PARAMETER DownloadUrl
    The URL to download the Windows VM Agent from.
    
.EXAMPLE
    .\simple_benchmark.ps1 -DownloadUrl "http://your-server/downloads/windows_vm_agent.zip"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$DownloadUrl
)

# Create temporary directory for downloads
$tempDir = Join-Path $env:TEMP "download_benchmark"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
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

# Create results array
$results = @()

# Test Invoke-WebRequest
Write-Host "Testing Invoke-WebRequest..." -ForegroundColor Cyan
$outputPath = Join-Path $tempDir "invoke_webrequest.zip"
if (Test-Path $outputPath) {
    Remove-Item -Path $outputPath -Force
}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $outputPath -UseBasicParsing
    $stopwatch.Stop()
    
    $fileSize = (Get-Item $outputPath).Length
    $downloadTime = $stopwatch.Elapsed.TotalSeconds
    $speed = $fileSize / $downloadTime
    
    $result = [PSCustomObject]@{
        Method = "Invoke-WebRequest"
        FileSize = $fileSize
        FileSizeFormatted = Format-FileSize -Size $fileSize
        DownloadTime = $downloadTime
        DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
        Speed = $speed
        SpeedFormatted = Format-Speed -BytesPerSecond $speed
    }
    
    Write-Host "  Downloaded $($result.FileSizeFormatted) in $($result.DownloadTimeFormatted) at $($result.SpeedFormatted)" -ForegroundColor Green
    $results += $result
}
catch {
    $stopwatch.Stop()
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test WebClient
Write-Host "Testing System.Net.WebClient..." -ForegroundColor Cyan
$outputPath = Join-Path $tempDir "webclient.zip"
if (Test-Path $outputPath) {
    Remove-Item -Path $outputPath -Force
}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($DownloadUrl, $outputPath)
    $stopwatch.Stop()
    
    $fileSize = (Get-Item $outputPath).Length
    $downloadTime = $stopwatch.Elapsed.TotalSeconds
    $speed = $fileSize / $downloadTime
    
    $result = [PSCustomObject]@{
        Method = "System.Net.WebClient"
        FileSize = $fileSize
        FileSizeFormatted = Format-FileSize -Size $fileSize
        DownloadTime = $downloadTime
        DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
        Speed = $speed
        SpeedFormatted = Format-Speed -BytesPerSecond $speed
    }
    
    Write-Host "  Downloaded $($result.FileSizeFormatted) in $($result.DownloadTimeFormatted) at $($result.SpeedFormatted)" -ForegroundColor Green
    $results += $result
}
catch {
    $stopwatch.Stop()
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test BITS
Write-Host "Testing BITS..." -ForegroundColor Cyan
$outputPath = Join-Path $tempDir "bits.zip"
if (Test-Path $outputPath) {
    Remove-Item -Path $outputPath -Force
}

# Check if BITS module is available
if (-not (Get-Module -ListAvailable -Name BitsTransfer)) {
    Write-Host "  BITS module not available. Skipping BITS benchmark." -ForegroundColor Yellow
} else {
    Import-Module BitsTransfer
    
    # Remove any existing BITS transfer with the same name
    Get-BitsTransfer -Name "BenchmarkDownload" -ErrorAction SilentlyContinue | Remove-BitsTransfer
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        Start-BitsTransfer -Source $DownloadUrl -Destination $outputPath -DisplayName "BenchmarkDownload" -Description "Benchmark Download"
        $stopwatch.Stop()
        
        $fileSize = (Get-Item $outputPath).Length
        $downloadTime = $stopwatch.Elapsed.TotalSeconds
        $speed = $fileSize / $downloadTime
        
        $result = [PSCustomObject]@{
            Method = "BITS"
            FileSize = $fileSize
            FileSizeFormatted = Format-FileSize -Size $fileSize
            DownloadTime = $downloadTime
            DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
            Speed = $speed
            SpeedFormatted = Format-Speed -BytesPerSecond $speed
        }
        
        Write-Host "  Downloaded $($result.FileSizeFormatted) in $($result.DownloadTimeFormatted) at $($result.SpeedFormatted)" -ForegroundColor Green
        $results += $result
    }
    catch {
        $stopwatch.Stop()
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Display comparison
Write-Host "`nComparison of Download Methods:" -ForegroundColor Green
Write-Host "=============================="

$results | Sort-Object -Property DownloadTime | Format-Table -Property Method, FileSizeFormatted, DownloadTimeFormatted, SpeedFormatted

# Identify the fastest method
$fastestMethod = $results | Sort-Object -Property DownloadTime | Select-Object -First 1
if ($fastestMethod) {
    Write-Host "`nFastest Method: $($fastestMethod.Method) with download time of $($fastestMethod.DownloadTimeFormatted)" -ForegroundColor Cyan

    # Calculate improvement over Invoke-WebRequest
    $invokeWebRequestResult = $results | Where-Object { $_.Method -eq "Invoke-WebRequest" }
    if ($invokeWebRequestResult) {
        $improvement = (1 - ($fastestMethod.DownloadTime / $invokeWebRequestResult.DownloadTime)) * 100
        Write-Host "Improvement over Invoke-WebRequest: $($improvement.ToString("N2"))%" -ForegroundColor Cyan
    }
}

# Clean up
Write-Host "`nCleaning up temporary files..." -ForegroundColor Gray
Remove-Item -Path (Join-Path $tempDir "*.zip") -Force -ErrorAction SilentlyContinue

Write-Host "`nBenchmark completed." -ForegroundColor Green
