# Stop the FastAPI server on Windows
# This script will stop the server started by start_server_windows.ps1

Write-Host "Stopping FastAPI server..." -ForegroundColor Yellow

# Try to read the process ID from the saved file
if (Test-Path "server.pid") {
    $processId = Get-Content "server.pid" -Raw
    $processId = $processId.Trim()

    try {
        Stop-Process -Id $processId -Force
        Write-Host "Server with Process ID $processId stopped successfully." -ForegroundColor Green
        Remove-Item "server.pid" -Force
    }
    catch {
        Write-Host "Could not stop process with ID $processId. It may have already stopped." -ForegroundColor Red
    }
}
else {
    Write-Host "No server.pid file found. Attempting to stop all uvicorn processes..." -ForegroundColor Yellow

    # Alternative: Stop all uvicorn processes
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*" }

    if ($processes) {
        $processes | Stop-Process -Force
        Write-Host "Stopped $($processes.Count) uvicorn process(es)." -ForegroundColor Green
    }
    else {
        Write-Host "No uvicorn processes found running." -ForegroundColor Yellow
    }
}
