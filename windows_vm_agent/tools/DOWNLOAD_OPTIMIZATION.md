# Windows VM Agent Download Optimization

This document describes the optimizations made to improve the download performance of the Windows VM Agent.

## Problem

The Windows VM Agent client file download was very slow, taking around 10 minutes to complete. This was due to inefficient download methods and lack of optimization on both the server and client sides. Additionally, there was an issue with the PowerShell command being too long, causing the "filename or extension is too long" error.

## Optimizations Implemented

### Server-side Optimizations

1. **Pre-generated ZIP file**:
   - Instead of creating the ZIP file on-demand for each request, we now pre-generate it and cache it.
   - The ZIP file is only regenerated when needed (after a configurable TTL).

2. **Added caching headers**:
   - Added proper caching headers to allow client-side caching.
   - Added ETag support for conditional requests.

3. **Download Progress Tracking**:
   - Implemented a download progress tracking system.
   - Added endpoints to check download progress and statistics.

4. **Simplified Installation Process**:
   - Created a separate installation script that can be downloaded and executed.
   - Avoided encoding large PowerShell scripts in command line arguments.

### Client-side Optimizations

1. **BITS (Background Intelligent Transfer Service)**:
   - Implemented BITS for downloading files, which is optimized for large file transfers.
   - BITS provides automatic throttling, resumable downloads, and better performance.
   - Falls back to WebClient if BITS is not available.

2. **System.Net.WebClient Fallback**:
   - If BITS is not available, we use System.Net.WebClient which is still faster than Invoke-WebRequest.
   - Added progress reporting to give users feedback during the download.

3. **Progress Reporting**:
   - Added progress reporting for all download methods.
   - Shows download speed and estimated time remaining.

## How to Test the Optimizations

We've included benchmarking tools to measure the download performance. You can use them to compare the performance of different download methods.

### Installation Options

We now provide multiple ways to install the Windows VM Agent:

1. **Direct Installation Command**:
   - Visit `http://your-server/downloads/direct_install_command?vm_id=YOUR_VM_ID&api_key=YOUR_API_KEY` in your browser
   - Copy the PowerShell command
   - Paste it into a PowerShell window and run it

2. **Using the Install Script**:
   - Download the install script: `http://your-server/downloads/install_agent.ps1`
   - Run it with parameters:
     ```powershell
     .\install_agent.ps1 -DownloadUrl "http://your-server/downloads/windows_vm_agent.zip" -VMId "YOUR_VM_ID" -APIKey "YOUR_API_KEY" -ServerURL "http://your-server"
     ```

### Benchmarking Options

#### Using the Simple Benchmark Command

The easiest way to run the benchmarks is to use the benchmark command endpoint:

1. Visit `http://your-server/downloads/benchmark_command` in your browser
2. Copy the PowerShell command
3. Paste it into a PowerShell window and run it

This will download and run the benchmark scripts automatically.

#### Manual Benchmarking

You can also run the benchmarks manually:

```powershell
# Download the benchmark scripts
Invoke-WebRequest -Uri "http://your-server/downloads/simple_benchmark.ps1" -OutFile "%TEMP%\simple_benchmark.ps1"
Invoke-WebRequest -Uri "http://your-server/downloads/run_benchmarks.ps1" -OutFile "%TEMP%\run_benchmarks.ps1"

# Run the benchmarks
& "%TEMP%\run_benchmarks.ps1" -DownloadUrl "http://your-server/downloads/windows_vm_agent.zip"
```

#### Testing Individual Download Methods

You can also test individual download methods:

```powershell
# Download the simple benchmark script
Invoke-WebRequest -Uri "http://your-server/downloads/simple_benchmark.ps1" -OutFile "%TEMP%\simple_benchmark.ps1"

# Test BITS download method
& "%TEMP%\simple_benchmark.ps1" -DownloadUrl "http://your-server/downloads/windows_vm_agent.zip" -Method "BITS"

# Test WebClient download method
& "%TEMP%\simple_benchmark.ps1" -DownloadUrl "http://your-server/downloads/windows_vm_agent.zip" -Method "WebClient"

# Test Invoke-WebRequest download method
& "%TEMP%\simple_benchmark.ps1" -DownloadUrl "http://your-server/downloads/windows_vm_agent.zip" -Method "InvokeWebRequest"
```

### Expected Results

The benchmark tool will compare the performance of:
- Invoke-WebRequest (original method)
- System.Net.WebClient (faster alternative)
- BITS (fastest method with resume capability)

You should see a significant improvement in download speed with BITS compared to the original Invoke-WebRequest method.

## Download Progress API

You can track the progress of downloads using the new API endpoints:

### Get Download Progress

```
GET /downloads/download-progress/{download_id}
```

This endpoint returns the progress of a specific download, including:
- Percentage complete
- Download speed
- Estimated time remaining

### Get Download Statistics

```
GET /downloads/download-stats
```

This endpoint returns statistics for all completed downloads, including:
- File size
- Download time
- Average download speed

## Recommendations for Further Optimization

1. **Content Delivery Network (CDN)**:
   - For production environments, consider using a CDN to serve the agent files.
   - This would distribute the files to edge servers closer to the clients, reducing download times.

2. **Compression Optimization**:
   - Consider using more efficient compression algorithms for the ZIP file.
   - Experiment with different compression levels to find the optimal balance between file size and compression time.

3. **Parallel Downloads**:
   - For very large files, consider implementing parallel downloads to further improve performance.
   - This would involve splitting the file into chunks and downloading them in parallel.

4. **Delta Updates**:
   - Implement delta updates to only download the changes between versions.
   - This would significantly reduce the download size for updates.

## Conclusion

The implemented optimizations should significantly reduce the download time for the Windows VM agent from the reported 10 minutes to a much more reasonable duration, likely just a few seconds to a minute depending on the connection speed.

The combination of server-side caching and client-side BITS implementation provides the best possible download experience for users.
