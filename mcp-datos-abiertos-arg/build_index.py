"""
build_index.py — Construye un índice local del catálogo de datos.gob.ar

Descarga el catálogo completo (~1,233 datasets) paginando contra el endpoint
CKAN `package_search`, extrae los campos útiles para búsqueda y los guarda
en `index.json`.

Este archivo permite que el servidor MCP arranque instantáneo y haga búsqueda
full-text sin depender de que el portal responda rápido en tiempo real.

Uso:
    python build_index.py              # construye index.json completo
    python build_index.py --limit 100  # trae solo 100 (para desarrollo rápido)
    python build_index.py --offset 500 --append  # continúa desde offset 500
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://datos.gob.ar"
API = f"{BASE_URL}/api/3/action"
PAGE_SIZE = 50
TIMEOUT = 60.0
DEFAULT_OUT = Path(__file__).parent / "index.json"


def _slim(ds: dict[str, Any]) -> dict[str, Any]:
    """Reduce un dataset completo al mínimo útil para búsqueda + navegación."""
    tags = [
        t.get("display_name") or t.get("name", "")
        for t in ds.get("tags", [])
        if isinstance(t, dict)
    ]
    groups = [
        g.get("title") or g.get("display_name") or g.get("name", "")
        for g in ds.get("groups", [])
        if isinstance(g, dict)
    ]

    # Organización
    org = ds.get("organization")
    org_title = ""
    if isinstance(org, dict):
        org_title = org.get("title") or org.get("name") or ""

    resources = [
        {
            "name": r.get("name"),
            "format": r.get("format"),
            "url": r.get("url"),
            "description": (r.get("description") or "")[:200],
        }
        for r in ds.get("resources", [])
        if isinstance(r, dict)
    ]

    notes = (ds.get("notes") or "")[:800]

    return {
        "id": ds.get("id"),
        "name": ds.get("name"),
        "title": ds.get("title"),
        "notes": notes,
        "author": ds.get("author") or "",
        "organization": org_title,
        "tags": tags,
        "groups": groups,
        "num_resources": len(resources),
        "resources": resources,
        "license": ds.get("license_title"),
        "metadata_modified": ds.get("metadata_modified"),
    }


async def _fetch_page(
    client: httpx.AsyncClient, offset: int, rows: int
) -> tuple[list[dict[str, Any]], int]:
    """Fetch una página de package_search. Retorna (datasets, total_count)."""
    params = {"rows": rows, "start": offset}
    r = await client.get(f"{API}/package_search", params=params)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"API error at offset {offset}: {data.get('error')}")
    result = data.get("result", {})
    return result.get("results", []), result.get("count", 0)


async def build(
    max_total: int | None,
    out_path: Path,
    start_offset: int = 0,
    append: bool = False,
) -> None:
    start = time.time()

    existing_items: list[dict[str, Any]] = []
    if append and out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
            existing_items = prev.get("datasets", [])
            print(f"Modo append: {len(existing_items)} datasets ya presentes")
        except Exception as e:
            print(f"No pude leer {out_path} ({e}), empezando de cero")

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        # Obtener total del catálogo
        _, total_catalog = await _fetch_page(client, 0, 0)
        print(f"Catálogo total: {total_catalog} datasets")

        target = min(max_total or total_catalog, total_catalog)
        print(
            f"Descargando {target} desde offset={start_offset} "
            f"(páginas de {PAGE_SIZE})..."
        )

        new_items: list[dict[str, Any]] = []
        offset = start_offset
        end = min(start_offset + target, total_catalog)
        while offset < end:
            rows = min(PAGE_SIZE, end - offset)
            try:
                page, _ = await _fetch_page(client, offset, rows)
            except Exception as e:
                print(f"  ⚠️  offset={offset}: {e}", file=sys.stderr)
                offset += rows
                continue
            if not page:
                print(f"  offset={offset}: página vacía, detengo")
                break
            new_items.extend(page)
            print(f"  offset={offset:>5}  +{len(page):>3}  total={len(new_items)}")
            offset += rows

    elapsed = time.time() - start
    slim_new = [_slim(ds) for ds in new_items]

    # Dedup por id al mergear
    seen_ids = {d.get("id") for d in existing_items if d.get("id")}
    merged = list(existing_items) + [
        d for d in slim_new if d.get("id") not in seen_ids
    ]

    payload = {
        "source": BASE_URL,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_catalog": total_catalog,
        "total_indexed": len(merged),
        "elapsed_seconds": round(elapsed, 1),
        "datasets": merged,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(
        f"\n✅ +{len(slim_new)} nuevos, total={len(merged)} → {out_path} "
        f"({size_mb:.1f} MB, {elapsed:.1f}s)"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--limit", type=int, default=None, help="Máximo a descargar este batch"
    )
    p.add_argument("--offset", type=int, default=0, help="Offset inicial")
    p.add_argument(
        "--append", action="store_true", help="Fusiona con index.json existente"
    )
    p.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Archivo de salida"
    )
    args = p.parse_args()
    asyncio.run(build(args.limit, args.out, args.offset, args.append))


if __name__ == "__main__":
    main()
