#Requires -Version 5.0

<#
.SYNOPSIS
    Run benchmarks for all download methods.
    
.DESCRIPTION
    This script runs benchmarks for all download methods and compares the results.
    
.PARAMETER DownloadUrl
    The URL to download the Windows VM Agent from.
    
.EXAMPLE
    .\run_benchmarks.ps1 -DownloadUrl "http://localhost:8000/downloads/windows_vm_agent.zip"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$DownloadUrl
)

# Create a results array
$results = @()

# Run the InvokeWebRequest benchmark
Write-Host "Running Invoke-WebRequest benchmark..." -ForegroundColor Yellow
$invokeResult = & "$PSScriptRoot\simple_benchmark.ps1" -DownloadUrl $DownloadUrl -Method "InvokeWebRequest"
$results += $invokeResult

# Run the WebClient benchmark
Write-Host "`nRunning WebClient benchmark..." -ForegroundColor Yellow
$webClientResult = & "$PSScriptRoot\simple_benchmark.ps1" -DownloadUrl $DownloadUrl -Method "WebClient"
$results += $webClientResult

# Run the BITS benchmark
Write-Host "`nRunning BITS benchmark..." -ForegroundColor Yellow
$bitsResult = & "$PSScriptRoot\simple_benchmark.ps1" -DownloadUrl $DownloadUrl -Method "BITS"
$results += $bitsResult

# Display comparison
Write-Host "`n`nComparison of Download Methods:" -ForegroundColor Green
Write-Host "=============================="

$results | Sort-Object -Property DownloadTime | Format-Table -Property Method, FileSizeFormatted, DownloadTimeFormatted, SpeedFormatted

# Identify the fastest method
$fastestMethod = $results | Sort-Object -Property DownloadTime | Select-Object -First 1
Write-Host "`nFastest Method: $($fastestMethod.Method) with download time of $($fastestMethod.DownloadTimeFormatted)" -ForegroundColor Cyan

# Calculate improvement over Invoke-WebRequest
$invokeWebRequestTime = ($results | Where-Object { $_.Method -eq "InvokeWebRequest" }).DownloadTime
if ($invokeWebRequestTime -gt 0) {
    $improvement = (1 - ($fastestMethod.DownloadTime / $invokeWebRequestTime)) * 100
    Write-Host "Improvement over Invoke-WebRequest: $($improvement.ToString("N2"))%" -ForegroundColor Cyan
}

# Save results to CSV
$csvPath = Join-Path $env:TEMP "download_benchmark_results.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation
Write-Host "`nResults saved to $csvPath" -ForegroundColor Green
