#Requires -Version 5.0

<#
.SYNOPSIS
    Benchmark the download performance of the Windows VM Agent.

.DESCRIPTION
    This script benchmarks the download performance of the Windows VM Agent using different download methods.
    It compares the performance of Invoke-WebRequest, System.Net.WebClient, and BITS.

.PARAMETER DownloadUrl
    The URL to download the Windows VM Agent from.

.PARAMETER Method
    The download method to use. Valid values are "InvokeWebRequest", "WebClient", "BITS", or "All".
    Default is "All" which tests all methods.

.PARAMETER OutputCsv
    Path to save the benchmark results as a CSV file. If not specified, results are only displayed on screen.

.EXAMPLE
    .\benchmark_download.ps1 -DownloadUrl "http://localhost:8000/downloads/windows_vm_agent.zip"

.EXAMPLE
    .\benchmark_download.ps1 -DownloadUrl "http://localhost:8000/downloads/windows_vm_agent.zip" -Method "BITS" -OutputCsv "benchmark_results.csv"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$DownloadUrl,

    [Parameter(Mandatory=$false)]
    [ValidateSet("InvokeWebRequest", "WebClient", "BITS", "All")]
    [string]$Method = "All",

    [Parameter(Mandatory=$false)]
    [string]$OutputCsv = ""
)

# Set a fixed number of iterations to simplify the script
$Iterations = 2

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

# Function to benchmark Invoke-WebRequest
function Benchmark-InvokeWebRequest {
    param([string]$Url, [string]$OutputPath)

    Write-Host "Testing Invoke-WebRequest..." -ForegroundColor Cyan

    $results = @()

    for ($i = 1; $i -le $Iterations; $i++) {
        Write-Host "  Iteration $i of $Iterations..." -ForegroundColor Gray

        # Clear any existing file
        if (Test-Path $OutputPath) {
            Remove-Item -Path $OutputPath -Force
        }

        # Measure download time
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        try {
            Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
            $stopwatch.Stop()

            $fileSize = (Get-Item $OutputPath).Length
            $downloadTime = $stopwatch.Elapsed.TotalSeconds
            $speed = $fileSize / $downloadTime

            $result = [PSCustomObject]@{
                Method = "Invoke-WebRequest"
                Iteration = $i
                FileSize = $fileSize
                FileSizeFormatted = Format-FileSize -Size $fileSize
                DownloadTime = $downloadTime
                DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
                Speed = $speed
                SpeedFormatted = Format-Speed -BytesPerSecond $speed
                Success = $true
                ErrorMessage = ""
            }

            Write-Host "    Downloaded $($result.FileSizeFormatted) in $($result.DownloadTimeFormatted) at $($result.SpeedFormatted)" -ForegroundColor Green
        }
        catch {
            $stopwatch.Stop()

            $result = [PSCustomObject]@{
                Method = "Invoke-WebRequest"
                Iteration = $i
                FileSize = 0
                FileSizeFormatted = "0 bytes"
                DownloadTime = $stopwatch.Elapsed.TotalSeconds
                DownloadTimeFormatted = "{0:N2} seconds" -f $stopwatch.Elapsed.TotalSeconds
                Speed = 0
                SpeedFormatted = "0 bytes/s"
                Success = $false
                ErrorMessage = $_.Exception.Message
            }

            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }

        $results += $result
    }

    return $results
}

