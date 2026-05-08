"""
MCP BCRA — Servidor MCP para la API pública del Banco Central de la República Argentina
https://api.bcra.gob.ar

Expone 4 herramientas:
  - list_variables(): lista todas las variables disponibles del BCRA
  - get_variable_data(variable_id, desde, hasta): serie temporal de una variable
  - get_latest_values(variable_ids): último valor de una o más variables
  - search_variables(query): busca variables por nombre/descripción

La API del BCRA (v4.0) es pública y no requiere autenticación. Provee datos sobre
reservas internacionales, tipo de cambio, base monetaria, tasas de interés,
inflación y otras variables macroeconómicas clave de Argentina.

Transporte: stdio (compatible con Claude Desktop, Kiro, Cursor, VS Code, etc.)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import unicodedata
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Logging al stderr (stdout lo usa el protocolo MCP por stdio — no tocar).
logging.basicConfig(
    level=os.environ.get("MCP_BCRA_LOGLEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] mcp-bcra: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("mcp-bcra")

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
BASE_URL = os.environ.get("BCRA_BASE_URL", "https://api.bcra.gob.ar")
API_PREFIX = f"{BASE_URL}/estadisticas/v4.0"

TIMEOUT = 30.0
MAX_RESULTS_PER_PAGE = 3000  # Máximo permitido por la API

# -----------------------------------------------------------------------------
# Cache en memoria para la lista de variables
# -----------------------------------------------------------------------------
_variables_cache: list[dict[str, Any]] | None = None


# -----------------------------------------------------------------------------
# Normalización para búsqueda
# -----------------------------------------------------------------------------
def _norm(s: str) -> str:
    """Minúsculas + sin tildes para búsqueda insensible."""
    s = s or ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# -----------------------------------------------------------------------------
# Cliente HTTP
# -----------------------------------------------------------------------------
def _get_http_client() -> httpx.AsyncClient:
    """Crea un cliente httpx configurado para la API del BCRA.

    Nota: Se usa verify=False porque la API del BCRA puede presentar
    problemas de certificado SSL en algunos entornos. La API es pública
    y no transmite datos sensibles del usuario.
    """
    return httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        verify=False,  # La API BCRA puede tener issues con certificados SSL
    )


async def _fetch_variables() -> list[dict[str, Any]]:
    """Obtiene la lista de variables monetarias del BCRA (v4.0).

    Cachea el resultado en memoria tras la primera llamada.
    La API v4.0 usa el endpoint /estadisticas/v4.0/Monetarias con paginación.
    """
    global _variables_cache
    if _variables_cache is not None:
        log.debug("Usando cache de variables (%d items)", len(_variables_cache))
        return _variables_cache

    url = f"{API_PREFIX}/Monetarias"
    log.info("Fetching variables desde %s", url)

    all_variables: list[dict[str, Any]] = []
    offset = 0

    async with _get_http_client() as client:
        while True:
            params = {"limit": MAX_RESULTS_PER_PAGE, "offset": offset}
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            all_variables.extend(results)

            # Verificar si hay más páginas
            metadata = data.get("metadata", {}).get("resultset", {})
            total_count = metadata.get("count", 0)

            if len(all_variables) >= total_count or not results:
                break
            offset += len(results)

    _variables_cache = all_variables
    log.info("Variables cargadas y cacheadas: %d items", len(all_variables))
    return all_variables


async def _fetch_variable_data(
    variable_id: int, desde: str, hasta: str
) -> list[dict[str, Any]]:
    """Obtiene datos de una variable entre dos fechas (YYYY-MM-DD).

    La API v4.0 usa /estadisticas/v4.0/Monetarias/{id}?desde=...&hasta=...
    """
    url = f"{API_PREFIX}/Monetarias/{variable_id}"
    params: dict[str, Any] = {
        "desde": desde,
        "hasta": hasta,
        "limit": MAX_RESULTS_PER_PAGE,
    }
    log.info("Fetching datos: variable=%d desde=%s hasta=%s", variable_id, desde, hasta)

    async with _get_http_client() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    # La API v4.0 retorna {"results": [{"idVariable": N, "detalle": [...]}]}
    results = data.get("results", [])
    if results and isinstance(results[0], dict) and "detalle" in results[0]:
        return results[0]["detalle"]
    return results


# -----------------------------------------------------------------------------
# Herramientas MCP
# -----------------------------------------------------------------------------
async def tool_list_variables() -> str:
    """Lista todas las variables disponibles del BCRA."""
    variables = await _fetch_variables()

    # Formatear para presentación
    result = []
    for var in variables:
        result.append({
            "idVariable": var.get("idVariable"),
            "descripcion": var.get("descripcion"),
            "categoria": var.get("categoria"),
            "periodicidad": var.get("periodicidad"),
            "unidadExpresion": var.get("unidadExpresion"),
            "ultFechaInformada": var.get("ultFechaInformada"),
            "ultValorInformado": var.get("ultValorInformado"),
        })

    return json.dumps(
        {
            "total": len(result),
            "variables": result,
        },
        ensure_ascii=False,
        indent=2,
    )


async def tool_get_variable_data(
    variable_id: int, desde: str, hasta: str
) -> str:
    """Obtiene serie temporal de una variable entre dos fechas."""
    try:
        datos = await _fetch_variable_data(variable_id, desde, hasta)
    except httpx.HTTPStatusError as e:
        return json.dumps(
            {
                "error": f"Error HTTP {e.response.status_code} al consultar variable {variable_id}",
                "detalle": str(e),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Error al obtener datos: {e}"},
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "variable_id": variable_id,
            "desde": desde,
            "hasta": hasta,
            "total_registros": len(datos),
            "datos": datos,
        },
        ensure_ascii=False,
        indent=2,
    )


async def tool_get_latest_values(variable_ids: list[int]) -> str:
    """Obtiene el último valor disponible para una o más variables."""
    variables = await _fetch_variables()

    # Crear mapa de id → variable
    var_map: dict[int, dict[str, Any]] = {}
    for var in variables:
        vid = var.get("idVariable")
        if vid is not None:
            var_map[int(vid)] = var

    results = []
    not_found = []
    for vid in variable_ids:
        if vid in var_map:
            v = var_map[vid]
            results.append({
                "idVariable": v.get("idVariable"),
                "descripcion": v.get("descripcion"),
                "categoria": v.get("categoria"),
                "ultFechaInformada": v.get("ultFechaInformada"),
                "ultValorInformado": v.get("ultValorInformado"),
                "unidadExpresion": v.get("unidadExpresion"),
            })
        else:
            not_found.append(vid)

    output: dict[str, Any] = {
        "total": len(results),
        "resultados": results,
    }
    if not_found:
        output["no_encontradas"] = not_found

    return json.dumps(output, ensure_ascii=False, indent=2)


async def tool_search_variables(query: str) -> str:
    """Busca variables por nombre/descripción."""
    variables = await _fetch_variables()
    query_norm = _norm(query)
    tokens = query_norm.split()

    if not tokens:
        return json.dumps(
            {"error": "Query vacía. Proporcioná palabras clave para buscar."},
            ensure_ascii=False,
        )

    matches = []
    for var in variables:
        descripcion = var.get("descripcion", "")
        categoria = var.get("categoria", "")
        searchable = f"{descripcion} {categoria}"
        searchable_norm = _norm(searchable)

        # Requiere que TODOS los tokens aparezcan (AND semántico)
        if all(token in searchable_norm for token in tokens):
            score = sum(searchable_norm.count(token) for token in tokens)
            # Bonus si la descripción empieza con el primer token
            if _norm(descripcion).startswith(tokens[0]):
                score += 3
            matches.append((score, var))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, var in matches:
        results.append({
            "idVariable": var.get("idVariable"),
            "descripcion": var.get("descripcion"),
            "categoria": var.get("categoria"),
            "periodicidad": var.get("periodicidad"),
            "unidadExpresion": var.get("unidadExpresion"),
            "ultFechaInformada": var.get("ultFechaInformada"),
            "ultValorInformado": var.get("ultValorInformado"),
        })

    return json.dumps(
        {
            "query": query,
            "total_variables": len(variables),
            "matched": len(results),
            "resultados": results,
        },
        ensure_ascii=False,
        indent=2,
    )


# -----------------------------------------------------------------------------
# Registro del servidor MCP
# -----------------------------------------------------------------------------
server: Server = Server("mcp-bcra")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_variables",
            description=(
                "Lista todas las variables económicas disponibles del BCRA "
                "(Banco Central de la República Argentina). Incluye reservas "
                "internacionales, tipo de cambio, base monetaria, tasas de "
                "interés, inflación, etc. Cada variable incluye su último "
                "valor y fecha de actualización."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_variable_data",
            description=(
                "Obtiene la serie temporal de una variable del BCRA entre "
                "dos fechas. Útil para analizar evolución de tipo de cambio, "
                "reservas, inflación, tasas, etc. Las fechas deben estar en "
                "formato YYYY-MM-DD."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "variable_id": {
                        "type": "integer",
                        "description": (
                            "ID de la variable (obtener con list_variables "
                            "o search_variables)"
                        ),
                    },
                    "desde": {
                        "type": "string",
                        "description": "Fecha inicio en formato YYYY-MM-DD",
                    },
                    "hasta": {
                        "type": "string",
                        "description": "Fecha fin en formato YYYY-MM-DD",
                    },
                },
                "required": ["variable_id", "desde", "hasta"],
            },
        ),
        Tool(
            name="get_latest_values",
            description=(
                "Obtiene el valor más reciente de una o más variables del "
                "BCRA. Útil para consultas rápidas como '¿cuánto están las "
                "reservas hoy?' o '¿cuál es el tipo de cambio actual?'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "variable_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": (
                            "Lista de IDs de variables a consultar "
                            "(ej: [1, 4, 6])"
                        ),
                    },
                },
                "required": ["variable_ids"],
            },
        ),
        Tool(
            name="search_variables",
            description=(
                "Busca variables del BCRA por nombre o descripción. "
                "Búsqueda insensible a tildes y mayúsculas. Usa AND entre "
                "palabras. Útil para encontrar el ID de una variable antes "
                "de consultar sus datos históricos."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Palabras clave (ej: 'reservas', 'tipo cambio', "
                            "'tasa política', 'inflación')"
                        ),
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "list_variables":
            out = await tool_list_variables()
        elif name == "get_variable_data":
            out = await tool_get_variable_data(
                arguments["variable_id"],
                arguments["desde"],
                arguments["hasta"],
            )
        elif name == "get_latest_values":
            out = await tool_get_latest_values(arguments["variable_ids"])
        elif name == "search_variables":
            out = await tool_search_variables(arguments["query"])
        else:
            out = json.dumps({"error": f"Tool desconocida: {name}"})
    except Exception as e:
        log.error("Error en tool %s: %s", name, e, exc_info=True)
        out = json.dumps(
            {"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False
        )
    return [TextContent(type="text", text=out)]


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
async def _amain() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
