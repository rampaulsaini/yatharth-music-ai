@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   Yatharth Music AI - Free Local Starter
echo ================================================
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or 3.12 first.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [2/3] Creating Python environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Could not create the virtual environment.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if not exist ".env" (
  echo [3/3] Creating local .env from .env.example...
  copy /Y ".env.example" ".env" >nul
)

findstr /B "DEMO_MODE=" .env >nul 2>&1
if errorlevel 1 echo DEMO_MODE=true>>.env
findstr /B "MUSIC_ENGINE_URL=" .env >nul 2>&1
if errorlevel 1 echo MUSIC_ENGINE_URL=http://127.0.0.1:8001>>.env

echo.
echo Yatharth backend is starting on http://127.0.0.1:8000
 echo.
echo IMPORTANT: This script starts the Yatharth web backend.
echo Start ACE-Step separately when you want real AI generation.
echo Demo mode remains available when ACE-Step is offline.
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
