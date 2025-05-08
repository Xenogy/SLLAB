"""
Downloads router.

This module provides endpoints for downloading files.
"""

import logging
import os
import shutil
import time
import zipfile
from typing import Dict, Any, Optional, List
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, Request, status
from fastapi.responses import FileResponse, StreamingResponse

from config import Config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/downloads",
    tags=["downloads"],
    responses={404: {"description": "Not found"}},
)

# Endpoints
@router.get("/test", response_class=FileResponse)
async def download_test_file():
    """
    Download a test file.
    """
    logger.info("Downloading test file")

    # Path to the test file
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "test.txt")

    # Check if the file exists
    if not os.path.exists(file_path):
        # Create a test file if it doesn't exist
        with open(file_path, "w") as f:
            f.write("This is a test file.")

    return FileResponse(
        path=file_path,
        filename="test.txt",
        media_type="text/plain"
    )

# Path to the cached Windows VM agent ZIP file
AGENT_ZIP_PATH = None
AGENT_ZIP_LAST_MODIFIED = 0
AGENT_ZIP_CACHE_TTL = 3600  # 1 hour in seconds

# Dictionary to store download progress information
DOWNLOAD_PROGRESS = {}
DOWNLOAD_STATS = {}

def create_agent_zip():
    """
    Create a ZIP file of the Windows VM agent.

    Returns:
        tuple: (zip_path, last_modified_time)
    """
    global AGENT_ZIP_PATH, AGENT_ZIP_LAST_MODIFIED

    # Get the absolute path to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    agent_dir = os.path.join(project_root, "windows_vm_agent")

    # Create a directory for cached files if it doesn't exist
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Path to the cached ZIP file
    zip_path = os.path.join(cache_dir, "windows_vm_agent.zip")

    # Check if the agent directory exists
    if not os.path.exists(agent_dir):
        logger.error(f"Windows VM agent directory not found: {agent_dir}")
        raise HTTPException(status_code=404, detail="Windows VM agent not found")

    try:
        # Create a ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Walk through the directory and add all files to the ZIP
            for root, dirs, files in os.walk(agent_dir):
                # Skip __pycache__ directories
                if "__pycache__" in root:
                    continue

                # Skip .git directories
                if ".git" in root:
                    continue

                # Skip .egg-info directories
                if ".egg-info" in root:
                    continue

                for file in files:
                    # Skip .pyc files
                    if file.endswith(".pyc"):
                        continue

                    # Skip .git files
                    if ".git" in file:
                        continue

                    # Get the full path of the file
                    file_path = os.path.join(root, file)

                    # Get the relative path for the ZIP file
                    rel_path = os.path.relpath(file_path, os.path.dirname(agent_dir))

                    # Add the file to the ZIP
                    zip_file.write(file_path, rel_path)

        # Get the last modified time
        last_modified = os.path.getmtime(zip_path)

        return zip_path, last_modified

    except Exception as e:
        logger.error(f"Error creating Windows VM agent ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Error creating Windows VM agent ZIP file")

class DownloadProgressTracker:
    """
    Class to track download progress.
    """
    def __init__(self, file_path, download_id):
        self.file_path = file_path
        self.download_id = download_id
        self.file_size = os.path.getsize(file_path)
        self.start_time = time.time()
        self.bytes_sent = 0
        self.last_update_time = time.time()
        self.completed = False

        # Initialize progress in the global dictionary
        DOWNLOAD_PROGRESS[download_id] = {
            "file_size": self.file_size,
            "bytes_sent": 0,
            "percent_complete": 0,
            "start_time": self.start_time,
            "last_update_time": self.last_update_time,
            "speed_bps": 0,
            "estimated_time_remaining": 0,
            "completed": False
        }

    async def __call__(self, file_path):
        """
        Generator function to yield file content in chunks while tracking progress.
        """
        with open(file_path, "rb") as f:
            chunk_size = 64 * 1024  # 64KB chunks
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                self.bytes_sent += len(chunk)
                current_time = time.time()

                # Update progress every 0.5 seconds
                if current_time - self.last_update_time >= 0.5:
                    self._update_progress(current_time)

                yield chunk

        # Mark download as completed
        self.completed = True
        DOWNLOAD_PROGRESS[self.download_id]["completed"] = True
        DOWNLOAD_PROGRESS[self.download_id]["percent_complete"] = 100

        # Store download stats
        elapsed_time = time.time() - self.start_time
        DOWNLOAD_STATS[self.download_id] = {
            "file_size": self.file_size,
            "elapsed_time": elapsed_time,
            "average_speed_bps": self.file_size / elapsed_time if elapsed_time > 0 else 0,
            "completed_at": time.time()
        }

    def _update_progress(self, current_time):
        """
        Update the progress information.
        """
        time_diff = current_time - self.last_update_time
        bytes_diff = self.bytes_sent - DOWNLOAD_PROGRESS[self.download_id]["bytes_sent"]

        # Calculate speed in bytes per second
        speed_bps = bytes_diff / time_diff if time_diff > 0 else 0

        # Calculate percent complete
        percent_complete = (self.bytes_sent * 100) / self.file_size if self.file_size > 0 else 0

        # Calculate estimated time remaining
        bytes_remaining = self.file_size - self.bytes_sent
        estimated_time_remaining = bytes_remaining / speed_bps if speed_bps > 0 else 0

        # Update progress information
        DOWNLOAD_PROGRESS[self.download_id].update({
            "bytes_sent": self.bytes_sent,
            "percent_complete": percent_complete,
            "last_update_time": current_time,
            "speed_bps": speed_bps,
            "estimated_time_remaining": estimated_time_remaining
        })

        self.last_update_time = current_time

