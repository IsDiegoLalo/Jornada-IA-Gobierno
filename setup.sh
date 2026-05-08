#!/bin/bash
# Setup rápido para el Jornada de IA para Gobierno
# Ejecutar: ./setup.sh

set -e

echo "🇦🇷 Jornada de IA para Gobierno — Setup"
echo "=========================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Instalalo desde https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ $PYTHON_VERSION"

# Instalar dependencias del MCP
echo ""
echo "📦 Instalando dependencias..."
pip3 install mcp httpx pandas openpyxl --quiet 2>/dev/null || \
pip3 install --break-system-packages mcp httpx pandas openpyxl --quiet 2>/dev/null || \
echo "⚠️  No se pudieron instalar automáticamente. Ejecutá: pip3 install mcp httpx pandas openpyxl"

echo "✅ Dependencias instaladas"

# Verificar que index.json existe
if [ ! -f "mcp-datos-abiertos-arg/index.json" ]; then
    echo ""
    echo "📥 Generando índice de datos.gob.ar (~5 segundos)..."
    python3 mcp-datos-abiertos-arg/build_index.py
else
    echo "✅ index.json ya existe ($(wc -l < mcp-datos-abiertos-arg/index.json | tr -d ' ') líneas)"
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
      "command": "python3",
      "args": ["$MCP_DATOS"],
      "disabled": false,
      "autoApprove": ["search_datasets", "get_dataset_info", "list_dataset_resources", "list_organizations", "index_stats"]
    },
    "bcra": {
      "command": "python3",
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
