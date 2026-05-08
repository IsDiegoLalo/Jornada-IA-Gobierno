# Arquitectura — MCP Datos Abiertos Argentina

## Visión general

El MCP (Model Context Protocol) de Datos Abiertos Argentina es un servidor que expone el catálogo de datos.gob.ar como herramientas consumibles por agentes de IA. Sigue el patrón **índice local + fetch en vivo**.

## Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTE DE IA                                 │
│  (Kiro / Claude Desktop / VS Code / Cursor / Claude Code)           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ stdio (JSON-RPC)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SERVIDOR MCP (main.py)                           │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │ Tool Router │  │ Index Engine │  │ HTTP Client (httpx)        │ │
│  │ (6 tools)   │  │ (búsqueda    │  │ - query_resource_data      │ │
│  │             │  │  full-text)  │  │ - fallback package_show    │ │
│  └─────────────┘  └──────┬───────┘  └────────────┬───────────────┘ │
│                           │                       │                  │
└───────────────────────────┼───────────────────────┼──────────────────┘
                            │                       │
                   ┌────────▼────────┐     ┌───────▼──────────────┐
                   │  index.json     │     │  datos.gob.ar        │
                   │  (~3 MB local)  │     │  API CKAN v3         │
                   │  1,233 datasets │     │  (solo para datos    │
                   └─────────────────┘     │   en vivo)           │
                                           └──────────────────────┘
```

## Componentes

### 1. `build_index.py` — Generador del índice

- **Responsabilidad**: Descargar el catálogo completo de datos.gob.ar y generar un snapshot local
- **Frecuencia**: Se ejecuta una vez (o periódicamente para actualizar)
- **API usada**: `package_search` de CKAN con paginación
- **Output**: `index.json` con metadata slim de cada dataset

### 2. `main.py` — Servidor MCP

- **Transporte**: stdio (stdin/stdout con JSON-RPC)
- **Búsqueda**: Full-text local sobre el índice, sin red
- **Datos en vivo**: Solo `query_resource_data` y fallbacks de `get_dataset_info` hacen HTTP

### 3. `index.json` — Snapshot del catálogo

- **Tamaño**: ~3 MB para ~1,233 datasets
- **Contenido por dataset**: id, name, title, notes (800 chars), author, organization, tags, groups, resources (name + format + url), license, metadata_modified
- **Deduplicación**: Por ID al cargar

## Decisiones de diseño

| Decisión | Justificación |
|----------|---------------|
| Índice local vs API en vivo | Búsqueda instantánea, resiliencia ante caídas del portal, no depender de latencia |
| CKAN `package_search` | datos.gob.ar usa CKAN estándar con API v3 funcional |
| Scoring por campo (título x3, tags x2) | Resultados más relevantes que búsqueda plana |
| AND semántico entre tokens | Evita falsos positivos con queries multi-palabra |
| Normalización sin tildes | Usuarios argentinos escriben con y sin tildes |
| Validación SSRF en URLs | Previene ataques de Server-Side Request Forgery |
| Límite 20 MB en downloads | Protege memoria del servidor |
| Sin API key | El portal es 100% público, no requiere autenticación |

## Flujo de una búsqueda típica

```
1. Usuario pregunta: "¿Qué datos hay sobre salud?"
2. Agente llama: search_datasets(query="salud", limit=10)
3. MCP carga index.json (si no está en memoria)
4. Tokeniza "salud" → ["salud"]
5. Filtra datasets donde "salud" aparece en texto normalizado
6. Calcula score: título(x3) + tags(x2) + org(x2) + notes(x1)
7. Ordena por score descendente, toma top 10
8. Retorna JSON con resultados al agente
9. Agente sintetiza respuesta para el usuario
```

## Flujo de preview de datos

```
1. Agente llama: query_resource_data(url="https://..../file.csv", rows=20)
2. MCP valida URL (SSRF check)
3. Descarga el archivo (máx 20 MB)
4. Detecta formato (CSV/XLSX) y encoding
5. Parsea con pandas, toma primeras N filas
6. Retorna columnas + sample_rows como JSON
```

## Seguridad

- **SSRF Prevention**: Validación de URLs antes de fetch (bloquea IPs privadas, localhost, metadata endpoints)
- **Sin credenciales**: No maneja secrets ni API keys
- **Read-only**: Solo lectura, nunca modifica datos en el portal
- **Límites de tamaño**: 20 MB máximo por recurso, 500 filas máximo por preview
- **Sin PII en logs**: No logea datos sensibles del usuario
