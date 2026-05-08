# API Reference — Tools del MCP

## Resumen

El servidor MCP expone 6 herramientas (tools) que un agente de IA puede invocar via JSON-RPC sobre stdio.

---

## `search_datasets`

Búsqueda full-text sobre el índice local del catálogo de datos.gob.ar.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Palabras clave (ej: 'educación', 'salud covid', 'presupuesto')"
    },
    "limit": {
      "type": "integer",
      "default": 10,
      "description": "Máx resultados (1-50)"
    }
  },
  "required": ["query"]
}
```

### Output

```json
{
  "query": "educación",
  "total_in_index": 1233,
  "matched": 3,
  "results": [
    {
      "id": "...",
      "name": "slug-del-dataset",
      "title": "Título del Dataset",
      "organization": "Nombre del Organismo",
      "description": "Primeros 400 chars de la descripción...",
      "tags": ["tag1", "tag2"],
      "num_resources": 2,
      "last_modified": "2024-06-01T10:00:00",
      "url": "https://datos.gob.ar/dataset/slug-del-dataset"
    }
  ]
}
```

### Algoritmo de búsqueda

1. Tokeniza la query (split por palabras, normaliza sin tildes)
2. Filtra datasets donde TODOS los tokens aparecen (AND semántico)
3. Calcula score: título(×3) + tags(×2) + organización(×2) + notes(×1)
4. Bonus +5 si el título empieza con el primer token
5. Ordena por score descendente

---

## `get_dataset_info`

Metadata completa de un dataset específico.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "dataset_id": {
      "type": "string",
      "description": "ID o slug (name) del dataset"
    }
  },
  "required": ["dataset_id"]
}
```

### Output

```json
{
  "id": "produccion_6f47ec76-...",
  "name": "sepa-precios",
  "title": "Precios SEPA",
  "organization": "Subsecretaría de Defensa del Consumidor",
  "description": "Primeros 400 chars...",
  "tags": ["precios", "consumo"],
  "num_resources": 7,
  "last_modified": "2026-05-04T11:41:28",
  "url": "https://datos.gob.ar/dataset/sepa-precios",
  "full_description": "Descripción completa...",
  "license": "Creative Commons Attribution 4.0",
  "author": "Subsecretaría de Defensa del Consumidor",
  "maintainer": "soporte@comercio.gob.ar"
}
```

### Comportamiento

- Primero busca en el índice local (instantáneo)
- Si no lo encuentra, hace fallback a la API en vivo (`package_show`)

---

## `list_dataset_resources`

Lista los archivos/recursos disponibles de un dataset.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "dataset_id": {
      "type": "string",
      "description": "ID o slug del dataset"
    }
  },
  "required": ["dataset_id"]
}
```

### Output

```json
{
  "dataset_id": "produccion_6f47ec76-...",
  "resources": [
    {
      "name": "Viernes",
      "format": "ZIP",
      "url": "https://datos.produccion.gob.ar/.../sepa_viernes.zip",
      "description": "Precios SEPA Minoristas viernes, 2026-05-01"
    },
    {
      "name": "CSV Consolidado",
      "format": "CSV",
      "url": "https://datos.produccion.gob.ar/.../consolidado.csv",
      "description": "Archivo consolidado mensual"
    }
  ]
}
```

---

## `query_resource_data`

Descarga un recurso CSV/XLSX y devuelve las primeras filas como preview.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "resource_url": {
      "type": "string",
      "description": "URL directa del CSV/XLSX"
    },
    "rows": {
      "type": "integer",
      "default": 20,
      "description": "Filas a devolver (1-500)"
    }
  },
  "required": ["resource_url"]
}
```

### Output

```json
{
  "url": "https://..../archivo.csv",
  "columns": ["columna1", "columna2", "columna3"],
  "row_count_preview": 20,
  "total_rows_in_file_approx": 1500,
  "sample_rows": [
    {"columna1": "valor1", "columna2": "valor2", "columna3": "valor3"},
    ...
  ]
}
```

### Limitaciones

- Máximo 20 MB por archivo
- Soporta CSV (con detección de encoding y separador) y XLSX
- No soporta ZIP, PDF, ni otros formatos binarios
- URLs deben ser HTTP(S) públicas (validación SSRF)

### Errores posibles

```json
{"error": "URL no permitida. Solo se aceptan URLs HTTP(S) públicas."}
{"error": "Recurso > 20 MB. Descargá directamente la URL.", "url": "..."}
{"error": "No se pudo parsear el archivo: ...", "url": "..."}
```

---

## `list_organizations`

Lista todas las entidades publicadoras presentes en el índice.

### Input Schema

```json
{
  "type": "object",
  "properties": {}
}
```

### Output

```json
{
  "total": 45,
  "organizations": [
    "ACUMAR",
    "Administración Nacional de Aviación Civil",
    "ARSAT",
    "Comisión Nacional de Regulación del Transporte",
    "ENACOM",
    "ENARGAS",
    "IGN",
    "INCAA",
    "INDEC",
    "Ministerio de Economía",
    "Ministerio de Salud",
    "..."
  ]
}
```

---

## `index_stats`

Información sobre el índice local: cuándo se generó, cuántos datasets, fuente.

### Input Schema

```json
{
  "type": "object",
  "properties": {}
}
```

### Output

```json
{
  "source": "https://datos.gob.ar",
  "generated_at": "2026-05-04T16:25:41-0300",
  "total_catalog": 1233,
  "total_indexed": 1233,
  "elapsed_seconds": 5.0,
  "index_path": "index.json",
  "tools": [
    "search_datasets",
    "get_dataset_info",
    "list_dataset_resources",
    "query_resource_data",
    "list_organizations",
    "index_stats"
  ]
}
```

---

## Manejo de errores

Todas las tools retornan JSON. En caso de error:

```json
{
  "error": "Descripción del error"
}
```

Errores comunes:
- `FileNotFoundError` — El índice no existe (ejecutar `build_index.py`)
- `httpx.HTTPStatusError` — Error HTTP al consultar el portal en vivo
- `RuntimeError` — Error de la API CKAN
- URL no permitida — Validación SSRF bloqueó la URL

## Protocolo

- **Transporte**: stdio (stdin/stdout)
- **Formato**: JSON-RPC 2.0 (estándar MCP)
- **Server name**: `mcp-argentina-datos-abiertos`
