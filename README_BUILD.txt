Chromatic Scale Generator PLUS! (REMASTERED)
===================================================

Quick Build (Windows, PyInstaller)
----------------------------------
1) Open **Command Prompt** (not PowerShell).
2) `cd` into the project folder (this folder).
3) Run:
   build_chromatic_plus.bat

The script will:
- Create `.venv_build` (isolated environment)
- Install pinned deps from requirements.txt
- Build an **onedir** GUI app (friendlier to antivirus)
- Put results in `dist\CSGPR\`

Run/Debug with logs
-------------------
Double-click `run_with_logs.bat` to launch the Python app from the venv and write logs to `run.log`. If something fails, Notepad opens the log.

Single-file EXE (optional)
--------------------------
One-file builds trigger more AV flags. If you still want it:
  pyinstaller --noconfirm --clean --onefile --windowed --noupx --collect-all numpy --collect-all parselmouth --icon="C:\Users\Administrator\Downloads\CSGR\icon.ico" "CSGPR.py"

Notes
-----
- To reduce size, you can remove `--collect-all numpy` or `--collect-all parselmouth` **if** your build starts fine without them.
- If the app doesn't open, try running `run_with_logs.bat` and check `run.log`.
- Make sure the icon exists at the path configured in the BAT script (or update the path).
