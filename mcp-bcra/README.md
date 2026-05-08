# 🏦 MCP BCRA — Banco Central de la República Argentina

Servidor MCP (Model Context Protocol) para la API pública del [Banco Central de la República Argentina](https://www.bcra.gob.ar/).

## ¿Qué problema resuelve?

El BCRA publica datos macroeconómicos clave a través de su API pública: tipo de cambio, reservas internacionales, base monetaria, tasas de interés, inflación, y más. Sin embargo, consultar estos datos requiere conocer los endpoints, IDs de variables y formatos de fecha.

Este MCP convierte esa API en algo que un agente de IA puede consultar en lenguaje natural:

> **Usuario:** "¿Cuánto están las reservas internacionales del BCRA hoy?"
>
> **Claude (usando este MCP):** "Las reservas internacionales brutas del BCRA al 23/05/2026 son USD 32.450 millones."

> **Usuario:** "Mostrame la evolución del tipo de cambio oficial en los últimos 3 meses"
>
> **Claude:** "Acá tenés la serie del tipo de cambio minorista (variable 4) desde febrero a mayo 2026: [datos]"

## Para quién es útil

- **Economistas y analistas** que necesitan datos del BCRA sin programar
- **Periodistas** que cubren economía y necesitan datos actualizados
- **Desarrolladores** que quieren integrar datos del BCRA en sus aplicaciones
- **Estudiantes** de economía que necesitan series temporales para análisis

## Herramientas disponibles

| Tool | Descripción |
|------|-------------|
| `list_variables()` | Lista todas las variables disponibles (reservas, tipo cambio, tasas, etc.) |
| `get_variable_data(variable_id, desde, hasta)` | Serie temporal de una variable entre dos fechas |
| `get_latest_values(variable_ids)` | Último valor de una o más variables |
| `search_variables(query)` | Busca variables por nombre/descripción |

## Cómo funciona

```
┌────────────────────┐      stdio      ┌────────────────────┐
│ main.py (MCP)      │ ◀────────────▶  │ Claude / Kiro /... │
│                    │                 │                    │
│ - Cache variables  │ ── HTTPS ──▶   │ api.bcra.gob.ar    │
│ - Búsqueda local   │                 │ /estadisticas/v2.0 │
│ - Fetch en vivo    │                 │                    │
└────────────────────┘                 └────────────────────┘
```

**Características:**
- Cache en memoria de la lista de variables (se carga una vez)
- Búsqueda insensible a tildes y mayúsculas
- Sin autenticación requerida (API 100% pública)
- Manejo graceful de errores HTTP y SSL

## Instalación

Requiere **Python 3.10+** (Windows, macOS o Linux).

```bash
cd mcp-bcra
pip install mcp httpx
```

> **Windows:** Usá `pip` en lugar de `pip3`, y `python` en lugar de `python3` en todos los comandos.

O usando el pyproject.toml:

```bash
pip install -e .
```

## Conectar a un cliente de IA

### Kiro

Editar `.kiro/settings/mcp.json`:

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

> **Tip:** Ejecutá `setup.sh` (macOS/Linux) o `setup.bat` (Windows) desde la raíz del proyecto para generar este archivo automáticamente con las rutas correctas.

### Claude Desktop

Editar `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

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

### Claude Code

```bash
claude mcp add bcra -- python3 /RUTA/ABSOLUTA/A/mcp-bcra/main.py
```

### VS Code

Editar `~/.config/Code/User/mcp.json`:

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

## Ejemplos de preguntas

- "¿Cuánto están las reservas internacionales del BCRA?"
- "¿Cuál es el tipo de cambio oficial hoy?"
- "Mostrame la evolución de la tasa de política monetaria en el último mes"
- "¿Cuál es la inflación mensual según el BCRA?"
- "Buscá variables relacionadas con base monetaria"
- "Dame el tipo de cambio mayorista de los últimos 6 meses"
- "¿Cuáles son las principales variables que publica el BCRA?"

## Configuración

Variables de entorno opcionales:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BCRA_BASE_URL` | `https://api.bcra.gob.ar` | Base URL de la API |
| `MCP_BCRA_LOGLEVEL` | `INFO` | Nivel de logging (DEBUG, INFO, WARNING, ERROR) |

## Prueba rápida sin cliente MCP

```bash
python3 -c "
import asyncio, sys
sys.path.insert(0, 'mcp-bcra')
from main import tool_list_variables
result = asyncio.run(tool_list_variables())
print(result[:500])
"
```

## Variables comunes del BCRA

| ID | Variable | Unidad |
|----|----------|--------|
| 1 | Reservas Internacionales | Millones de USD |
| 4 | Tipo de Cambio Minorista (promedio vendedor) | ARS por USD |
| 5 | Tipo de Cambio Mayorista de referencia | ARS por USD |
| 7 | Tasa de interés BADLAR bancos privados | % TNA |
| 15 | Base Monetaria | Millones de ARS |

*El BCRA publica ~1220 variables. Usar `list_variables` o `search_variables` para obtener la lista completa.*

## API del BCRA

- **Base URL**: `https://api.bcra.gob.ar`
- **Autenticación**: No requiere
- **Versión**: v4.0 (la v2.0 fue deprecada)
- **Endpoints usados**:
  - `GET /estadisticas/v4.0/Monetarias` — Lista de variables (con paginación)
  - `GET /estadisticas/v4.0/Monetarias/{id}?desde=...&hasta=...` — Serie temporal
- **Formato de fechas**: YYYY-MM-DD
- **Paginación**: `limit` (máx 3000) y `offset`

## Licencia

MIT — ver [LICENSE](LICENSE).

## Contribuir

1. Fork del repositorio
2. Crear branch (`git checkout -b feature/mi-mejora`)
3. Commit (`git commit -m 'Agrega mi mejora'`)
4. Push (`git push origin feature/mi-mejora`)
5. Abrir Pull Request

---

Hecho para el **Jornada de IA para Gobierno** — Dirección Nacional de Datos e Información Pública de Argentina, mayo 2026.
