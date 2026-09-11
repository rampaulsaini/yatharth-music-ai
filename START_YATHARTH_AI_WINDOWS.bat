@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ========================================================
echo       Yatharth Music AI - Windows One Click Start
echo ========================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.11+ first.
  pause
  exit /b 1
)

where git >nul 2>&1
if errorlevel 1 (
  echo Git was not found. Install Git for Windows first.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/5] Creating Yatharth virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Could not create the Python virtual environment.
    pause
    exit /b 1
  )
)

echo [2/5] Installing Yatharth dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Yatharth dependency installation failed.
  pause
  exit /b 1
)

if not exist ".env" (
  copy /y ".env.example" ".env" >nul
)

set "DEMO_MODE=false"
set "MUSIC_ENGINE_URL=http://127.0.0.1:8001"
set "PYTHONUNBUFFERED=1"

echo [3/5] Starting ACE-Step in a separate window...
start "Yatharth - ACE-Step" cmd /k "call "%~dp0start_acestep_windows.bat""

echo [4/5] Waiting for ACE-Step API at http://127.0.0.1:8001/health ...
set /a attempts=0
:wait_engine
set /a attempts+=1
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:8001/health; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto engine_ready
if !attempts! GEQ 90 (
  echo.
  echo ACE-Step did not become ready within 3 minutes.
  echo Yatharth can still be started in DEMO mode if needed.
  echo.
  goto start_yatharth
)
timeout /t 2 /nobreak >nul
goto wait_engine

:engine_ready
echo ACE-Step is READY.

a:start_yatharth

echo [5/5] Starting Yatharth Music AI on http://127.0.0.1:8000 ...
echo.
echo Open the app in your browser at:
echo http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
