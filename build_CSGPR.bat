@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM ===============================================================
REM  Chromatic Scale Generator PLUS! (REMASTERED) - Build Script
REM  Entry: CSGPR.py
REM  Output: dist\CSGPR\CSGPR.exe
REM ===============================================================

cd /d "%~dp0"

set PYTHONUTF8=1
set APP=CSGPR.py
set ICON=icon.ico

if not exist "%APP%" (
  echo [ERROR] Cannot find %APP% in %cd%
  exit /b 1
)
if not exist "%ICON%" (
  echo [WARN] Icon not found: "%ICON%". The build will continue without a custom icon.
)

echo [1/5] Creating/using virtual environment: .venv_build
if not exist ".venv_build" (
  py -3 -m venv .venv_build || python -m venv .venv_build
)

echo [2/5] Activating virtual environment
call ".venv_build\Scripts\activate.bat"

echo [2.1] Upgrading pip/setuptools/wheel
python -m pip install --upgrade pip setuptools wheel

echo [3/5] Installing dependencies...
if exist requirements.txt (
  python -m pip install -r requirements.txt
) else (
  python -m pip install PySide6==6.10.0 praat-parselmouth==0.4.6 numpy==2.3.3 pyinstaller==6.16.0
)

echo [4/5] Building (onedir, windowed, no UPX)...
pyinstaller --noconfirm --clean --windowed --noupx ^
  --name CSGPR ^
  --collect-all numpy ^
  --collect-all parselmouth ^
  --icon="%ICON%" "%APP%"

if errorlevel 1 (
  echo [ERROR] Build failed.
  exit /b 1
)

echo [5/5] Build complete!
echo Output folder:
echo   dist\CSGPR
echo Launch:
echo   dist\CSGPR\CSGPR.exe

echo.
echo [Optional] Build single-file EXE (may trigger more antivirus flags):
echo   pyinstaller --noconfirm --clean --onefile --windowed --noupx --name CSGPR --collect-all numpy --collect-all parselmouth --icon="%ICON%" "%APP%"
echo.
pause
