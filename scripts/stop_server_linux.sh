#!/bin/bash
# Linux/Unix shell script to stop the FastAPI server
# This script will stop the server started by start_server_linux.sh

echo "Stopping FastAPI server..."

# Try to read the process ID from the saved file
if [ -f "server.pid" ]; then
    PID=$(cat server.pid)

    # Check if the process is still running
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "Server with Process ID $PID stopped successfully."
        rm -f server.pid
    else
        echo "Process with ID $PID is not running."
        rm -f server.pid
    fi
else
    echo "No server.pid file found. Attempting to stop all uvicorn processes..."

    # Alternative: Stop all uvicorn processes
    PIDS=$(pgrep -f uvicorn)

    if [ ! -z "$PIDS" ]; then
        echo "Found uvicorn processes: $PIDS"
        pkill -f uvicorn
        echo "Stopped uvicorn processes."
    else
        echo "No uvicorn processes found running."
    fi
fi
