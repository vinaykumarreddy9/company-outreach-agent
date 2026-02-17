@echo off
SETLOCAL EnableDelayedExpansion

:: --- CONFIGURATION ---
SET "APP_NAME=GTM Intelligence ^& Outreach System"
SET "VENV_ACTIVATE=venv\Scripts\activate.bat"
SET "BACKEND_PORT=8000"
SET "FRONTEND_PORT=3000"

TITLE %APP_NAME% - Master Bootstrapper
COLOR 0A

echo ======================================================================
echo    "%APP_NAME%"
echo    PHASE 2: AUTONOMOUS ENGINE BOOTSTRAPPER
echo ======================================================================
echo.

:: 1. Verify Environment
echo [SYSTEM] Checking prerequisites...
if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run: python -m venv venv
    pause
    exit /b
)

if not exist ".env" (
    echo [WARNING] .env file not found. Ensure your API keys are configured.
)

:: 2. Choose Execution Mode
echo EXECUTION MODES:
echo  [1] UNIFIED ENGINE (Recommended)
echo      - Runs Backend + 3 Workers inside a SINGLE process.
echo      - Mimics Render Free Tier environment.
echo      - Low RAM usage (~80MB total).
echo.
echo  [2] CLUSTER MODE (Advanced)
echo      - Launches 5 separate windows (Frontend, Backend, 3 Workers).
echo      - Best for deep debugging of specific services.
echo      - High RAM usage (~300MB total).
echo.

set /p mode="Select Execution Mode [1 or 2]: "

if "%mode%"=="2" (
    goto :CLUSTER_MODE
) else (
    goto :UNIFIED_MODE
)

:UNIFIED_MODE
echo.
echo [MODE] Initializing UNIFIED ENGINE...
echo.
echo [1/2] Launching React Frontend (Port %FRONTEND_PORT%)...
start "FRONTEND - %APP_NAME%" cmd /k "cd frontend && npm start"

echo [2/2] Launching Backend + Workers (Bundle Mode)...
:: We set BUNDLE_WORKERS=true here to trigger the lifespan tasks in main.py
start "UNIFIED ENGINE - %APP_NAME%" cmd /k "call %VENV_ACTIVATE% && set BUNDLE_WORKERS=true&& uvicorn backend.main:app --reload --port %BACKEND_PORT%"
goto :COMPLETE

:CLUSTER_MODE
echo.
echo [MODE] Initializing CLUSTER MODE...
echo.
echo [1/5] Launching FastAPI Backend...
start "BACKEND - %APP_NAME%" cmd /k "call %VENV_ACTIVATE% && uvicorn backend.main:app --reload --port %BACKEND_PORT%"

echo [2/5] Launching React Frontend...
start "FRONTEND - %APP_NAME%" cmd /k "cd frontend && npm start"

echo [3/5] Starting IMAP Ingestion Worker...
start "WORKER: IMAP Ingestion" cmd /k "call %VENV_ACTIVATE% && python -m backend.background_workers.email_ingestion"

echo [4/5] Starting Orchestrator Worker...
start "WORKER: Orchestrator" cmd /k "call %VENV_ACTIVATE% && python -m backend.background_workers.orchestrator_worker"

echo [5/5] Starting Timer Engine Worker...
start "WORKER: Timer Engine" cmd /k "call %VENV_ACTIVATE% && python -m backend.background_workers.timer_engine"
goto :COMPLETE

:COMPLETE
echo.
echo ======================================================================
echo    ALL SYSTEMS LIVE
echo ======================================================================
echo.
echo URLS:
echo  - Frontend: http://localhost:%FRONTEND_PORT%
echo  - API Docs: http://localhost:%BACKEND_PORT%/docs
echo.
echo Execution complete. Monitoring processes...
echo.
pause
