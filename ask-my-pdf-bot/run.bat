@echo off
REM ============================================================
REM Ask My PDF Bot - Quick Start Script
REM Starts both Backend (FastAPI) and Frontend (Streamlit)
REM Usage: Double-click or run from VS Code terminal
REM ============================================================

title Ask My PDF Bot

echo.
echo  =============================================
echo   ASK MY PDF BOT - Starting Up
echo  =============================================
echo.

REM Check if virtual environment exists
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   1. python -m venv venv
    echo   2. venv\Scripts\activate
    echo   3. pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
IF NOT EXIST ".env" (
    echo [WARN] .env file not found. Copying from .env.example...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Please edit .env and add your GEMINI_API_KEY
    echo Get a free key at: https://aistudio.google.com/app/apikey
    echo.
    notepad .env
    pause
)

REM Create required directories
echo [2/3] Creating directories...
if not exist uploads mkdir uploads
if not exist data mkdir data
if not exist logs mkdir logs

echo.
echo [3/3] Starting servers...
echo.
echo  Backend  : http://localhost:8000
echo  Frontend : http://localhost:8501
echo  API Docs : http://localhost:8000/docs
echo.
echo  Press Ctrl+C in each window to stop.
echo.

REM Start Backend in new window
echo Starting Backend (FastAPI)...
start "PDF Bot - Backend" cmd /k "call venv\Scripts\activate.bat && python backend\main.py"

REM Wait 4 seconds for backend to initialize
echo Waiting for backend to start...
timeout /t 4 /nobreak > nul

REM Start Frontend in new window
echo Starting Frontend (Streamlit)...
start "PDF Bot - Frontend" cmd /k "call venv\Scripts\activate.bat && streamlit run frontend\app.py --server.port 8501"

echo.
echo  =============================================
echo   Both servers are starting!
echo   The browser will open automatically.
echo  =============================================
echo.

REM Open browser after a short delay
timeout /t 3 /nobreak > nul
start http://localhost:8501

pause
