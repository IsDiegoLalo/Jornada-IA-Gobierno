# Instalación y Configuración — MCP BCRA

## Requisitos previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet (para consultar la API del BCRA)

> **Nota sobre comandos según sistema operativo:**
> - **macOS / Linux:** Usá `python3` y `pip3`
> - **Windows:** Usá `python` y `pip` (o `python -m pip`)
> - **Alternativa:** Ejecutá `setup.sh` (macOS/Linux) o `setup.bat` (Windows) desde la raíz del proyecto para configurar todo automáticamente.

## Paso 1: Instalar dependencias

```bash
cd mcp-bcra
pip install mcp httpx
```

O usando el pyproject.toml:

```bash
pip install -e .
```

**Nota**: A diferencia del MCP de Datos Abiertos, este MCP no requiere `pandas` ni `openpyxl` ya que no procesa archivos CSV/XLSX.

## Paso 2: Verificar que funciona

**macOS / Linux:**
```bash
python3 -c "
import asyncio, sys
sys.path.insert(0, 'mcp-bcra')
from main import tool_list_variables
result = asyncio.run(tool_list_variables())
print(result[:500])
"
```

**Windows (CMD):**
```cmd
python -c "import asyncio, sys; sys.path.insert(0, 'mcp-bcra'); from main import tool_list_variables; result = asyncio.run(tool_list_variables()); print(result[:500])"
```

Deberías ver una lista de variables del BCRA con sus últimos valores.

## Paso 3: Configurar en tu cliente de IA

### Kiro

Editar `.kiro/settings/mcp.json` en tu workspace:

**macOS / Linux:**
```json
{
  "mcpServers": {
    "bcra": {
      "command": "python3",
      "args": ["/RUTA/ABSOLUTA/A/mcp-bcra/main.py"]
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "bcra": {
      "command": "python",
      "args": ["C:/Users/TU_USUARIO/ruta/al/mcp-bcra/main.py"]
    }
  }
}
```

> **Tip:** Usá forward slashes (`/`) en las rutas del JSON incluso en Windows.

### Claude Desktop

Editar el archivo de configuración:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bcra": {
      "command": "python3",
      "args": ["/RUTA/ABSOLUTA/A/mcp-bcra/main.py"]
    }
  }
}
```

Reiniciar Claude Desktop después de guardar.

### Claude Code

```bash
claude mcp add bcra -- python3 /RUTA/ABSOLUTA/A/mcp-bcra/main.py
```

### VS Code

Editar `~/.config/Code/User/mcp.json` (Linux) o equivalente:

```json
{
  "servers": {
    "bcra": {
      "type": "stdio",
      "command": "python3",
      "args": ["/RUTA/ABSOLUTA/A/mcp-bcra/main.py"]
    }
  }
}
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BCRA_BASE_URL` | `https://api.bcra.gob.ar` | URL base de la API del BCRA |
| `MCP_BCRA_LOGLEVEL` | `INFO` | Nivel de logging: DEBUG, INFO, WARNING, ERROR |

Ejemplo con variables de entorno en Kiro:

```json
{
  "mcpServers": {
    "bcra": {
      "command": "python3",
      "args": ["/ruta/a/mcp-bcra/main.py"],
      "env": {
        "MCP_BCRA_LOGLEVEL": "DEBUG"
      }
    }
  }
}
```

## Usar ambos MCPs juntos

Podés configurar el MCP BCRA junto con el MCP de Datos Abiertos:

```json
{
  "mcpServers": {
    "argentina-datos-abiertos": {
      "command": "python3",
      "args": ["/ruta/a/mcp-datos-abiertos-arg/main.py"]
    },
    "bcra": {
      "command": "python3",
      "args": ["/ruta/a/mcp-bcra/main.py"]
    }
  }
}
```

Así el agente puede combinar datos del portal de datos abiertos con variables macroeconómicas del BCRA.

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'mcp'` | Ejecutar `pip install mcp httpx` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | El MCP ya usa `verify=False` para manejar esto |
| El MCP no aparece en el cliente | Verificar la ruta absoluta y reiniciar el cliente |
| Timeout al consultar la API | La API del BCRA puede estar lenta; reintentar |
| `HTTPStatusError 404` | Verificar que el ID de variable existe con `list_variables` |
| Datos vacíos en `get_variable_data` | Verificar rango de fechas (formato YYYY-MM-DD) |