@router.get("/windows_vm_agent.zip")
async def download_windows_vm_agent(request: Request):
    """
    Download the Windows VM agent as a ZIP file.

    This endpoint serves a pre-generated ZIP file of the Windows VM agent.
    The ZIP file is cached and regenerated only when needed.
    """
    global AGENT_ZIP_PATH, AGENT_ZIP_LAST_MODIFIED

    logger.info("Downloading Windows VM agent")

    current_time = time.time()

    # Check if we need to create or refresh the ZIP file
    if (AGENT_ZIP_PATH is None or
        not os.path.exists(AGENT_ZIP_PATH) or
        current_time - AGENT_ZIP_LAST_MODIFIED > AGENT_ZIP_CACHE_TTL):

        logger.info("Creating new Windows VM agent ZIP file")
        AGENT_ZIP_PATH, AGENT_ZIP_LAST_MODIFIED = create_agent_zip()
    else:
        logger.info(f"Using cached Windows VM agent ZIP file: {AGENT_ZIP_PATH}")

    # Generate a unique download ID
    download_id = f"windows_vm_agent_{int(time.time())}_{id(request)}"

    # Create a progress tracker
    progress_tracker = DownloadProgressTracker(AGENT_ZIP_PATH, download_id)

    # Return the ZIP file as a streaming response with progress tracking
    return StreamingResponse(
        progress_tracker(AGENT_ZIP_PATH),
        media_type="application/zip",
        headers={
            "Cache-Control": "public, max-age=3600",
            "ETag": f"\"{AGENT_ZIP_LAST_MODIFIED}\"",
            "Content-Disposition": "attachment; filename=windows_vm_agent.zip",
            "X-Download-ID": download_id
        }
    )

@router.get("/download-progress/{download_id}")
async def get_download_progress(download_id: str):
    """
    Get the progress of a download.

    Args:
        download_id: The ID of the download to get progress for.

    Returns:
        The progress information for the download.
    """
    if download_id not in DOWNLOAD_PROGRESS:
        raise HTTPException(status_code=404, detail="Download not found")

    progress = DOWNLOAD_PROGRESS[download_id]

    # Format the progress information for the response
    return {
        "download_id": download_id,
        "file_size": progress["file_size"],
        "bytes_sent": progress["bytes_sent"],
        "percent_complete": round(progress["percent_complete"], 2),
        "speed_bps": round(progress["speed_bps"], 2),
        "speed_mbps": round(progress["speed_bps"] / (1024 * 1024), 2),
        "estimated_time_remaining": round(progress["estimated_time_remaining"], 2),
        "completed": progress["completed"]
    }

@router.get("/download-stats")
async def get_download_stats():
    """
    Get statistics for all downloads.

    Returns:
        Statistics for all downloads.
    """
    stats = []

    for download_id, download_stat in DOWNLOAD_STATS.items():
        stats.append({
            "download_id": download_id,
            "file_size": download_stat["file_size"],
            "file_size_mb": round(download_stat["file_size"] / (1024 * 1024), 2),
            "elapsed_time": round(download_stat["elapsed_time"], 2),
            "average_speed_bps": round(download_stat["average_speed_bps"], 2),
            "average_speed_mbps": round(download_stat["average_speed_bps"] / (1024 * 1024), 2),
            "completed_at": download_stat["completed_at"]
        })

    return {"stats": stats}

