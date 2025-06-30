@echo off
echo ========================================
echo  INICIO RAPIDO (sin instalacion)
echo ========================================
echo.

echo Verificando si ya tienes las dependencias...
cd /d "%~dp0backend"

python -c "import fastapi, uvicorn" 2>nul
if %errorlevel% neq 0 (
    echo Instalando FastAPI...
    pip install fastapi uvicorn
)

python -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo Instalando requests...
    pip install requests
)

echo.
echo [1/2] Iniciando backend...
start "Backend" cmd /k "python api.py"

timeout /t 3 /nobreak > nul

echo [2/2] Iniciando frontend...
cd /d "%~dp0frontend"

if not exist node_modules (
    echo Instalando dependencias React...
    npm install
)

start "Frontend" cmd /k "npm start"

echo.
echo ✅ Aplicacion iniciada:
echo    - Backend: http://localhost:8000  
echo    - Frontend: http://localhost:3000
echo.
pause