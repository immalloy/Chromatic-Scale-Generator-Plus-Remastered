@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM ===============================================================
REM  Chromatic Scale Generator PLUS! (REMASTERED) - Build Script
REM  Entry: CSGPR.py (thin launcher for the csgpr package)
REM  Output: dist\CSGPR\CSGPR.exe
REM ===============================================================

cd /d "%~dp0"

set "PYTHONUTF8=1"
set "APP=CSGPR.py"
set "ICON=icon.ico"

set "LOG_DIR=logs"
if not exist "%LOG_DIR%" (
  mkdir "%LOG_DIR%"
)

set "TIMESTAMP="
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format \"yyyyMMdd_HHmmss\"" 2^>NUL') do set "TIMESTAMP=%%i"
if not defined TIMESTAMP (
  for /f "tokens=1-3 delims=/-. " %%a in ("%date%") do set "DATE_PART=%%c%%a%%b"
  for /f "tokens=1-3 delims=:., " %%a in ("%time%") do set "TIME_PART=%%a%%b%%c"
  set "TIME_PART=%TIME_PART: =0%"
  set "TIMESTAMP=%DATE_PART%_%TIME_PART%"
)

set "LOG_FILE=%LOG_DIR%\build_%TIMESTAMP%.log"

call :log "==============================================================="
call :log " Chromatic Scale Generator PLUS! (REMASTERED) - Build Script"
call :log " Logging to: %LOG_FILE%"
call :log "==============================================================="

call :log "App entry: %APP%"
call :log "Icon path: %ICON%"
call :log "Working directory: %cd%"

if not exist "%APP%" (
  call :log "[ERROR] Cannot find %APP% in %cd%"
  goto :fail
)
if not exist "csgpr" (
  call :log "[ERROR] Cannot find application package folder: csgpr"
  goto :fail
)
if not exist "%ICON%" (
  call :log "[WARN] Icon not found: %ICON%. The build will continue without a custom icon."
)

call :log "[1/5] Creating/using virtual environment: .venv_build"
if not exist ".venv_build" (
  call :log "Creating virtual environment with py -3..."
  py -3 -m venv .venv_build >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    set "ERR=%ERRORLEVEL%"
    call :log "[WARN] py -3 failed with exit code !ERR!. Falling back to python -m venv..."
    python -m venv .venv_build >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
      set "ERR=%ERRORLEVEL%"
      call :log "[ERROR] Failed to create virtual environment (exit code !ERR!)."
      goto :fail
    )
  )
) else (
  call :log "Virtual environment already exists; reusing."
)
call :log "Virtual environment ready."

call :log "[2/5] Activating virtual environment"
call ".venv_build\Scripts\activate.bat" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  set "ERR=%ERRORLEVEL%"
  call :log "[ERROR] Failed to activate virtual environment (exit code !ERR!)."
  goto :fail
)

for /f "usebackq tokens=*" %%i in (`python --version 2^>^&1`) do set "PYVER=%%i"
call :log "Using interpreter: %PYVER%"

call :log "[2.1] Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  set "ERR=%ERRORLEVEL%"
  call :log "[ERROR] Failed to upgrade packaging tools (exit code !ERR!)."
  goto :fail
)

call :log "[3/5] Installing dependencies..."
if exist "requirements.txt" (
  python -m pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
) else (
  python -m pip install PySide6==6.10.0 praat-parselmouth==0.4.6 numpy==2.3.3 pyinstaller==6.16.0 >> "%LOG_FILE%" 2>&1
)
if errorlevel 1 (
  set "ERR=%ERRORLEVEL%"
  call :log "[ERROR] Dependency installation failed (exit code !ERR!)."
  goto :fail
)

call :log "[4/5] Building (onedir, windowed, no UPX)..."
set "PYI_ARGS=--noconfirm --clean --windowed --noupx --name CSGPR --collect-all numpy --collect-all parselmouth --collect-all i18n_pkg --collect-all csgpr"
set "OPTIONAL_ASSET_FLAG="
if exist "assets" (
  set "PYI_ARGS=!PYI_ARGS! --add-data \"assets;assets\""
  set "OPTIONAL_ASSET_FLAG= --add-data \"assets;assets\""
  call :log "[INFO] Bundling assets directory."
) else (
  call :log "[INFO] Optional assets directory not found; continuing without it."
)
set "PYI_ARGS=!PYI_ARGS! --add-data \"icon.ico;.\" --icon=\"%ICON%\" \"%APP%\""
pyinstaller !PYI_ARGS! >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  set "ERR=%ERRORLEVEL%"
  call :log "[ERROR] Build failed (exit code !ERR!)."
  goto :fail
)

call :log "[5/5] Build complete!"
call :log "Output folder:"
call :log "  dist\CSGPR"
call :log "Launch:"
call :log "  dist\CSGPR\CSGPR.exe"
call :log "Build log saved to: %LOG_FILE%"
call :log ""
call :log "[Optional] Build single-file EXE (may trigger more antivirus flags):"
call :log "  pyinstaller --noconfirm --clean --onefile --windowed --noupx --name CSGPR --collect-all numpy --collect-all parselmouth --collect-all i18n_pkg --collect-all csgpr%OPTIONAL_ASSET_FLAG% --add-data \"icon.ico;.\" --icon=\"%ICON%\" \"%APP%\""

echo.
pause
exit /b 0

:fail
call :log "See %LOG_FILE% for detailed output."
echo.
pause
exit /b 1

:log
setlocal ENABLEDELAYEDEXPANSION
set "MSG=%~1"
if not defined MSG set "MSG="
echo !MSG!
>> "%LOG_FILE%" echo(!DATE! !TIME! ^| !MSG!
endlocal
exit /b 0
