@echo off
cd /d "%~dp0.."
echo Starting DFMEA dev server...
uvicorn app:app --reload --host 0.0.0.0 --port 8000
