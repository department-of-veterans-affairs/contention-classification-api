# Windows PowerShell script to start the FastAPI server in the background
# Equivalent to: nohup poetry run uvicorn python_src.api:app --port 8120 --reload &

Write-Host "Starting FastAPI server in the background..." -ForegroundColor Green

# Start the process in the background and redirect output to a log file
$process = Start-Process -FilePath "poetry" -ArgumentList "run", "uvicorn", "python_src.api:app", "--port", "8120", "--reload" -NoNewWindow -PassThru -RedirectStandardOutput "server.log" -RedirectStandardError "server_error.log"

Write-Host "Server started with Process ID: $($process.Id)" -ForegroundColor Yellow
Write-Host "Output logged to: server.log" -ForegroundColor Cyan
Write-Host "Errors logged to: server_error.log" -ForegroundColor Cyan
Write-Host "To stop the server, run: Stop-Process -Id $($process.Id)" -ForegroundColor Red

# Optional: Save the process ID to a file for later reference
$process.Id | Out-File -FilePath "server.pid" -Encoding ASCII
Write-Host "Process ID saved to: server.pid" -ForegroundColor Cyan