# Function to benchmark System.Net.WebClient
function Benchmark-WebClient {
    param([string]$Url, [string]$OutputPath)

    Write-Host "Testing System.Net.WebClient..." -ForegroundColor Cyan

    $results = @()

    for ($i = 1; $i -le $Iterations; $i++) {
        Write-Host "  Iteration $i of $Iterations..." -ForegroundColor Gray

        # Clear any existing file
        if (Test-Path $OutputPath) {
            Remove-Item -Path $OutputPath -Force
        }

        # Measure download time
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        try {
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($Url, $OutputPath)
            $stopwatch.Stop()

            $fileSize = (Get-Item $OutputPath).Length
            $downloadTime = $stopwatch.Elapsed.TotalSeconds
            $speed = $fileSize / $downloadTime

            $result = [PSCustomObject]@{
                Method = "System.Net.WebClient"
                Iteration = $i
                FileSize = $fileSize
                FileSizeFormatted = Format-FileSize -Size $fileSize
                DownloadTime = $downloadTime
                DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
                Speed = $speed
                SpeedFormatted = Format-Speed -BytesPerSecond $speed
                Success = $true
                ErrorMessage = ""
            }

            Write-Host "    Downloaded $($result.FileSizeFormatted) in $($result.DownloadTimeFormatted) at $($result.SpeedFormatted)" -ForegroundColor Green
        }
        catch {
            $stopwatch.Stop()

            $result = [PSCustomObject]@{
                Method = "System.Net.WebClient"
                Iteration = $i
                FileSize = 0
                FileSizeFormatted = "0 bytes"
                DownloadTime = $stopwatch.Elapsed.TotalSeconds
                DownloadTimeFormatted = "{0:N2} seconds" -f $stopwatch.Elapsed.TotalSeconds
                Speed = 0
                SpeedFormatted = "0 bytes/s"
                Success = $false
                ErrorMessage = $_.Exception.Message
            }

            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }

        $results += $result
    }

    return $results
}

# Function to benchmark BITS
function Benchmark-BITS {
    param([string]$Url, [string]$OutputPath)

    Write-Host "Testing BITS..." -ForegroundColor Cyan

    # Check if BITS module is available
    if (-not (Get-Module -ListAvailable -Name BitsTransfer)) {
        Write-Host "  BITS module not available. Skipping BITS benchmark." -ForegroundColor Yellow
        return @()
    }

    Import-Module BitsTransfer

    $results = @()

    for ($i = 1; $i -le $Iterations; $i++) {
        Write-Host "  Iteration $i of $Iterations..." -ForegroundColor Gray

        # Clear any existing file
        if (Test-Path $OutputPath) {
            Remove-Item -Path $OutputPath -Force
        }

        # Remove any existing BITS transfer with the same name
        Get-BitsTransfer -Name "BenchmarkDownload" -ErrorAction SilentlyContinue | Remove-BitsTransfer

        # Measure download time
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        try {
            Start-BitsTransfer -Source $Url -Destination $OutputPath -DisplayName "BenchmarkDownload" -Description "Benchmark Download" -Asynchronous

            $bitsJob = Get-BitsTransfer -Name "BenchmarkDownload"

            while ($bitsJob.JobState -eq "Transferring" -or $bitsJob.JobState -eq "Connecting") {
                $percentComplete = 0
                if ($bitsJob.BytesTotal -gt 0) {
                    $percentComplete = [int](($bitsJob.BytesTransferred * 100) / $bitsJob.BytesTotal)
                }

                Write-Progress -Activity "Downloading with BITS" -Status "$percentComplete% Complete" -PercentComplete $percentComplete
                Start-Sleep -Seconds 1
                $bitsJob = Get-BitsTransfer -Name "BenchmarkDownload"
            }

            if ($bitsJob.JobState -eq "Transferred") {
                Complete-BitsTransfer -BitsJob $bitsJob
                $stopwatch.Stop()

                $fileSize = (Get-Item $OutputPath).Length
                $downloadTime = $stopwatch.Elapsed.TotalSeconds
                $speed = $fileSize / $downloadTime

                $result = [PSCustomObject]@{
                    Method = "BITS"
                    Iteration = $i
                    FileSize = $fileSize
                    FileSizeFormatted = Format-FileSize -Size $fileSize
                    DownloadTime = $downloadTime
                    DownloadTimeFormatted = "{0:N2} seconds" -f $downloadTime
                    Speed = $speed
                    SpeedFormatted = Format-Speed -BytesPerSecond $speed
                    Success = $true
                    ErrorMessage = ""
                }

                Write-Host "    Downloaded $($result.FileSizeFormatted) in $($result.DownloadTimeFormatted) at $($result.SpeedFormatted)" -ForegroundColor Green
            } else {
                $stopwatch.Stop()

                $result = [PSCustomObject]@{
                    Method = "BITS"
                    Iteration = $i
                    FileSize = 0
                    FileSizeFormatted = "0 bytes"
                    DownloadTime = $stopwatch.Elapsed.TotalSeconds
                    DownloadTimeFormatted = "{0:N2} seconds" -f $stopwatch.Elapsed.TotalSeconds
                    Speed = 0
                    SpeedFormatted = "0 bytes/s"
                    Success = $false
                    ErrorMessage = "BITS transfer failed with state: $($bitsJob.JobState)"
                }

                Write-Host "    Error: BITS transfer failed with state: $($bitsJob.JobState)" -ForegroundColor Red
            }
        }
        catch {
            $stopwatch.Stop()

            $result = [PSCustomObject]@{
                Method = "BITS"
                Iteration = $i
                FileSize = 0
                FileSizeFormatted = "0 bytes"
                DownloadTime = $stopwatch.Elapsed.TotalSeconds
                DownloadTimeFormatted = "{0:N2} seconds" -f $stopwatch.Elapsed.TotalSeconds
                Speed = 0
                SpeedFormatted = "0 bytes/s"
                Success = $false
                ErrorMessage = $_.Exception.Message
            }

            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }

        $results += $result
    }

    return $results
}

