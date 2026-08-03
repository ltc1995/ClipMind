@echo off
chcp 65001 >nul
echo ========================================
echo   ClipMind - Building executable...
echo ========================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
.venv\Scripts\python.exe -m pip install pyinstaller -q

echo.
echo Building ClipMind.exe...
.venv\Scripts\python.exe build.py

if exist "dist\ClipMind.exe" (
    echo.
    echo SUCCESS: dist\ClipMind.exe
    echo.
    echo You can now run ClipMind.exe directly!
) else (
    echo.
    echo Build failed. Check errors above.
)

pause
