@echo off
echo Iniciando Transparencia Downloader...
echo.

echo [1/2] Iniciando backend Python...
start "Backend" cmd /k "cd /d %~dp0backend && python api.py"

timeout /t 5 /nobreak > nul

echo [2/2] Iniciando frontend React...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ✅ Aplicación iniciada:
echo    - Backend: http://localhost:8000
echo    - Frontend: http://localhost:3000
echo.
pause