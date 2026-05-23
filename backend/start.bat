@echo off
setlocal

set DOMAIN=%1
if "%DOMAIN%"=="" set DOMAIN=stretch-wildfire-blouse.ngrok-free.dev
set PORT=%2
if "%PORT%"=="" set PORT=8000

echo Starting backend on port %PORT% ...
start "Backend" cmd /c "uv run uvicorn app.main:app --reload --port %PORT%"

timeout /t 2 /nobreak >nul

echo Starting ngrok tunnel to %DOMAIN% ...
start "Ngrok" cmd /c "ngrok http --url=%DOMAIN% %PORT%"

echo Backend: http://localhost:%PORT%
echo Public:  https://%DOMAIN%
echo Press Ctrl+C to stop, or close the two windows.
