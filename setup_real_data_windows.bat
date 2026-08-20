@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
python scripts\fetch_real_data.py
if errorlevel 1 goto :fail
python scripts\train.py
if errorlevel 1 goto :fail
python scripts\run_tests.py
if errorlevel 1 goto :fail
echo.
echo REAL-DATA SETUP, TRAINING AND TESTING COMPLETED SUCCESSFULLY.
pause
exit /b 0
:fail
echo.
echo Setup failed. Review the error above, check your internet connection, and try again.
pause
exit /b 1
