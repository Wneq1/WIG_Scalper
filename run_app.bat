@echo off
cd /d "%~dp0"
echo Uruchamianie WIG Scalper...
".venv\Scripts\python.exe" main.py
if %errorlevel% neq 0 (
    echo Wystapil blad podczas uruchamiania.
    pause
)
