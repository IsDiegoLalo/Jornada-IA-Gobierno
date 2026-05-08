# Instalación y Configuración

## Requisitos previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet (para generar el índice y para `query_resource_data`)

## Paso 1: Instalar dependencias

```bash
cd MCP-datos-abiertos-arg
pip install mcp httpx pandas openpyxl
```

O usando el pyproject.toml:

```bash
pip install -e .
```

## Paso 2: Generar el índice

```bash
python build_index.py
```

Esto descarga el catálogo completo de datos.gob.ar (~1,233 datasets) y genera `index.json` (~3 MB). Tarda aproximadamente 5 segundos.

Para desarrollo rápido (solo 100 datasets):

```bash
python build_index.py --limit 100
```

## Paso 3: Verificar que funciona

```bash
python3 -c "
import asyncio, json, sys
sys.path.insert(0, '.')
from main import tool_search_datasets
result = asyncio.run(tool_search_datasets('salud', limit=3))
print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
"
```

Deberías ver resultados de datasets relacionados con salud.

## Paso 4: Configurar en tu cliente de IA

### Kiro

Editar `.kiro/settings/mcp.json` en tu workspace:

```json
{
  "mcpServers": {
    "argentina-datos-abiertos": {
      "command": "python3",
      "args": ["/RUTA/ABSOLUTA/A/MCP-datos-abiertos-arg/main.py"]
    }
  }
}
```

### Claude Desktop

Editar el archivo de configuración:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "argentina-datos-abiertos": {
      "command": "python3",
      "args": ["/RUTA/ABSOLUTA/A/MCP-datos-abiertos-arg/main.py"]
    }
  }
}
```

Reiniciar Claude Desktop después de guardar.

### Claude Code

```bash
claude mcp add argentina-datos-abiertos -- python3 /RUTA/ABSOLUTA/A/MCP-datos-abiertos-arg/main.py
```

### VS Code

Editar `~/.config/Code/User/mcp.json` (Linux) o equivalente:

```json
{
  "servers": {
    "argentina-datos-abiertos": {
      "type": "stdio",
      "command": "python3",
      "args": ["/RUTA/ABSOLUTA/A/MCP-datos-abiertos-arg/main.py"]
    }
  }
}
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATOSARG_BASE` | `https://datos.gob.ar` | URL base del portal CKAN |
| `MCP_ARG_INDEX` | `./index.json` (junto a main.py) | Ruta al archivo de índice |
| `MCP_ARG_LOGLEVEL` | `INFO` | Nivel de logging: DEBUG, INFO, WARNING, ERROR |

Ejemplo con variables de entorno en Kiro:

```json
{
  "mcpServers": {
    "argentina-datos-abiertos": {
      "command": "python3",
      "args": ["/ruta/a/MCP-datos-abiertos-arg/main.py"],
      "env": {
        "MCP_ARG_LOGLEVEL": "DEBUG"
      }
    }
  }
}
```

## Actualizar el índice

El índice es un snapshot estático. Para actualizarlo cuando el portal agregue nuevos datasets:

```bash
# Regenerar completo
python build_index.py

# Solo agregar nuevos (modo incremental)
python build_index.py --offset 1200 --append
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'mcp'` | Ejecutar `pip install mcp httpx pandas openpyxl` |
| `FileNotFoundError: No encontré el índice` | Ejecutar `python build_index.py` primero |
| El MCP no aparece en el cliente | Verificar la ruta absoluta en la configuración y reiniciar el cliente |
| Timeout al generar índice | Verificar conexión a internet; el portal puede estar lento |
| `query_resource_data` falla | El recurso puede estar offline o ser > 20 MB |
