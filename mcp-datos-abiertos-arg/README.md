# 🇦🇷 MCP Datos Abiertos Argentina

Servidor MCP (Model Context Protocol) para el Portal Nacional de Datos Abiertos de Argentina — [datos.gob.ar](https://datos.gob.ar).

## ¿Qué problema resuelve?

El Estado argentino publica ~1,233 datasets abiertos en datos.gob.ar (ministerios, secretarías, organismos descentralizados). El portal existe, pero para un ciudadano o funcionario encontrar un dato específico es difícil: la búsqueda del portal es limitada, los datasets viven detrás de slugs largos, y para cruzar datos hay que descargar CSVs manualmente.

Este MCP convierte ese catálogo en algo que un agente de IA (Claude Desktop, Kiro, Cursor, VS Code, Claude Code) puede consultar en lenguaje natural:

> **Usuario:** "¿Qué datasets hay sobre transporte público en Argentina?"
>
> **Claude (usando este MCP):** "Encontré 5 datasets: SUBE - Cantidad de transacciones (Min. Transporte) en CSV, Estadísticas de transporte ferroviario (CNRT) en CSV, Peajes - Tránsito en autopistas (Vialidad Nacional) en CSV... ¿Te traigo una preview del primero?"

Inspirado en [datos-abiertos-peru-mcp-demo](https://github.com/deltamacuro/datos-abiertos-peru-mcp-demo) y construido para el **Jornada de IA para Gobierno** organizado por la Dirección Nacional de Datos e Información Pública de Argentina.

## Para quién es útil

- **Ciudadanos / periodistas de datos** que quieren encontrar información pública sin conocer la nomenclatura de CKAN.
- **Funcionarios públicos** que necesitan cruzar datos de varias entidades sin ser programadores.
- **Equipos de transformación digital** que exploran cómo los agentes IA pueden consumir sus portales.
- **Desarrolladores** que quieren un ejemplo real y funcional de un MCP en español sobre datos públicos.

## Herramientas disponibles

| Tool | Descripción |
|------|-------------|
| `search_datasets(query, limit)` | Búsqueda full-text sobre el índice local (título, descripción, tags, entidad). Ranking por relevancia, ignora tildes |
| `get_dataset_info(dataset_id)` | Metadata completa de un dataset |
| `list_dataset_resources(dataset_id)` | Archivos (CSV/XLSX/PDF/API) con URL de descarga |
| `query_resource_data(resource_url, rows)` | Preview de filas de un CSV/XLSX (hasta 20 MB) |
| `list_organizations()` | Lista las entidades publicadoras presentes en el índice |
| `index_stats()` | Info del índice: cuándo se generó, cuántos datasets, fuente |

## Cómo funciona

El portal datos.gob.ar usa CKAN y expone una API estándar. Para lograr búsqueda rápida y relevante, este MCP usa un patrón de **índice local pre-generado**:

```
┌────────────────────┐                 ┌──────────────────────┐
│ build_index.py     │ ── HTTPS ──▶   │ datos.gob.ar         │
│ (offline, 1 vez)   │                 │  /api/3/action/*     │
└────────┬───────────┘                 └──────────────────────┘
         │
         ▼
    index.json  (~3 MB, ~1,233 datasets)
         │
         ▼
┌────────────────────┐      stdio      ┌────────────────────┐
│ main.py (MCP)      │ ◀────────────▶  │ Claude / Kiro /... │
│ búsqueda local     │                 │                    │
│ + fetch de datos   │ ── HTTPS ──▶   │ datos.gob.ar       │
│   en vivo          │ (solo para     │                    │
└────────────────────┘  resources)    └────────────────────┘
```

**Ventajas:**
- Búsqueda instantánea (sin latencia del portal en cada query)
- Full-text sobre título + notes + tags + entidad, con scoring por campo
- Resiliente: si el portal está lento o caído, la búsqueda sigue funcionando
- Publicable como dataset: `index.json` es un snapshot citeable del catálogo

## Instalación

Requiere **Python 3.10+**.

```bash
cd MCP-datos-abiertos-arg
pip install mcp httpx pandas openpyxl
python build_index.py        # ~5 seg, genera index.json (~3 MB)
```

Para desarrollo rápido: `python build_index.py --limit 100` solo trae 100 datasets.

## Conectar a un cliente de IA

### Kiro

Editar `.kiro/settings/mcp.json`:

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

Editar `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

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

### Claude Code

```bash
claude mcp add argentina-datos-abiertos -- python3 /RUTA/ABSOLUTA/A/MCP-datos-abiertos-arg/main.py
```

### VS Code

Editar `~/.config/Code/User/mcp.json`:

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

## Ejemplos de preguntas

- "¿Qué datasets hay sobre educación en Argentina?"
- "Busca datos sobre COVID-19 y dime qué publicó el Ministerio de Salud."
- "Trae el CSV de precios SEPA y hazme un resumen."
- "¿Qué publica el ENACOM sobre telecomunicaciones?"
- "Lista los datos de presupuesto del sector público."
- "Cuántas entidades publican en el portal y cuáles son."
- "¿Hay datos sobre transporte ferroviario?"

El agente decide qué tool llamar, encadena llamadas y sintetiza la respuesta.

## Configuración

Variables de entorno opcionales:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATOSARG_BASE` | `https://datos.gob.ar` | Base URL del portal |
| `MCP_ARG_INDEX` | `./index.json` | Ruta al index.json |
| `MCP_ARG_LOGLEVEL` | `INFO` | Nivel de logging (DEBUG, INFO, WARNING, ERROR) |

## Prueba rápida sin cliente MCP

```bash
python3 -c "
import asyncio, json, sys
sys.path.insert(0, 'MCP-datos-abiertos-arg')
from main import tool_search_datasets
result = asyncio.run(tool_search_datasets('educación', limit=3))
print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
"
```

## Tests

```bash
pip install pytest pytest-asyncio
pytest MCP-datos-abiertos-arg/tests/ -v
```

17 tests que cubren: carga de índice con deduplicación, búsqueda insensible a tildes, semántica AND entre tokens, ranking por campo, validación de URLs seguras, y todas las tools MCP.

## Regenerar el índice

Cuando el portal agregue nuevos datasets:

```bash
python build_index.py                    # regenera completo
python build_index.py --offset 1000 --append  # solo nuevos desde offset 1000
```

## Arquitectura de archivos

```
MCP-datos-abiertos-arg/
├── main.py            # Servidor MCP (stdio), 6 tools
├── build_index.py     # Generador del índice (paginado)
├── index.json         # Snapshot del catálogo (~3 MB, ~1,233 datasets)
├── manifest.json      # Metadata del paquete MCP
├── tests/             # Tests unitarios (pytest)
├── pyproject.toml
├── LICENSE            # MIT
└── README.md
```

El servidor es **read-only**: solo consulta el portal, no modifica nada. Sin API key.

## Roadmap

- [ ] Soporte para la API de Series de Tiempo de Argentina
- [ ] Integración con API Georef para normalización geográfica
- [ ] Tool `validate_dataset(resource_url)` — valida calidad (nulos, duplicados, tipos)
- [ ] Tool `suggest_metadata(resource_url)` — sugiere descripción y tags según contenido
- [ ] Desplegar en producción con Amazon Bedrock AgentCore Gateway
- [ ] Soportar transport HTTP streamable además de stdio

## Licencia

MIT — ver [LICENSE](LICENSE).

## Datos

Los datos del `index.json` provienen del [Portal Nacional de Datos Abiertos de Argentina](https://datos.gob.ar), publicados por entidades del Estado argentino. Los datasets individuales pueden tener licencias específicas indicadas en su metadata (la mayoría usa Creative Commons Attribution 4.0).

Este proyecto no modifica ni redistribuye los datos originales — solo indexa metadata pública para facilitar su descubrimiento.

## Contribuir

1. Fork del repositorio
2. Crear branch (`git checkout -b feature/mi-mejora`)
3. Commit (`git commit -m 'Agrega mi mejora'`)
4. Push (`git push origin feature/mi-mejora`)
5. Abrir Pull Request

---

Hecho para el **Jornada de IA para Gobierno** — Dirección Nacional de Datos e Información Pública de Argentina, mayo 2026.
