@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   Yatharth Music AI - ACE-Step Starter
echo ================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo Git was not found. Install Git for Windows first.
  pause
  exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
  echo uv was not found. Installing uv with pip...
  python -m pip install --user uv
  if errorlevel 1 (
    echo Could not install uv.
    pause
    exit /b 1
  )
)

if not exist "ACE-Step-1.5" (
  echo [1/3] Downloading official ACE-Step repository...
  git clone --depth 1 https://github.com/ace-step/ACE-Step-1.5.git ACE-Step-1.5
  if errorlevel 1 (
    echo ACE-Step download failed.
    pause
    exit /b 1
  )
)

cd /d "%~dp0ACE-Step-1.5"

echo [2/3] Installing ACE-Step environment...
uv sync
if errorlevel 1 (
  echo ACE-Step dependency installation failed.
  pause
  exit /b 1
)

echo [3/3] Starting ACE-Step API on port 8001...
echo Keep this window open while Yatharth Music AI is generating music.
echo.
uv run acestep-api --host 127.0.0.1 --port 8001

pause