@router.get("/install_agent.ps1")
async def download_install_agent_script():
    """
    Download the install_agent.ps1 script.

    This script is used to install the Windows VM agent.
    """
    logger.info("Downloading install_agent.ps1 script")

    # Path to the install_agent.ps1 script
    # Try multiple possible locations for the file
    possible_paths = [
        # Standard project root path
        os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                    "windows_vm_agent", "tools", "install_agent.ps1"),
        # Docker container path
        "/windows_vm_agent/tools/install_agent.ps1",
        # Absolute path
        "/home/axel/accountdb/windows_vm_agent/tools/install_agent.ps1"
    ]

    # Find the first path that exists
    script_path = None
    for path in possible_paths:
        if os.path.exists(path):
            script_path = path
            break

    logger.info(f"Looking for install_agent.ps1 script at: {script_path}")

    # Check if the file exists
    if not os.path.exists(script_path):
        logger.error(f"install_agent.ps1 script not found: {script_path}")
        raise HTTPException(status_code=404, detail="install_agent.ps1 script not found")

    # Return the script as a file response
    return FileResponse(
        path=script_path,
        filename="install_agent.ps1",
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "attachment; filename=install_agent.ps1"
        }
    )

@router.get("/simple_benchmark.ps1")
async def download_simple_benchmark_script():
    """
    Download the simple_benchmark.ps1 script.

    This script is used to benchmark download methods.
    """
    logger.info("Downloading simple_benchmark.ps1 script")

    # Path to the simple_benchmark.ps1 script
    # Try multiple possible locations for the file
    possible_paths = [
        # Standard project root path
        os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                    "windows_vm_agent", "tools", "simple_benchmark.ps1"),
        # Docker container path
        "/windows_vm_agent/tools/simple_benchmark.ps1",
        # Absolute path
        "/home/axel/accountdb/windows_vm_agent/tools/simple_benchmark.ps1"
    ]

    # Find the first path that exists
    script_path = None
    for path in possible_paths:
        if os.path.exists(path):
            script_path = path
            break

    logger.info(f"Looking for simple_benchmark.ps1 script at: {script_path}")

    # Check if the file exists
    if not os.path.exists(script_path):
        logger.error(f"simple_benchmark.ps1 script not found: {script_path}")
        raise HTTPException(status_code=404, detail="simple_benchmark.ps1 script not found")

    # Return the script as a file response
    return FileResponse(
        path=script_path,
        filename="simple_benchmark.ps1",
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "attachment; filename=simple_benchmark.ps1"
        }
    )

@router.get("/run_benchmarks.ps1")
async def download_run_benchmarks_script():
    """
    Download the run_benchmarks.ps1 script.

    This script is used to run all benchmark tests.
    """
    logger.info("Downloading run_benchmarks.ps1 script")

    # Path to the run_benchmarks.ps1 script
    # Try multiple possible locations for the file
    possible_paths = [
        # Standard project root path
        os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                    "windows_vm_agent", "tools", "run_benchmarks.ps1"),
        # Docker container path
        "/windows_vm_agent/tools/run_benchmarks.ps1",
        # Absolute path
        "/home/axel/accountdb/windows_vm_agent/tools/run_benchmarks.ps1"
    ]

    # Find the first path that exists
    script_path = None
    for path in possible_paths:
        if os.path.exists(path):
            script_path = path
            break

    logger.info(f"Looking for run_benchmarks.ps1 script at: {script_path}")

    # Check if the file exists
    if not os.path.exists(script_path):
        logger.error(f"run_benchmarks.ps1 script not found: {script_path}")
        raise HTTPException(status_code=404, detail="run_benchmarks.ps1 script not found")

    # Return the script as a file response
    return FileResponse(
        path=script_path,
        filename="run_benchmarks.ps1",
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "attachment; filename=run_benchmarks.ps1"
        }
    )

