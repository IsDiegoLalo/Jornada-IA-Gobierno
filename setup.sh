#!/bin/bash
# Setup rápido para el Jornada de IA para Gobierno
# Compatible con macOS y Linux
# Para Windows usar: setup.bat
# Ejecutar: ./setup.sh

set -e

echo "🇦🇷 Jornada de IA para Gobierno — Setup"
echo "=========================="
echo ""

# Detectar el comando de Python disponible
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Verificar que sea Python 3
    PY_MAJOR=$(python -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
    if [ "$PY_MAJOR" = "3" ]; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3 no encontrado. Instalalo desde https://python.org"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "✅ $PYTHON_VERSION (comando: $PYTHON_CMD)"

# Verificar versión mínima (3.10+)
PY_OK=$($PYTHON_CMD -c "import sys; print(1 if sys.version_info >= (3, 10) else 0)" 2>/dev/null || echo "0")
if [ "$PY_OK" != "1" ]; then
    echo "❌ Se requiere Python 3.10 o superior. Tu versión: $PYTHON_VERSION"
    echo "   Descargá la última versión desde https://python.org"
    exit 1
fi

# Detectar pip
PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    PIP_CMD="$PYTHON_CMD -m pip"
fi

# Instalar dependencias del MCP
echo ""
echo "📦 Instalando dependencias..."
$PIP_CMD install mcp httpx pandas openpyxl --quiet 2>/dev/null || \
$PIP_CMD install --break-system-packages mcp httpx pandas openpyxl --quiet 2>/dev/null || \
echo "⚠️  No se pudieron instalar automáticamente. Ejecutá: $PIP_CMD install mcp httpx pandas openpyxl"

echo "✅ Dependencias instaladas"

# Verificar que index.json existe
if [ ! -f "mcp-datos-abiertos-arg/index.json" ]; then
    echo ""
    echo "📥 Generando índice de datos.gob.ar (~5 segundos)..."
    $PYTHON_CMD mcp-datos-abiertos-arg/build_index.py
else
    echo "✅ index.json ya existe"
fi

# Generar .kiro/settings/mcp.json con ruta absoluta correcta
WORKSPACE_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_DATOS="$WORKSPACE_DIR/mcp-datos-abiertos-arg/main.py"
MCP_BCRA="$WORKSPACE_DIR/mcp-bcra/main.py"

mkdir -p .kiro/settings

cat > .kiro/settings/mcp.json << EOF
{
  "mcpServers": {
    "argentina-datos-abiertos": {
      "command": "$PYTHON_CMD",
      "args": ["$MCP_DATOS"],
      "disabled": false,
      "autoApprove": ["search_datasets", "get_dataset_info", "list_dataset_resources", "list_organizations", "index_stats"]
    },
    "bcra": {
      "command": "$PYTHON_CMD",
      "args": ["$MCP_BCRA"],
      "disabled": false,
      "autoApprove": ["list_variables", "get_variable_data", "get_latest_values", "search_variables"]
    }
  }
}
EOF

echo "✅ MCPs configurados en .kiro/settings/mcp.json"
echo "   - argentina-datos-abiertos (1,233 datasets de datos.gob.ar)"
echo "   - bcra (1,220 variables económicas del Banco Central)"

echo ""
echo "🎉 ¡Listo! Los MCP Servers están configurados."
echo ""
echo "Próximos pasos:"
echo "  1. Abrí este folder en Kiro"
echo "  2. Los MCPs se conectan automáticamente"
echo "  3. Probá preguntar:"
echo "     - '¿Qué datasets hay sobre educación?'"
echo "     - '¿Cuánto están las reservas del BCRA?'"
echo ""
