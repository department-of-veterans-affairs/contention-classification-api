#!/bin/bash
# Linux/Unix shell script to start the FastAPI server in the background
# Equivalent to: nohup poetry run uvicorn python_src.api:app --port 8120 --reload &

echo "Starting FastAPI server in the background..."

# Start the process in the background and redirect output to log files
nohup poetry run uvicorn python_src.api:app --port 8120 --reload > server.log 2>&1 &

# Get the process ID
PID=$!

# Save the process ID to a file for later reference
echo $PID > server.pid

echo "Server started with Process ID: $PID"
echo "Output logged to: server.log"
echo "Process ID saved to: server.pid"
echo "To stop the server, run: ./scripts/stop_server_linux.sh"
echo "Or manually: kill $PID"
