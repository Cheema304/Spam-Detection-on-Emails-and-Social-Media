@echo off
setlocal
title SpamShield AI - ICT942
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer and select "Add Python to PATH".
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
python -c "import sklearn, matplotlib, numpy, joblib" >nul 2>nul
if errorlevel 1 (
  echo Installing project dependencies...
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and Python version.
    pause
    exit /b 1
  )
)
python run.py
pause
