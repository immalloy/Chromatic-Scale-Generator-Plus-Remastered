@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM ===============================================================
REM  Chromatic Scale Generator PLUS! (REMASTERED) - Build Script
REM  Output: dist\chromatic_gen_qt_plus_modular_i18n\*.exe
REM ===============================================================

REM Change to the directory of this script
cd /d "%~dp0"

set APP=CSGPR.py
set ICON=C:\Users\Administrator\Downloads\CSGR\icon.ico

if not exist "%APP%" (
  echo [ERROR] Cannot find %APP% in %cd%
  exit /b 1
)

echo [1/5] Creating/using virtual environment: .venv_build
if not exist ".venv_build" (
  py -3 -m venv .venv_build
)

echo [2/5] Activating venv
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
REM Notes:
REM  - onedir is friendlier to antivirus than onefile
REM  - --collect-all ensures native libs for numpy / parselmouth come along
REM  - remove --collect-all if you want a smaller build and it still works
pyinstaller --noconfirm --clean --windowed --noupx ^
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
echo   pyinstaller --noconfirm --clean --onefile --windowed --noupx --collect-all numpy --collect-all parselmouth --icon="%ICON%" "%APP%"
echo.
pause
