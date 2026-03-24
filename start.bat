@echo off
title Sptube - Free Music
echo ============================================
echo   Sptube - Free Music
echo ============================================
echo.

:: Check if venv exists
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python 3.10+ is installed and in PATH.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo [1/3] Virtual environment found.
)

:: Activate venv
echo [2/3] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

:: Install/upgrade pip and requirements
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed.

echo [3/3] Starting Sptube server...
echo.
echo   App running at: http://localhost:8002
echo.

:: Start the server in the background
start /b uvicorn main:app --reload --host 0.0.0.0 --port 8002

:: Wait for server to be ready
timeout /t 2 /nobreak >nul

:: Launch Chrome with autoplay policy disabled (the magic flag!)
echo   Launching Sptube player (autoplay enabled)...
set "SPTUBE_URL=http://localhost:8002"
set "CHROME_FLAGS=--autoplay-policy=no-user-gesture-required --app=%SPTUBE_URL% --new-window"

:: Try Chrome locations
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" %CHROME_FLAGS%
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" %CHROME_FLAGS%
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" %CHROME_FLAGS%
) else (
    :: Try Edge as fallback (also Chromium-based, same flag works)
    echo   Chrome not found, trying Edge...
    start "" msedge %CHROME_FLAGS%
)

echo.
echo   Press Ctrl+C to stop the server.
echo.

:: Keep the server running in foreground
wait


:: By JP