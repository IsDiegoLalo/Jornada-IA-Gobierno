"""
MCP Argentina — Servidor MCP para el Portal Nacional de Datos Abiertos
https://datos.gob.ar

Expone 6 herramientas:
  - search_datasets(query, limit): búsqueda full-text sobre el índice local
  - get_dataset_info(dataset_id): detalle de un dataset
  - list_dataset_resources(dataset_id): archivos (CSV/XLSX/etc.)
  - query_resource_data(resource_url, rows): preview de filas de un CSV
  - list_organizations(): entidades publicadoras (del índice)
  - index_stats(): info del índice (cuándo se generó, cuántos datasets)

El servidor usa un índice local (`index.json`, generado con `build_index.py`)
para búsqueda instantánea sobre título + descripción + tags + entidad, sin
depender del portal para cada query. Para detalle/datos sí consulta el portal
en vivo.

Transporte: stdio (compatible con Claude Desktop, Kiro, Cursor, VS Code, etc.)
"""

from __future__ import annotations

import asyncio
import io
import ipaddress
import json
import logging
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Logging al stderr (stdout lo usa el protocolo MCP por stdio — no tocar).
logging.basicConfig(
    level=os.environ.get("MCP_ARG_LOGLEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] mcp-argentina: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("mcp-argentina")

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
BASE_URL = os.environ.get("DATOSARG_BASE", "https://datos.gob.ar")
API = f"{BASE_URL}/api/3/action"
INDEX_PATH = Path(
    os.environ.get("MCP_ARG_INDEX", Path(__file__).parent / "index.json")
)

TIMEOUT = 30.0


# -----------------------------------------------------------------------------
# Normalización e índice
# -----------------------------------------------------------------------------
_WORD_RE = re.compile(r"[a-z0-9áéíóúñü]+", re.IGNORECASE)


def _norm(s: str) -> str:
    """Minúsculas + sin tildes."""
    s = s or ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _tokens(s: str) -> list[str]:
    return _WORD_RE.findall(_norm(s))


class Index:
    """Índice local cargado desde index.json."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.metadata: dict[str, Any] = {}
        self.datasets: list[dict[str, Any]] = []
        self._by_id: dict[str, dict[str, Any]] = {}
        self._by_name: dict[str, dict[str, Any]] = {}
        self._searchable: list[str] = []
        self.loaded = False

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(
                f"No encontré el índice en {self.path}. "
                f"Ejecutá `python build_index.py` primero para generarlo."
            )
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.metadata = {k: v for k, v in data.items() if k != "datasets"}
        raw = data.get("datasets", [])

        # Dedup por ID
        seen: set[str] = set()
        self.datasets = []
        duplicates = 0
        for ds in raw:
            ds_id = ds.get("id") or ds.get("name")
            if not ds_id:
                continue
            if ds_id in seen:
                duplicates += 1
                continue
            seen.add(ds_id)
            self.datasets.append(ds)

        for ds in self.datasets:
            if ds.get("id"):
                self._by_id[ds["id"]] = ds
            if ds.get("name"):
                self._by_name[ds["name"]] = ds
            self._searchable.append(
                _norm(
                    " ".join(
                        [
                            ds.get("title") or "",
                            ds.get("name") or "",
                            ds.get("notes") or "",
                            " ".join(ds.get("tags") or []),
                            " ".join(ds.get("groups") or []),
                            ds.get("organization") or "",
                            ds.get("author") or "",
                        ]
                    )
                )
            )
        self.loaded = True
        log.info(
            "Índice cargado: %d datasets (%d duplicados descartados) desde %s",
            len(self.datasets),
            duplicates,
            self.path,
        )

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        return self._by_id.get(dataset_id) or self._by_name.get(dataset_id)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Búsqueda por scoring: cada token de la query aporta puntos si aparece
        en título (x3), tags (x2), organización (x2), o notes/nombre (x1).
        Requiere que TODOS los tokens aparezcan en algún campo (AND).
        """
        tokens = _tokens(query)
        if not tokens:
            return []

        scored: list[tuple[int, dict[str, Any]]] = []
        for ds, hay in zip(self.datasets, self._searchable):
            if not all(t in hay for t in tokens):
                continue
            score = 0
            title_n = _norm(ds.get("title") or "")
            tags_n = _norm(" ".join(ds.get("tags") or []))
            org_n = _norm(ds.get("organization") or "")
            notes_n = _norm(ds.get("notes") or "")
            for t in tokens:
                score += 3 * title_n.count(t)
                score += 2 * tags_n.count(t)
                score += 2 * org_n.count(t)
                score += 1 * notes_n.count(t)
            # Bonus si el título empieza con el primer token
            if title_n.startswith(tokens[0]):
                score += 5
            scored.append((score, ds))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ds for _, ds in scored[:limit]]

    def organizations(self) -> list[str]:
        seen: set[str] = set()
        for ds in self.datasets:
            for g in ds.get("groups") or []:
                if g:
                    seen.add(g)
            org = ds.get("organization")
            if org:
                seen.add(org)
        return sorted(seen)


INDEX = Index(INDEX_PATH)


# -----------------------------------------------------------------------------
# Helpers HTTP (para operaciones que SÍ necesitan el portal en vivo)
# -----------------------------------------------------------------------------
async def _api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    log.debug("GET %s/%s params=%s", API, path, params)
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(f"{API}/{path}", params=params or {})
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"API error: {data.get('error', data)}")
        return data["result"]


def _summary(ds: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": ds.get("id"),
        "name": ds.get("name"),
        "title": ds.get("title"),
        "organization": ds.get("organization"),
        "description": (ds.get("notes") or "")[:400],
        "tags": ds.get("tags", []),
        "num_resources": ds.get("num_resources", len(ds.get("resources", []))),
        "last_modified": ds.get("metadata_modified"),
        "url": f"{BASE_URL}/dataset/{ds.get('name', '')}",
    }


# -----------------------------------------------------------------------------
# Herramientas MCP
# -----------------------------------------------------------------------------
async def tool_search_datasets(query: str, limit: int = 10) -> str:
    if not INDEX.loaded:
        INDEX.load()
    limit = max(1, min(limit, 50))
    matches = INDEX.search(query, limit=limit)
    log.info("search_datasets(%r, limit=%d) → %d matches", query, limit, len(matches))
    return json.dumps(
        {
            "query": query,
            "total_in_index": INDEX.metadata.get("total_indexed", len(INDEX.datasets)),
            "matched": len(matches),
            "results": [_summary(m) for m in matches],
        },
        ensure_ascii=False,
        indent=2,
    )


async def tool_get_dataset_info(dataset_id: str) -> str:
    if not INDEX.loaded:
        INDEX.load()
    ds = INDEX.get(dataset_id)
    if ds is None:
        # Fallback: consulta en vivo al portal
        try:
            result = await _api_get("package_show", {"id": dataset_id})
            if isinstance(result, dict):
                ds = result
            elif isinstance(result, list) and result:
                ds = result[0] if isinstance(result[0], dict) else {}
            else:
                ds = None
        except Exception:
            ds = None

        if not ds:
            return json.dumps(
                {"error": f"Dataset no encontrado: {dataset_id}"},
                ensure_ascii=False,
            )

    out = _summary(ds)
    out["full_description"] = ds.get("notes")
    out["license"] = ds.get("license") or ds.get("license_title")
    out["author"] = ds.get("author")
    out["maintainer"] = ds.get("maintainer")
    return json.dumps(out, ensure_ascii=False, indent=2)


async def tool_list_dataset_resources(dataset_id: str) -> str:
    if not INDEX.loaded:
        INDEX.load()
    ds = INDEX.get(dataset_id)
    resources: list[dict[str, Any]]
    if ds and ds.get("resources"):
        resources = ds["resources"]
    else:
        try:
            live = await _api_get("package_show", {"id": dataset_id})
            if isinstance(live, list):
                live = live[0] if live else {}
            resources = [
                {
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "url": r.get("url"),
                    "description": r.get("description"),
                }
                for r in (live or {}).get("resources", [])
            ]
        except Exception as e:
            return json.dumps(
                {"error": f"No se pudo obtener recursos: {e}"},
                ensure_ascii=False,
            )
    return json.dumps(
        {"dataset_id": dataset_id, "resources": resources},
        ensure_ascii=False,
        indent=2,
    )


def _is_safe_url(url: str) -> bool:
    """Valida que la URL sea HTTP(S) en un host público (previene SSRF)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    host = (parsed.hostname or "").lower()
    if not host:
        return False

    # Bloquear endpoints de metadata cloud
    _BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal"}
    if host in _BLOCKED_HOSTS:
        return False

    # Bloquear IPs privadas/loopback
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except ValueError:
        if host in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]"):
            return False

    return True


async def tool_query_resource_data(resource_url: str, rows: int = 20) -> str:
    rows = max(1, min(rows, 500))

    if not _is_safe_url(resource_url):
        return json.dumps(
            {"error": "URL no permitida. Solo se aceptan URLs HTTP(S) públicas."},
            ensure_ascii=False,
        )

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.get(resource_url)
        r.raise_for_status()
        content = r.content

    if len(content) > 20 * 1024 * 1024:
        return json.dumps(
            {
                "error": "Recurso > 20 MB. Descargá directamente la URL.",
                "url": resource_url,
            },
            ensure_ascii=False,
        )

    try:
        lower = resource_url.lower()
        if lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            try:
                df = pd.read_csv(io.BytesIO(content), nrows=rows + 50)
            except UnicodeDecodeError:
                df = pd.read_csv(
                    io.BytesIO(content), nrows=rows + 50, encoding="latin-1"
                )
            except Exception:
                df = pd.read_csv(
                    io.BytesIO(content),
                    nrows=rows + 50,
                    sep=";",
                    encoding="latin-1",
                )
    except Exception as e:
        return json.dumps(
            {"error": f"No se pudo parsear el archivo: {e}", "url": resource_url},
            ensure_ascii=False,
        )

    preview = df.head(rows)
    return json.dumps(
        {
            "url": resource_url,
            "columns": list(preview.columns.astype(str)),
            "row_count_preview": len(preview),
            "total_rows_in_file_approx": len(df),
            "sample_rows": preview.fillna("").astype(str).to_dict(orient="records"),
        },
        ensure_ascii=False,
        indent=2,
    )


async def tool_list_organizations() -> str:
    if not INDEX.loaded:
        INDEX.load()
    orgs = INDEX.organizations()
    return json.dumps(
        {"total": len(orgs), "organizations": orgs},
        ensure_ascii=False,
        indent=2,
    )


async def tool_index_stats() -> str:
    if not INDEX.loaded:
        INDEX.load()
    return json.dumps(
        {
            **INDEX.metadata,
            "index_path": INDEX.path.name,
            "tools": [
                "search_datasets",
                "get_dataset_info",
                "list_dataset_resources",
                "query_resource_data",
                "list_organizations",
                "index_stats",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


# -----------------------------------------------------------------------------
# Registro del servidor MCP
# -----------------------------------------------------------------------------
server: Server = Server("mcp-argentina-datos-abiertos")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_datasets",
            description=(
                "Busca datasets en el Portal Nacional de Datos Abiertos de Argentina "
                "(datos.gob.ar). Full-text sobre título, descripción, tags y "
                "entidad publicadora. Ignora tildes. Usa AND entre palabras, ordena "
                "por relevancia. Siempre empieza con esta tool cuando el usuario "
                "pregunte por datos del Estado argentino."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Palabras clave (ej: 'educación', 'salud covid', "
                            "'presupuesto', 'transporte')"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Máx resultados (1-50)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_dataset_info",
            description=(
                "Metadata completa de un dataset (descripción, licencia, autor, "
                "fecha, URL). Usa id o slug."
            ),
            inputSchema={
                "type": "object",
                "properties": {"dataset_id": {"type": "string"}},
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="list_dataset_resources",
            description=(
                "Lista los archivos/recursos (CSV, XLSX, PDF, API) de un dataset "
                "con su URL de descarga."
            ),
            inputSchema={
                "type": "object",
                "properties": {"dataset_id": {"type": "string"}},
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="query_resource_data",
            description=(
                "Descarga un recurso CSV/XLSX y devuelve las primeras filas como "
                "preview. Útil para inspeccionar estructura y contenido antes de "
                "analizar."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_url": {
                        "type": "string",
                        "description": "URL directa del CSV/XLSX",
                    },
                    "rows": {
                        "type": "integer",
                        "default": 20,
                        "description": "Filas a devolver (1-500)",
                    },
                },
                "required": ["resource_url"],
            },
        ),
        Tool(
            name="list_organizations",
            description=(
                "Lista las entidades publicadoras (ministerios, secretarías, "
                "organismos descentralizados del Estado argentino)."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="index_stats",
            description="Info del índice local: cuándo se generó, cuántos datasets, fuente.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "search_datasets":
            out = await tool_search_datasets(
                arguments["query"], arguments.get("limit", 10)
            )
        elif name == "get_dataset_info":
            out = await tool_get_dataset_info(arguments["dataset_id"])
        elif name == "list_dataset_resources":
            out = await tool_list_dataset_resources(arguments["dataset_id"])
        elif name == "query_resource_data":
            out = await tool_query_resource_data(
                arguments["resource_url"], arguments.get("rows", 20)
            )
        elif name == "list_organizations":
            out = await tool_list_organizations()
        elif name == "index_stats":
            out = await tool_index_stats()
        else:
            out = json.dumps({"error": f"Tool desconocida: {name}"})
    except FileNotFoundError as e:
        out = json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        out = json.dumps(
            {"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False
        )
    return [TextContent(type="text", text=out)]


async def _amain() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
