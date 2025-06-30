@echo off
echo ========================================
echo  INSTALACION SIMPLIFICADA
echo ========================================
echo.

echo Instalando dependencias minimas para Python 3.13...
cd /d "%~dp0backend"

echo Instalando FastAPI y dependencias basicas...
pip install fastapi uvicorn pydantic requests beautifulsoup4 fuzzywuzzy python-levenshtein

echo.
echo Instalando Selenium...
pip install selenium webdriver-manager

echo.
echo Instalando pandas (version compatible)...
pip install "pandas>=2.2.0" openpyxl

echo.
echo Instalando dependencias opcionales...
pip install PyPDF2 pytesseract Pillow

echo.
echo ========================================
echo  INSTALACION FRONTEND
echo ========================================
echo.
cd /d "%~dp0frontend"
echo Instalando dependencias React...
npm install

echo.
echo ========================================
echo  INICIANDO APLICACION
echo ========================================
echo.

echo [1/2] Iniciando backend...
cd /d "%~dp0backend"
start "Backend" cmd /k "python api.py"

timeout /t 5 /nobreak > nul

echo [2/2] Iniciando frontend...
cd /d "%~dp0frontend"
start "Frontend" cmd /k "npm start"

echo.
echo ✅ Aplicacion iniciada:
echo    - Backend: http://localhost:8000
echo    - Frontend: http://localhost:3000
echo.
pause