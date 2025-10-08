@echo off
setlocal
cd /d "%~dp0"

if exist ".venv_build\Scripts\activate.bat" (
  call ".venv_build\Scripts\activate.bat"
)

REM Force UTF-8 mode to avoid console encoding issues
set PYTHONUTF8=1

REM Show logs if the app fails to start in GUI mode
python CSGPR.py 1>run.log 2>&1
if errorlevel 1 (
  echo The app exited with an error. See run.log for details.
  notepad run.log
) else (
  echo App exited normally.
)
pause
