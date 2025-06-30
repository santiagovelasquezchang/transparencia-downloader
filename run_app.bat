@echo off
echo ========================================
echo  TRANSPARENCIA DOWNLOADER
echo ========================================
echo.

echo [1/2] Iniciando Backend...
cd /d "%~dp0backend"
start "Backend API" cmd /k "python api.py"

timeout /t 3 /nobreak > nul

echo [2/2] Iniciando Frontend...
cd /d "%~dp0frontend"
start "Frontend React" cmd /k "npm start"

echo.
echo ✅ Aplicación iniciada:
echo    - Backend: http://localhost:8000
echo    - Frontend: http://localhost:3000
echo.
pause