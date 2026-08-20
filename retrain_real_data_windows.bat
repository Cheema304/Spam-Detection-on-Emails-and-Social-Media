@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run run_windows.bat once first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python scripts\train.py
if errorlevel 1 goto :fail
python scripts\run_tests.py
if errorlevel 1 goto :fail
echo.
echo RETRAINING AND TESTS COMPLETED SUCCESSFULLY.
pause
exit /b 0
:fail
echo.
echo Retraining or tests failed. Review the error above.
pause
exit /b 1