@router.get("/benchmark_command")
async def get_benchmark_command(request: Request):
    """
    Get a simple PowerShell command to run the benchmarks.

    This endpoint returns a PowerShell command that can be copied and pasted into a PowerShell window.
    """
    logger.info("Getting benchmark command")

    # Generate a simple command that runs the benchmark directly
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    download_url = f"{server_url}/downloads/windows_vm_agent.zip"

    # Create a very simple benchmark command with explicit steps
    command = f'''powershell -ExecutionPolicy Bypass -Command "
# Set TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Define variables
$downloadUrl = '{download_url}'
$tempDir = Join-Path $env:TEMP 'download_benchmark'

# Create temporary directory
if (-not (Test-Path $tempDir)) {{
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}}

# Define helper functions
function Format-FileSize {{
    param([long]$Size)

    if ($Size -ge 1GB) {{
        return '{0:N2} GB' -f ($Size / 1GB)
    }} elseif ($Size -ge 1MB) {{
        return '{0:N2} MB' -f ($Size / 1MB)
    }} elseif ($Size -ge 1KB) {{
        return '{0:N2} KB' -f ($Size / 1KB)
    }} else {{
        return '$Size bytes'
    }}
}}

function Format-Speed {{
    param([double]$BytesPerSecond)

    if ($BytesPerSecond -ge 1GB) {{
        return '{0:N2} GB/s' -f ($BytesPerSecond / 1GB)
    }} elseif ($BytesPerSecond -ge 1MB) {{
        return '{0:N2} MB/s' -f ($BytesPerSecond / 1MB)
    }} elseif ($BytesPerSecond -ge 1KB) {{
        return '{0:N2} KB/s' -f ($BytesPerSecond / 1KB)
    }} else {{
        return '$BytesPerSecond bytes/s'
    }}
}}

# Create results array
$results = @()

# Test Invoke-WebRequest
Write-Host 'Testing Invoke-WebRequest...' -ForegroundColor Cyan
$outputPath = Join-Path $tempDir 'invoke_webrequest.zip'
if (Test-Path $outputPath) {{
    Remove-Item -Path $outputPath -Force
}}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
try {{
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath -UseBasicParsing
    $stopwatch.Stop()

    $fileSize = (Get-Item $outputPath).Length
    $downloadTime = $stopwatch.Elapsed.TotalSeconds
    $speed = $fileSize / $downloadTime

    $result = [PSCustomObject]@{{
        Method = 'Invoke-WebRequest'
        FileSize = $fileSize
        FileSizeFormatted = Format-FileSize -Size $fileSize
        DownloadTime = $downloadTime
        DownloadTimeFormatted = '{0:N2} seconds' -f $downloadTime
        Speed = $speed
        SpeedFormatted = Format-Speed -BytesPerSecond $speed
    }}

    Write-Host ('  Downloaded ' + $result.FileSizeFormatted + ' in ' + $result.DownloadTimeFormatted + ' at ' + $result.SpeedFormatted) -ForegroundColor Green
    $results += $result
}}
catch {{
    $stopwatch.Stop()
    Write-Host ('  Error: ' + $_.Exception.Message) -ForegroundColor Red
}}

# Test WebClient
Write-Host 'Testing System.Net.WebClient...' -ForegroundColor Cyan
$outputPath = Join-Path $tempDir 'webclient.zip'
if (Test-Path $outputPath) {{
    Remove-Item -Path $outputPath -Force
}}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
try {{
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $outputPath)
    $stopwatch.Stop()

    $fileSize = (Get-Item $outputPath).Length
    $downloadTime = $stopwatch.Elapsed.TotalSeconds
    $speed = $fileSize / $downloadTime

    $result = [PSCustomObject]@{{
        Method = 'System.Net.WebClient'
        FileSize = $fileSize
        FileSizeFormatted = Format-FileSize -Size $fileSize
        DownloadTime = $downloadTime
        DownloadTimeFormatted = '{0:N2} seconds' -f $downloadTime
        Speed = $speed
        SpeedFormatted = Format-Speed -BytesPerSecond $speed
    }}

    Write-Host ('  Downloaded ' + $result.FileSizeFormatted + ' in ' + $result.DownloadTimeFormatted + ' at ' + $result.SpeedFormatted) -ForegroundColor Green
    $results += $result
}}
catch {{
    $stopwatch.Stop()
    Write-Host ('  Error: ' + $_.Exception.Message) -ForegroundColor Red
}}

# Test BITS
Write-Host 'Testing BITS...' -ForegroundColor Cyan
$outputPath = Join-Path $tempDir 'bits.zip'
if (Test-Path $outputPath) {{
    Remove-Item -Path $outputPath -Force
}}

# Check if BITS module is available
if (-not (Get-Module -ListAvailable -Name BitsTransfer)) {{
    Write-Host '  BITS module not available. Skipping BITS benchmark.' -ForegroundColor Yellow
}} else {{
    Import-Module BitsTransfer

    # Remove any existing BITS transfer with the same name
    Get-BitsTransfer -Name 'BenchmarkDownload' -ErrorAction SilentlyContinue | Remove-BitsTransfer

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {{
        Start-BitsTransfer -Source $downloadUrl -Destination $outputPath -DisplayName 'BenchmarkDownload' -Description 'Benchmark Download'
        $stopwatch.Stop()

        $fileSize = (Get-Item $outputPath).Length
        $downloadTime = $stopwatch.Elapsed.TotalSeconds
        $speed = $fileSize / $downloadTime

        $result = [PSCustomObject]@{{
            Method = 'BITS'
            FileSize = $fileSize
            FileSizeFormatted = Format-FileSize -Size $fileSize
            DownloadTime = $downloadTime
            DownloadTimeFormatted = '{0:N2} seconds' -f $downloadTime
            Speed = $speed
            SpeedFormatted = Format-Speed -BytesPerSecond $speed
        }}

        Write-Host ('  Downloaded ' + $result.FileSizeFormatted + ' in ' + $result.DownloadTimeFormatted + ' at ' + $result.SpeedFormatted) -ForegroundColor Green
        $results += $result
    }}
    catch {{
        $stopwatch.Stop()
        Write-Host ('  Error: ' + $_.Exception.Message) -ForegroundColor Red
    }}
}}

# Display comparison
Write-Host ''
Write-Host 'Comparison of Download Methods:' -ForegroundColor Green
Write-Host '=============================='

$results | Sort-Object -Property DownloadTime | Format-Table -Property Method, FileSizeFormatted, DownloadTimeFormatted, SpeedFormatted

# Identify the fastest method
$fastestMethod = $results | Sort-Object -Property DownloadTime | Select-Object -First 1
if ($fastestMethod) {{
    Write-Host ''
    Write-Host ('Fastest Method: ' + $fastestMethod.Method + ' with download time of ' + $fastestMethod.DownloadTimeFormatted) -ForegroundColor Cyan

    # Calculate improvement over Invoke-WebRequest
    $invokeWebRequestResult = $results | Where-Object {{ $_.Method -eq 'Invoke-WebRequest' }}
    if ($invokeWebRequestResult) {{
        $improvement = (1 - ($fastestMethod.DownloadTime / $invokeWebRequestResult.DownloadTime)) * 100
        Write-Host ('Improvement over Invoke-WebRequest: ' + $improvement.ToString('N2') + '%') -ForegroundColor Cyan
    }}
}}

# Clean up
Write-Host ''
Write-Host 'Cleaning up temporary files...' -ForegroundColor Gray
Remove-Item -Path (Join-Path $tempDir '*.zip') -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host 'Benchmark completed.' -ForegroundColor Green
"'''

    # Return the command as plain text
    return Response(
        content=command,
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache"
        }
    )

