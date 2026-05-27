@echo off
REM ============================================================
REM Ask My PDF Bot - First-Time Setup & Launch Script
REM Run this ONCE to install everything and start the project
REM ============================================================

title Ask My PDF Bot - Setup

echo.
echo  =============================================
echo   ASK MY PDF BOT - First Time Setup
echo  =============================================
echo.

REM ── Step 1: Check Python ─────────────────────────────────────
echo [Step 1/6] Checking Python installation...
python --version > nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.11 from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo Python found.
echo.

REM ── Step 2: Create virtual environment ───────────────────────
echo [Step 2/6] Creating virtual environment...
IF EXIST "venv" (
    echo Virtual environment already exists. Skipping creation.
) ELSE (
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)
echo.

REM ── Step 3: Activate venv ────────────────────────────────────
echo [Step 3/6] Activating virtual environment...
call venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

REM ── Step 4: Upgrade pip ──────────────────────────────────────
echo [Step 4/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo pip upgraded.
echo.

REM ── Step 5: Install dependencies ─────────────────────────────
echo [Step 5/6] Installing dependencies (this may take 5-10 minutes)...
echo Installing PyTorch CPU version first...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
echo Installing remaining dependencies...
pip install -r requirements.txt --quiet
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Dependency installation failed!
    echo Try running manually: pip install -r requirements.txt
    pause
    exit /b 1
)
echo All dependencies installed.
echo.

REM ── Step 6: Setup .env file ───────────────────────────────────
echo [Step 6/6] Setting up environment file...
IF NOT EXIST ".env" (
    copy .env.example .env
    echo .env file created from template.
    echo.
    echo =============================================
    echo  ACTION REQUIRED: Add your Gemini API Key
    echo =============================================
    echo.
    echo  1. Go to: https://aistudio.google.com/app/apikey
    echo  2. Create a free API key
    echo  3. Open .env file and replace:
    echo     GEMINI_API_KEY=your_gemini_api_key_here
    echo     with your actual key
    echo.
    echo Opening .env file in Notepad...
    timeout /t 2 /nobreak > nul
    notepad .env
) ELSE (
    echo .env file already exists. Skipping.
)
echo.

REM ── Create directories ────────────────────────────────────────
if not exist uploads mkdir uploads
if not exist data mkdir data
if not exist logs mkdir logs
echo Directories created.
echo.

REM ── Generate sample PDFs ──────────────────────────────────────
echo Generating sample PDF files for testing...
python data\create_sample_pdfs.py
echo.

REM ── Done ─────────────────────────────────────────────────────
echo  =============================================
echo   Setup Complete!
echo  =============================================
echo.
echo  To start the project, run:
echo    run.bat
echo.
echo  Or manually:
echo    Terminal 1: python backend\main.py
echo    Terminal 2: streamlit run frontend\app.py
echo.
echo  URLs:
echo    Frontend : http://localhost:8501
echo    Backend  : http://localhost:8000
echo    API Docs : http://localhost:8000/docs
echo.

set /p START_NOW="Start the project now? (y/n): "
IF /I "%START_NOW%"=="y" (
    call run.bat
) ELSE (
    echo Run 'run.bat' whenever you're ready to start.
    pause
)
