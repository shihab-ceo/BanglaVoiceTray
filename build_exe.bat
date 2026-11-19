@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
python -m PyInstaller --noconfirm --clean --windowed --onedir --noupx --name BanglaVoiceTray --runtime-hook pyside_dll_path.py --collect-all pystray --collect-all speech_recognition main.py
if errorlevel 1 goto :error
echo.
echo Build complete. EXE: dist\BanglaVoiceTray.exe
pause
exit /b 0
:error
echo.
echo Build failed. Review the error above.
pause
exit /b 1

