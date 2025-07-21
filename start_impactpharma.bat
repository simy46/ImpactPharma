@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "PYTHON=python"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYTHON% -m venv .venv
)

call "%VENV_DIR%\Scripts\activate.bat"

echo Installing dependencies...
pip install -r requirements.txt

echo Running ImpactPharma...
python main.py

pause
