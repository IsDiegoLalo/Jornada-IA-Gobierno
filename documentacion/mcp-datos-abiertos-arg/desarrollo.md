# Guía de Desarrollo

## Setup del entorno

```bash
# Clonar el repositorio
git clone https://github.com/Eduvilascoder/Jornada-IA-Gobierno.git
cd Jornada-IA-Gobierno/mcp-datos-abiertos-arg

# Crear entorno virtual (recomendado)
python3 -m venv .venv        # macOS/Linux
# python -m venv .venv       # Windows

source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows (CMD)
# .venv\Scripts\Activate.ps1 # Windows (PowerShell)

# Instalar dependencias + dev
pip install -e ".[dev]"

# Generar índice (necesario para que el MCP funcione)
python build_index.py
```

## Estructura del proyecto

```
MCP-datos-abiertos-arg/
├── main.py            # Servidor MCP — punto de entrada principal
├── build_index.py     # Script para generar/actualizar index.json
├── index.json         # Índice local del catálogo (generado, no commitear)
├── manifest.json      # Metadata del paquete MCP
├── pyproject.toml     # Configuración del proyecto Python
├── LICENSE            # MIT
├── README.md          # Documentación principal
└── tests/
    ├── __init__.py
    └── test_index.py  # Tests unitarios
```

## Correr tests

```bash
pytest tests/ -v
```

Los tests no requieren conexión a internet — usan fixtures con datos de ejemplo.

## Linting y formato

```bash
# Instalar ruff
pip install ruff

# Verificar estilo
ruff check .

# Auto-fix
ruff check --fix .

# Formatear
ruff format .
```

## Agregar una nueva tool

1. **Definir la función** en `main.py`:

```python
async def tool_mi_nueva_tool(param1: str, param2: int = 10) -> str:
    """Descripción de lo que hace."""
    # Implementación
    return json.dumps(resultado, ensure_ascii=False, indent=2)
```

2. **Registrar en `list_tools()`**:

```python
Tool(
    name="mi_nueva_tool",
    description="Descripción para el agente de IA",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "default": 10},
        },
        "required": ["param1"],
    },
),
```

3. **Agregar al dispatcher en `call_tool()`**:

```python
elif name == "mi_nueva_tool":
    out = await tool_mi_nueva_tool(arguments["param1"], arguments.get("param2", 10))
```

4. **Escribir tests** en `tests/test_index.py`

5. **Actualizar documentación** en `documentacion/api-reference.md`

## Regenerar el índice

```bash
# Completo (~5 segundos)
python build_index.py

# Solo primeros 100 (desarrollo rápido)
python build_index.py --limit 100

# Incremental (agregar nuevos desde offset)
python build_index.py --offset 1200 --append
```

## Debugging

### Ver logs del MCP

Los logs van a stderr (stdout es para el protocolo MCP):

```bash
# Ejecutar con debug
MCP_ARG_LOGLEVEL=DEBUG python main.py 2>mcp.log
```

### Probar tools individualmente

```python
import asyncio, sys
sys.path.insert(0, '.')
from main import tool_search_datasets, tool_get_dataset_info

# Buscar
result = asyncio.run(tool_search_datasets("educación", limit=5))
print(result)

# Info de un dataset
result = asyncio.run(tool_get_dataset_info("mi-dataset-id"))
print(result)
```

### Inspeccionar el índice

```python
import json
with open("index.json") as f:
    data = json.load(f)

print(f"Total datasets: {data['total_indexed']}")
print(f"Generado: {data['generated_at']}")
print(f"Primer dataset: {data['datasets'][0]['title']}")
```

## Convenciones de código

- **PEP 8** estricto (enforced por ruff)
- **Type hints** en todas las funciones públicas
- **Docstrings** en español para funciones principales
- **Variables** en inglés, comentarios en español
- **Funciones** máximo 30 líneas
- **Constantes** en UPPER_CASE

## Git workflow

1. Crear branch desde `main`: `git checkout -b feature/mi-feature`
2. Hacer commits atómicos con mensajes descriptivos
3. Correr tests antes de push: `pytest tests/ -v`
4. Abrir PR contra `main`

## Consideraciones de seguridad

- **NUNCA** logear datos sensibles del usuario
- **SIEMPRE** validar URLs antes de hacer fetch (usar `_is_safe_url()`)
- **NO** commitear `index.json` si contiene datos sensibles (no debería, pero verificar)
- **NO** agregar dependencias sin verificar su reputación
- Mantener el servidor **read-only** — nunca escribir al portal
