@echo off
setlocal
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto failed
echo Setup complete. Run start_gui.bat for the desktop interface or start.bat for the CLI.
pause
exit /b 0
:failed
echo Setup failed. Install Python 3.10 or newer with Add Python to PATH, and check your internet connection.
pause
exit /b 1
