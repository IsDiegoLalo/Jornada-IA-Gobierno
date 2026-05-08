# API Reference — Tools del MCP BCRA

## Resumen

El servidor MCP BCRA expone 4 herramientas (tools) que un agente de IA puede invocar via JSON-RPC sobre stdio.

---

## `list_variables`

Lista todas las variables económicas disponibles del BCRA con su último valor.

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
  "total": 1220,
  "variables": [
    {
      "idVariable": 1,
      "descripcion": "Reservas internacionales",
      "categoria": "Principales Variables",
      "periodicidad": "D",
      "unidadExpresion": "En millones de USD",
      "ultFechaInformada": "2026-05-04",
      "ultValorInformado": 45657.0
    },
    {
      "idVariable": 4,
      "descripcion": "Tipo de cambio minorista (promedio vendedor)",
      "categoria": "Principales Variables",
      "periodicidad": "D",
      "unidadExpresion": "Pesos argentinos por dólar estadounidense",
      "ultFechaInformada": "2026-05-06",
      "ultValorInformado": 1408.27
    }
  ]
}
```

### Comportamiento

- Primera llamada: consulta la API del BCRA v4.0 y cachea el resultado (~1220 variables)
- Llamadas subsiguientes: retorna desde cache (instantáneo)
- El cache persiste durante toda la vida del proceso MCP
- Usa paginación automática para obtener todas las variables

---

## `get_variable_data`

Obtiene la serie temporal de una variable del BCRA entre dos fechas.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "variable_id": {
      "type": "integer",
      "description": "ID de la variable (obtener con list_variables o search_variables)"
    },
    "desde": {
      "type": "string",
      "description": "Fecha inicio en formato YYYY-MM-DD"
    },
    "hasta": {
      "type": "string",
      "description": "Fecha fin en formato YYYY-MM-DD"
    }
  },
  "required": ["variable_id", "desde", "hasta"]
}
```

### Output

```json
{
  "variable_id": 4,
  "desde": "2026-05-01",
  "hasta": "2026-05-23",
  "total_registros": 16,
  "datos": [
    {
      "fecha": "2026-05-23",
      "valor": 1408.27
    },
    {
      "fecha": "2026-05-22",
      "valor": 1405.50
    }
  ]
}
```

### Notas

- Las fechas deben estar en formato YYYY-MM-DD
- La API del BCRA solo retorna datos para días hábiles
- Los datos se retornan en orden descendente (más reciente primero)
- Si la variable no existe, retorna error HTTP 404

### Errores posibles

```json
{"error": "Error HTTP 404 al consultar variable 999", "detalle": "..."}
{"error": "Error al obtener datos: ..."}
```

---

## `get_latest_values`

Obtiene el valor más reciente de una o más variables del BCRA.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "variable_ids": {
      "type": "array",
      "items": {"type": "integer"},
      "description": "Lista de IDs de variables a consultar (ej: [1, 4, 6])"
    }
  },
  "required": ["variable_ids"]
}
```

### Output

```json
{
  "total": 3,
  "resultados": [
    {
      "idVariable": 1,
      "descripcion": "Reservas internacionales",
      "categoria": "Principales Variables",
      "ultFechaInformada": "2026-05-04",
      "ultValorInformado": 45657.0,
      "unidadExpresion": "En millones de USD"
    },
    {
      "idVariable": 4,
      "descripcion": "Tipo de cambio minorista (promedio vendedor)",
      "categoria": "Principales Variables",
      "ultFechaInformada": "2026-05-06",
      "ultValorInformado": 1408.27,
      "unidadExpresion": "Pesos argentinos por dólar estadounidense"
    }
  ]
}
```

### Notas

- Los valores provienen del cache de variables (última actualización del BCRA)
- Si un ID no existe en el cache, aparece en el campo `no_encontradas`
- Útil para dashboards o resúmenes rápidos

### Output con variables no encontradas

```json
{
  "total": 2,
  "resultados": [...],
  "no_encontradas": [999, 888]
}
```

---

## `search_variables`

Busca variables del BCRA por nombre o descripción.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Palabras clave (ej: 'reservas', 'tipo cambio', 'tasa política', 'inflación')"
    }
  },
  "required": ["query"]
}
```

### Output

```json
{
  "query": "tipo cambio",
  "total_variables": 1220,
  "matched": 15,
  "resultados": [
    {
      "idVariable": 4,
      "descripcion": "Tipo de cambio minorista (promedio vendedor)",
      "categoria": "Principales Variables",
      "periodicidad": "D",
      "unidadExpresion": "Pesos argentinos por dólar estadounidense",
      "ultFechaInformada": "2026-05-06",
      "ultValorInformado": 1408.27
    },
    {
      "idVariable": 5,
      "descripcion": "Tipo de cambio mayorista de referencia",
      "categoria": "Principales Variables",
      "periodicidad": "D",
      "unidadExpresion": "Pesos argentinos por dólar estadounidense",
      "ultFechaInformada": "2026-05-06",
      "ultValorInformado": 1386.29
    }
  ]
}
```

### Algoritmo de búsqueda

1. Normaliza la query (minúsculas, sin tildes)
2. Tokeniza por espacios
3. Filtra variables donde TODOS los tokens aparecen en la descripción (AND)
4. Calcula score por frecuencia de tokens
5. Bonus +3 si la descripción empieza con el primer token
6. Ordena por score descendente

### Errores posibles

```json
{"error": "Query vacía. Proporcioná palabras clave para buscar."}
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
- `httpx.HTTPStatusError` — Error HTTP al consultar la API del BCRA
- `httpx.ConnectError` — No se pudo conectar a la API
- `httpx.TimeoutException` — Timeout (>30 segundos)
- Variable no encontrada — ID inválido

## Protocolo

- **Transporte**: stdio (stdin/stdout)
- **Formato**: JSON-RPC 2.0 (estándar MCP)
- **Server name**: `mcp-bcra`

## API del BCRA subyacente

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/estadisticas/v4.0/Monetarias` | GET | Lista de variables con último valor (paginado) |
| `/estadisticas/v4.0/Monetarias/{id}` | GET | Serie temporal (con params `desde`, `hasta`, `limit`) |

- **Base URL**: `https://api.bcra.gob.ar`
- **Versión**: v4.0 (la v2.0 fue deprecada)
- **Autenticación**: Ninguna (API pública)
- **Formato de respuesta**: JSON
- **Formato de fechas**: YYYY-MM-DD
- **Paginación**: `limit` (máx 3000) y `offset`
