@echo off
echo ========================================
echo  TRANSPARENCIA DOWNLOADER - MANUAL
echo ========================================
echo.

echo PASO 1: Instalar dependencias backend
echo.
cd /d "%~dp0backend"
echo Instalando dependencias Python...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias Python
    pause
    exit /b 1
)
echo.

echo PASO 2: Instalar dependencias frontend
echo.
cd /d "%~dp0frontend"
echo Instalando dependencias React...
npm install
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias React
    pause
    exit /b 1
)
echo.

echo PASO 3: Iniciando aplicaciones...
echo.
echo [1/2] Iniciando backend Python...
cd /d "%~dp0backend"
start "Backend Python" cmd /k "python api.py"

timeout /t 5 /nobreak > nul

echo [2/2] Iniciando frontend React...
cd /d "%~dp0frontend"
start "Frontend React" cmd /k "npm start"

echo.
echo ✅ Aplicación iniciada:
echo    - Backend: http://localhost:8000
echo    - Frontend: http://localhost:3000
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul