@echo off
echo =======================================
echo JARVIS System Initialization...
echo =======================================

echo.
echo [1/3] Setting up Backend Dependencies...
cd "%~dp0backend"
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo [2/3] Starting Backend Server...
start "JARVIS Backend" cmd /k "title JARVIS Backend && venv\Scripts\activate && python main.py"

echo.
echo [3/3] Starting Frontend Server...
cd "%~dp0frontend"
start "JARVIS Frontend" cmd /k "title JARVIS Frontend && npm run dev"

echo.
echo =======================================
echo All services are booting up!
echo You can now close this window.
echo =======================================
pause
