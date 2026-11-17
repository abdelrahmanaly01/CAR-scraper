@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
 echo Run setup.bat first.
 pause
 exit /b 1
)
start "CAR Property Finder" ".venv\Scripts\pythonw.exe" -m src.car_gui
