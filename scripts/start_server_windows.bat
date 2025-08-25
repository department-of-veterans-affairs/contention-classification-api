@echo off
REM Windows batch script to start the FastAPI server in the background
REM Equivalent to: nohup poetry run uvicorn python_src.api:app --port 8120 --reload &

echo Starting FastAPI server in the background...
start /B poetry run uvicorn python_src.api:app --port 8120 --reload > server.log 2>&1

echo Server started. Check server.log for output.
echo To stop the server, use: taskkill /F /IM python.exe
