@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =====================================================================
REM  Chromatic Scale Generator PLUS! (Remastered) - Build Script
REM =====================================================================
REM  Creates a dedicated virtual environment, installs dependencies and
REM  bundles the application with PyInstaller. Supports building in the
REM  default onedir layout or an optional onefile executable.
REM =====================================================================

chcp 65001 >nul
pushd "%~dp0" >nul

set "EXIT_CODE=0"
set "PYTHONUTF8=1"
set "APP=CSGPR.py"
set "ICON=icon.ico"
set "ASSETS_DIR=assets"
set "PACKAGE_DIR=csgpr"
set "I18N_DIR=i18n_pkg"
set "VENV_DIR=.venv_build"
set "BUILD_MODE=onedir"
set "SKIP_DEPS=0"

REM ---------------------------------------------------------------------
REM  Parse optional command-line arguments
REM ---------------------------------------------------------------------
:parse_args
if "%~1"=="" goto after_args
if /I "%~1"=="--help" goto show_help
if /I "%~1"=="-h" goto show_help
if /I "%~1"=="--onefile" (
  set "BUILD_MODE=onefile"
  shift
  goto parse_args
)
if /I "%~1"=="--onedir" (
  set "BUILD_MODE=onedir"
  shift
  goto parse_args
)
if /I "%~1"=="--skip-deps" (
  set "SKIP_DEPS=1"
  shift
  goto parse_args
)
echo [WARN] Ignoring unknown argument: %~1
shift
goto parse_args

:show_help
echo Usage: build_CSGPR.bat [--onefile ^| --onedir] [--skip-deps]
echo.
echo   --onefile    Build a single executable (slower to start, larger initial download).
echo   --onedir     Build the default folder-based layout. This is the default.
echo   --skip-deps  Reuse the existing virtual environment without reinstalling packages.
echo   --help       Show this message and exit.
echo.
echo Examples:
echo   build_CSGPR.bat
echo   build_CSGPR.bat --onefile
echo   build_CSGPR.bat --skip-deps
set "EXIT_CODE=0"
goto finalize

:after_args
echo ================================================================
echo  Chromatic Scale Generator PLUS! - Build
if /I "%BUILD_MODE%"=="onefile" (
  echo  Mode: single-file executable
) else (
  echo  Mode: onedir (recommended^)
)
echo ================================================================

REM ---------------------------------------------------------------------
REM  Verify project structure
REM ---------------------------------------------------------------------
if not exist "%APP%" (
  echo [ERROR] Cannot find launcher script: %APP%
  set "EXIT_CODE=1"
  goto finalize
)
if not exist "%PACKAGE_DIR%" (
  echo [ERROR] Cannot find package directory: %PACKAGE_DIR%
  set "EXIT_CODE=1"
  goto finalize
)
if not exist "%I18N_DIR%" (
  echo [ERROR] Cannot find translations package: %I18N_DIR%
  set "EXIT_CODE=1"
  goto finalize
)
if not exist "%ICON%" (
  echo [WARN] Icon not found: %ICON%. Using default PyInstaller icon.
)
if not exist "%ASSETS_DIR%" (
  echo [WARN] Assets directory not found: %ASSETS_DIR%. Splash screens may be missing.
)

REM ---------------------------------------------------------------------
REM  Locate Python 3.10+
REM ---------------------------------------------------------------------
set "PYTHON_CMD="
for %%P in (py python python3) do (
  if not defined PYTHON_CMD (
    %%P --version >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON_CMD=%%P"
    )
  )
)
if not defined PYTHON_CMD (
  echo [ERROR] Python 3.10+ is required but was not found in PATH.
  set "EXIT_CODE=1"
  goto finalize
)

for /f "tokens=1" %%a in ('%PYTHON_CMD% -c "import sys; print(sys.version_info.major)"') do (
  set "PY_MAJOR=%%a"
)
for /f "tokens=1" %%a in ('%PYTHON_CMD% -c "import sys; print(sys.version_info.minor)"') do (
  set "PY_MINOR=%%a"
)
if not defined PY_MAJOR (
  echo [ERROR] Unable to detect Python version from %PYTHON_CMD%.
  set "EXIT_CODE=1"
  goto finalize
)
if !PY_MAJOR! LSS 3 (
  echo [ERROR] Python 3.10+ is required. Found version !PY_MAJOR!.!PY_MINOR!.
  set "EXIT_CODE=1"
  goto finalize
)
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 10 (
  echo [ERROR] Python 3.10+ is required. Found version !PY_MAJOR!.!PY_MINOR!.
  set "EXIT_CODE=1"
  goto finalize
)