@router.get("/simple_benchmark.ps1")
async def download_simple_benchmark_script():
    """
    Download the simple_benchmark.ps1 script.

    This is a simplified script for benchmarking download methods.
    """
    logger.info("Downloading simple_benchmark.ps1 script")

    # Path to the simple_benchmark.ps1 script
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "simple_benchmark.ps1")

    # Try multiple possible locations for the file
    possible_paths = [
        script_path,
        "/simple_benchmark.ps1",
        "/home/axel/accountdb/simple_benchmark.ps1",
        os.path.abspath("simple_benchmark.ps1")
    ]

    logger.info(f"Looking for simple_benchmark.ps1 script at multiple locations")
    for path in possible_paths:
        logger.info(f"Checking path: {path}, exists: {os.path.exists(path)}")
        if os.path.exists(path):
            script_path = path
            break

    logger.info(f"Using simple_benchmark.ps1 script at: {script_path}")

    # Check if the file exists
    if not os.path.exists(script_path):
        logger.error(f"simple_benchmark.ps1 script not found: {script_path}")
        raise HTTPException(status_code=404, detail="simple_benchmark.ps1 script not found")

    # Return the script as a file response
    return FileResponse(
        path=script_path,
        filename="simple_benchmark.ps1",
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "attachment; filename=simple_benchmark.ps1"
        }
    )