# Main script execution
Write-Host "Starting download benchmark for $DownloadUrl" -ForegroundColor Green
Write-Host "Running $Iterations iterations for each download method" -ForegroundColor Green
Write-Host ""

# Create temporary directory for downloads
$tempDir = Join-Path $env:TEMP "download_benchmark"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

$outputPath = Join-Path $tempDir "windows_vm_agent.zip"

# Run benchmarks
$invokeWebRequestResults = Benchmark-InvokeWebRequest -Url $DownloadUrl -OutputPath $outputPath
$webClientResults = Benchmark-WebClient -Url $DownloadUrl -OutputPath $outputPath
$bitsResults = Benchmark-BITS -Url $DownloadUrl -OutputPath $outputPath

# Combine results
$allResults = $invokeWebRequestResults + $webClientResults + $bitsResults

# Calculate averages
$averages = $allResults | Group-Object -Property Method | ForEach-Object {
    $successfulDownloads = $_.Group | Where-Object { $_.Success }
    $averageTime = ($successfulDownloads | Measure-Object -Property DownloadTime -Average).Average
    $averageSpeed = ($successfulDownloads | Measure-Object -Property Speed -Average).Average
    $successRate = ($successfulDownloads.Count / $_.Group.Count) * 100

    [PSCustomObject]@{
        Method = $_.Name
        AverageDownloadTime = $averageTime
        AverageDownloadTimeFormatted = "{0:N2} seconds" -f $averageTime
        AverageSpeed = $averageSpeed
        AverageSpeedFormatted = Format-Speed -BytesPerSecond $averageSpeed
        SuccessRate = $successRate
        SuccessRateFormatted = "{0:N2}%" -f $successRate
    }
}

# Display results
Write-Host ""
Write-Host "Benchmark Results:" -ForegroundColor Green
Write-Host "================="
Write-Host ""

$averages | Format-Table -Property Method, AverageDownloadTimeFormatted, AverageSpeedFormatted, SuccessRateFormatted -AutoSize

# Save results to CSV if requested
if ($OutputCsv) {
    $allResults | Export-Csv -Path $OutputCsv -NoTypeInformation
    Write-Host "Results saved to $OutputCsv" -ForegroundColor Green
}

# Clean up
Remove-Item -Path $outputPath -Force -ErrorAction SilentlyContinue
