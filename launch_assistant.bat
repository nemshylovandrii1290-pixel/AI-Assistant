@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo .venv\Scripts\python.exe not found.
  exit /b 1
)

".venv\Scripts\python.exe" -m ui.app