@router.get("/direct_install_command")
async def get_direct_install_command(request: Request, vm_id: str = "YOUR_VM_ID", api_key: str = "YOUR_API_KEY"):
    """
    Get a simple PowerShell command to directly install the Windows VM Agent.

    This endpoint returns a PowerShell command that can be copied and pasted into a PowerShell window.

    Args:
        vm_id: The VM identifier.
        api_key: The API key for authentication.
    """
    logger.info("Getting direct install command")

    # Generate a simple command that directly installs the Windows VM Agent
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    download_url = f"{server_url}/downloads/windows_vm_agent.zip"

    # Create a very simple command with explicit steps
    command = f'''powershell -ExecutionPolicy Bypass -Command "
# Set TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Define variables
$downloadUrl = '{download_url}'
$vmId = '{vm_id}'
$apiKey = '{api_key}'
$serverUrl = '{server_url}'
$installDir = 'C:\\CsBotAgent'
$agentZip = Join-Path $env:TEMP 'windows_vm_agent.zip'
$extractDir = Join-Path $env:TEMP 'vm_agent_extract'

Write-Host 'Downloading Windows VM Agent...'
try {{
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $agentZip)
    Write-Host 'Download completed successfully.'
}} catch {{
    Write-Host 'Error downloading file: $_'
    exit 1
}}

Write-Host 'Extracting files...'
try {{
    # Create installation directory
    if (-not (Test-Path $installDir)) {{
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }}

    # Clean up extract directory if it exists
    if (Test-Path $extractDir) {{
        Remove-Item -Path $extractDir -Recurse -Force
    }}
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    # Extract the ZIP file
    Expand-Archive -Path $agentZip -DestinationPath $extractDir -Force

    # Find the agent directory
    $dirInfo = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if ($dirInfo) {{
        $agentDir = Join-Path $dirInfo.FullName 'windows_vm_agent'
        if (Test-Path $agentDir) {{
            Write-Host 'Found windows_vm_agent directory in ZIP.'
            Copy-Item -Path $agentDir\\* -Destination $installDir -Recurse -Force
        }} else {{
            Write-Host 'Using repository root directory.'
            Copy-Item -Path $dirInfo.FullName\\* -Destination $installDir -Recurse -Force
        }}
    }} else {{
        Write-Host 'Using extract directory root.'
        Copy-Item -Path $extractDir\\* -Destination $installDir -Recurse -Force
    }}

    Write-Host 'Files extracted successfully.'
}} catch {{
    Write-Host 'Error extracting files: $_'
    exit 1
}}

Write-Host 'Creating configuration file...'
try {{
    $configContent = @'
General:
  VMIdentifier: \"{0}\"
  APIKey: \"{1}\"
  ManagerBaseURL: \"{2}\"
  ScriptsPath: \"{3}\\ActionScripts\"
  LoggingEnabled: true
  LogLevel: \"INFO\"
'@ -f $vmId, $apiKey, $serverUrl, $installDir

    Set-Content -Path (Join-Path $installDir 'config.yaml') -Value $configContent
    Write-Host 'Configuration file created successfully.'
}} catch {{
    Write-Host 'Error creating configuration file: $_'
    exit 1
}}

Write-Host 'Windows VM Agent installed successfully!' -ForegroundColor Green
Write-Host 'Installation Directory: ' -NoNewline
Write-Host $installDir -ForegroundColor Cyan
"'''

    # Return the command as plain text
    return Response(
        content=command,
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache"
        }
    )

@router.get("/direct_install.ps1")
async def download_direct_install_script():
    """
    Download the direct_install.ps1 script.

    This is a simplified script for installing the Windows VM Agent.
    """
    logger.info("Downloading direct_install.ps1 script")

    # Path to the direct_install.ps1 script
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "direct_install.ps1")

    # Try multiple possible locations for the file
    possible_paths = [
        script_path,
        "/direct_install.ps1",
        "/home/axel/accountdb/direct_install.ps1",
        os.path.abspath("direct_install.ps1")
    ]

    logger.info(f"Looking for direct_install.ps1 script at multiple locations")
    for path in possible_paths:
        logger.info(f"Checking path: {path}, exists: {os.path.exists(path)}")
        if os.path.exists(path):
            script_path = path
            break

    logger.info(f"Using direct_install.ps1 script at: {script_path}")

    # Check if the file exists
    if not os.path.exists(script_path):
        logger.error(f"direct_install.ps1 script not found: {script_path}")
        raise HTTPException(status_code=404, detail="direct_install.ps1 script not found")

    # Return the script as a file response
    return FileResponse(
        path=script_path,
        filename="direct_install.ps1",
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "attachment; filename=direct_install.ps1"
        }
    )
