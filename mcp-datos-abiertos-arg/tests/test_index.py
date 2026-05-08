"""Tests unitarios para el MCP Argentina Datos Abiertos."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# Importar desde el directorio padre
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import Index, _norm, _tokens, _is_safe_url


# --- Fixtures ---

SAMPLE_INDEX = {
    "source": "https://datos.gob.ar",
    "generated_at": "2026-05-04T12:00:00",
    "total_catalog": 3,
    "total_indexed": 3,
    "elapsed_seconds": 1.0,
    "datasets": [
        {
            "id": "ds-001",
            "name": "presupuesto-nacional-2024",
            "title": "Presupuesto Nacional 2024",
            "notes": "Ejecución presupuestaria del sector público nacional",
            "author": "Ministerio de Economía",
            "organization": "Ministerio de Economía",
            "tags": ["presupuesto", "gasto público", "finanzas"],
            "groups": ["Economía"],
            "num_resources": 2,
            "resources": [
                {"name": "CSV", "format": "CSV", "url": "https://example.com/a.csv"},
            ],
            "license": "Creative Commons Attribution 4.0",
            "metadata_modified": "2024-06-01T10:00:00",
        },
        {
            "id": "ds-002",
            "name": "covid-19-casos",
            "title": "Casos COVID-19 Argentina",
            "notes": "Registro de casos confirmados de COVID-19",
            "author": "Ministerio de Salud",
            "organization": "Ministerio de Salud",
            "tags": ["covid", "salud", "pandemia"],
            "groups": ["Salud"],
            "num_resources": 1,
            "resources": [
                {"name": "CSV", "format": "CSV", "url": "https://example.com/b.csv"},
            ],
            "license": "Creative Commons Attribution 4.0",
            "metadata_modified": "2024-03-15T08:00:00",
        },
    ],
}


@pytest.fixture
def index_file(tmp_path: Path) -> Path:
    p = tmp_path / "index.json"
    p.write_text(json.dumps(SAMPLE_INDEX, ensure_ascii=False), encoding="utf-8")
    return p


@pytest.fixture
def loaded_index(index_file: Path) -> Index:
    idx = Index(index_file)
    idx.load()
    return idx


# --- Tests de normalización ---

def test_norm_removes_accents():
    assert _norm("Educación") == "educacion"
    assert _norm("INFORMACIÓN") == "informacion"


def test_norm_lowercase():
    assert _norm("HELLO World") == "hello world"


def test_tokens_splits_words():
    result = _tokens("COVID-19 en Argentina")
    assert "covid" in result
    assert "19" in result
    assert "argentina" in result


# --- Tests del índice ---

def test_index_loads(loaded_index: Index):
    assert loaded_index.loaded
    assert len(loaded_index.datasets) == 2


def test_index_dedup(tmp_path: Path):
    data = SAMPLE_INDEX.copy()
    data["datasets"] = SAMPLE_INDEX["datasets"] + SAMPLE_INDEX["datasets"]
    p = tmp_path / "index.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    idx = Index(p)
    idx.load()
    assert len(idx.datasets) == 2


def test_index_get_by_id(loaded_index: Index):
    ds = loaded_index.get("ds-001")
    assert ds is not None
    assert ds["title"] == "Presupuesto Nacional 2024"


def test_index_get_by_name(loaded_index: Index):
    ds = loaded_index.get("covid-19-casos")
    assert ds is not None
    assert "COVID" in ds["title"]


def test_index_get_not_found(loaded_index: Index):
    assert loaded_index.get("nonexistent") is None


def test_search_basic(loaded_index: Index):
    results = loaded_index.search("presupuesto")
    assert len(results) == 1
    assert results[0]["id"] == "ds-001"


def test_search_ignores_accents(loaded_index: Index):
    results = loaded_index.search("economia")
    assert len(results) >= 1


def test_search_and_semantics(loaded_index: Index):
    results = loaded_index.search("covid salud")
    assert len(results) == 1
    assert results[0]["id"] == "ds-002"


def test_search_no_results(loaded_index: Index):
    results = loaded_index.search("volcanes")
    assert len(results) == 0


def test_organizations(loaded_index: Index):
    orgs = loaded_index.organizations()
    assert "Ministerio de Economía" in orgs
    assert "Ministerio de Salud" in orgs


# --- Tests de seguridad URL ---

def test_safe_url_public():
    assert _is_safe_url("https://datos.gob.ar/dataset/test.csv") is True


def test_safe_url_blocks_private():
    assert _is_safe_url("http://169.254.169.254/latest/meta-data") is False


def test_safe_url_blocks_localhost():
    assert _is_safe_url("http://localhost:8080/secret") is False


def test_safe_url_blocks_non_http():
    assert _is_safe_url("file:///etc/passwd") is False
    assert _is_safe_url("ftp://example.com/file") is False
