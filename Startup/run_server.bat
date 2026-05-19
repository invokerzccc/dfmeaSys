@echo off
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0run_server.ps1"
pause
