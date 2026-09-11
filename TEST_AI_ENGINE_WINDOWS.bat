@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Yatharth virtual environment was not found.
  echo Run START_YATHARTH_AI_WINDOWS.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe scripts\test_engine.py
pause
