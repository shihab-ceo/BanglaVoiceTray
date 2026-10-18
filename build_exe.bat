@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --windowed --onefile --name BanglaVoiceTray --collect-all pystray --collect-all speech_recognition main.py
echo.
echo Build complete. EXE: dist\BanglaVoiceTray.exe
pause
