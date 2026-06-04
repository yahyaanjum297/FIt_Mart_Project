@echo off
echo ====================================
echo  FitMart Backend Launcher (Windows)
echo ====================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from python.org
    pause
    exit /b
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start server
echo.
echo Starting FitMart backend on http://localhost:8000
echo Swagger docs at http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.
python run.py
pause