echo [1/6] Using Python interpreter: %PYTHON_CMD% (version !PY_MAJOR!.!PY_MINOR!)

REM ---------------------------------------------------------------------
REM  Create virtual environment if needed
REM ---------------------------------------------------------------------
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [2/6] Creating virtual environment in %VENV_DIR% ...
  "%PYTHON_CMD%" -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    set "EXIT_CODE=1"
    goto finalize
  )
) else (
  echo [2/6] Using existing virtual environment: %VENV_DIR%
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Unable to activate virtual environment.
  set "EXIT_CODE=1"
  goto finalize
)

REM ---------------------------------------------------------------------
REM  Install or reuse dependencies
REM ---------------------------------------------------------------------
if "%SKIP_DEPS%"=="1" (
  echo [3/6] Skipping dependency installation (per --skip-deps).
) else (
  echo [3/6] Upgrading pip, setuptools, and wheel...
  python -m pip install --upgrade pip setuptools wheel
  if errorlevel 1 (
    echo [ERROR] Failed to upgrade packaging tools.
    set "EXIT_CODE=1"
    goto finalize
  )

  if exist requirements.txt (
    echo [4/6] Installing project requirements...
    python -m pip install --upgrade -r requirements.txt
  ) else (
    echo [4/6] Installing baseline dependencies (requirements.txt missing)...
    python -m pip install --upgrade PySide6 praat-parselmouth numpy pyinstaller
  )
  if errorlevel 1 (
    echo [ERROR] Failed to install project requirements.
    set "EXIT_CODE=1"
    goto finalize
  )
)

REM ---------------------------------------------------------------------
REM  Clean previous build artifacts
REM ---------------------------------------------------------------------
if exist build (
  echo [5/6] Removing previous build directory...
  rmdir /s /q build
)
if exist dist\CSGPR (
  rmdir /s /q dist\CSGPR
)
if exist dist\CSGPR.exe (
  del /q dist\CSGPR.exe
)
if exist CSGPR.spec (
  del /q CSGPR.spec
)

REM Determine PyInstaller mode switch and output hint
if /I "%BUILD_MODE%"=="onefile" (
  set "MODE_SWITCH=--onefile"
  set "OUTPUT_HINT=dist\CSGPR.exe"
) else (
  set "MODE_SWITCH=--onedir"
  set "OUTPUT_HINT=dist\CSGPR"
)

echo [6/6] Running PyInstaller...
pyinstaller --noconfirm --clean %MODE_SWITCH% --windowed --noupx --name CSGPR ^
  --collect-all numpy ^
  --collect-all parselmouth ^
  --collect-all i18n_pkg ^
  --collect-all csgpr ^
  --add-data "%ICON%;." ^
  --add-data "%ASSETS_DIR%;assets" ^
  --icon="%ICON%" "%APP%"
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed.
  set "EXIT_CODE=1"
  goto finalize
)

echo.
echo Build complete!
echo Output:
if /I "%BUILD_MODE%"=="onefile" (
  if exist "%OUTPUT_HINT%" (
    for %%F in ("%OUTPUT_HINT%") do echo   %%~fF
  ) else (
    echo   %OUTPUT_HINT%
  )
) else (
  if exist "%OUTPUT_HINT%" (
    for %%D in ("%OUTPUT_HINT%") do echo   %%~fD
  ) else (
    echo   %OUTPUT_HINT%
  )
)
echo Launch via:
if /I "%BUILD_MODE%"=="onefile" (
  echo   %OUTPUT_HINT%
) else (
  echo   %OUTPUT_HINT%\CSGPR.exe
)
echo.
echo Use "run_with_logs.bat" if you need to capture console output while testing the unfrozen app.

goto finalize

:finalize
popd >nul
endlocal & exit /b %EXIT_CODE%
