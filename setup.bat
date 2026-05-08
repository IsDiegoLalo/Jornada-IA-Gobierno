@echo off
REM Setup rapido para el Jornada de IA para Gobierno (Windows)
REM Ejecutar: setup.bat

echo.
echo === Jornada de IA para Gobierno - Setup (Windows) ===
echo.

REM Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python no encontrado.
    echo Instalalo desde https://python.org
    echo IMPORTANTE: Durante la instalacion, marca la casilla "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION%

REM Verificar que sea Python 3.10+
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Se requiere Python 3.10 o superior.
    echo Tu version actual: %PYTHON_VERSION%
    echo Descarga la ultima version desde https://python.org
    pause
    exit /b 1
)

echo.
echo [INFO] Instalando dependencias...
python -m pip install mcp httpx pandas openpyxl --quiet 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARN] Hubo un problema instalando dependencias.
    echo Ejecuta manualmente: python -m pip install mcp httpx pandas openpyxl
)
echo [OK] Dependencias instaladas

REM Verificar que index.json existe
if not exist "mcp-datos-abiertos-arg\index.json" (
    echo.
    echo [INFO] Generando indice de datos.gob.ar (~5 segundos^)...
    python mcp-datos-abiertos-arg\build_index.py
) else (
    echo [OK] index.json ya existe
)

REM Obtener ruta absoluta del workspace
set "WORKSPACE_DIR=%~dp0"
REM Quitar trailing backslash
if "%WORKSPACE_DIR:~-1%"=="\" set "WORKSPACE_DIR=%WORKSPACE_DIR:~0,-1%"

REM Convertir backslashes a forward slashes para JSON
set "WORKSPACE_FWD=%WORKSPACE_DIR:\=/%"

set "MCP_DATOS=%WORKSPACE_FWD%/mcp-datos-abiertos-arg/main.py"
set "MCP_BCRA=%WORKSPACE_FWD%/mcp-bcra/main.py"

REM Crear directorio .kiro\settings si no existe
if not exist ".kiro\settings" mkdir ".kiro\settings"

REM Generar mcp.json con rutas absolutas
(
echo {
echo   "mcpServers": {
echo     "argentina-datos-abiertos": {
echo       "command": "python",
echo       "args": ["%MCP_DATOS%"],
echo       "disabled": false,
echo       "autoApprove": ["search_datasets", "get_dataset_info", "list_dataset_resources", "list_organizations", "index_stats"]
echo     },
echo     "bcra": {
echo       "command": "python",
echo       "args": ["%MCP_BCRA%"],
echo       "disabled": false,
echo       "autoApprove": ["list_variables", "get_variable_data", "get_latest_values", "search_variables"]
echo     }
echo   }
echo }
) > .kiro\settings\mcp.json

echo [OK] MCPs configurados en .kiro\settings\mcp.json
echo     - argentina-datos-abiertos (1,233 datasets de datos.gob.ar^)
echo     - bcra (1,220 variables economicas del Banco Central^)

echo.
echo === Listo! Los MCP Servers estan configurados. ===
echo.
echo Proximos pasos:
echo   1. Abri este folder en Kiro
echo   2. Los MCPs se conectan automaticamente
echo   3. Proba preguntar:
echo      - "Que datasets hay sobre educacion?"
echo      - "Cuanto estan las reservas del BCRA?"
echo.
pause
