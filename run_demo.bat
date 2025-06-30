@echo off
echo ========================================
echo  DEMO TRANSPARENCIA DOWNLOADER
echo ========================================
echo.

echo [1/2] Iniciando backend simplificado...
cd /d "%~dp0backend"
start "Backend Demo" cmd /k "python api_simple.py"

timeout /t 3 /nobreak > nul

echo [2/2] Iniciando frontend React...
cd /d "%~dp0frontend"
start "Frontend React" cmd /k "npm start"

echo.
echo ✅ Demo iniciado:
echo    - Backend: http://localhost:8000
echo    - Frontend: http://localhost:3000
echo.
echo Nota: Esta es una versión demo que simula la funcionalidad
echo Para la versión completa, instala todas las dependencias
echo.
pause