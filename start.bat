@echo off
echo ========================================================
echo   Starting AI Invoice Intelligence System
echo ========================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found in PATH!
        echo Please restart your terminal or install Python from python.org.
        pause
        exit /b 1
    )
)

echo Starting FastAPI Backend on port 8000...
start "AI Invoice Backend (FastAPI)" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 >nul

echo Starting Streamlit Frontend on port 8501...
start "AI Invoice Frontend (Streamlit)" cmd /k "streamlit run frontend/app.py"

echo.
echo ========================================================
echo  Applications started!
echo  Backend API:  http://localhost:8000/docs
echo  Dashboard:    http://localhost:8501
echo ========================================================
