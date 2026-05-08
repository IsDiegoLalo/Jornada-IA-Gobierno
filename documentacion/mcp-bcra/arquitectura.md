# Arquitectura — MCP BCRA

## Visión general

El MCP BCRA es un servidor que expone la API de Estadísticas del Banco Central de la República Argentina como herramientas consumibles por agentes de IA. A diferencia del MCP de Datos Abiertos (que usa un índice local), este MCP consulta la API del BCRA en vivo para cada operación, con cache en memoria para la lista de variables.

## Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTE DE IA                                 │
│  (Kiro / Claude Desktop / VS Code / Cursor / Claude Code)           │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ stdio (JSON-RPC)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SERVIDOR MCP (main.py)                           │
│                                                                     │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │ Tool Router │  │ Variables Cache   │  │ HTTP Client (httpx)   │  │
│  │ (4 tools)   │  │ (en memoria,     │  │ - list_variables      │  │
│  │             │  │  lazy load)      │  │ - get_variable_data   │  │
│  └─────────────┘  └──────────────────┘  │ - search (local)      │  │
│                                          └───────────┬───────────┘  │
│                                                      │              │
└──────────────────────────────────────────────────────┼──────────────┘
                                                       │
                                              ┌────────▼──────────────┐
                                              │  api.bcra.gob.ar      │
                                              │  /estadisticas/v2.0   │
                                              │                       │
                                              │  - PrincipalesVars    │
                                              │  - DatosVariable      │
                                              └───────────────────────┘
```

## Componentes

### 1. `main.py` — Servidor MCP

- **Transporte**: stdio (stdin/stdout con JSON-RPC)
- **Cache**: Lista de variables en memoria tras primera carga (~1220 variables)
- **Búsqueda**: Full-text local sobre el cache de variables
- **Datos en vivo**: `get_variable_data` siempre consulta la API
- **API version**: v4.0 (`/estadisticas/v4.0/Monetarias`)

### 2. Cache de variables

- **Estrategia**: Lazy loading — se carga en la primera llamada que lo necesite
- **Invalidación**: Se mantiene durante toda la vida del proceso
- **Contenido**: ~1220 variables con ID, descripción, categoría, último valor y fecha

## Decisiones de diseño

| Decisión | Justificación |
|----------|---------------|
| Sin índice local (vs datos-abiertos) | La API del BCRA es rápida y tiene ~1220 variables, se cachean en memoria |
| Cache en memoria | Evita llamadas repetidas a `/estadisticas/v4.0/Monetarias` que cambia poco |
| `verify=False` en httpx | La API del BCRA puede tener issues de certificado SSL en algunos entornos |
| Búsqueda AND semántica | Consistente con el patrón del MCP de datos abiertos |
| Normalización sin tildes | Usuarios escriben "inflacion" o "inflación" indistintamente |
| Sin API key | La API es 100% pública, no requiere autenticación |
| Fechas YYYY-MM-DD | Formato estándar ISO que la API espera |

## Flujo de una consulta típica

### Consulta de último valor

```
1. Usuario pregunta: "¿Cuánto están las reservas?"
2. Agente llama: search_variables(query="reservas")
3. MCP carga variables (o usa cache)
4. Filtra por "reservas" en descripción
5. Retorna matches con ID, descripción, último valor
6. Agente sintetiza respuesta
```

### Consulta de serie temporal

```
1. Usuario pregunta: "Evolución del dólar en el último mes"
2. Agente llama: search_variables(query="tipo cambio")
3. MCP retorna variables de tipo de cambio con sus IDs
4. Agente llama: get_variable_data(variable_id=4, desde="2026-04-23", hasta="2026-05-23")
5. MCP consulta API del BCRA en vivo
6. Retorna serie temporal con fechas y valores
7. Agente presenta los datos al usuario
```

## Seguridad

- **Sin credenciales**: La API es pública, no maneja secrets
- **Read-only**: Solo lectura, nunca modifica datos
- **SSL flexible**: `verify=False` por compatibilidad (la API es pública)
- **Sin PII en logs**: No logea datos sensibles del usuario
- **Timeout**: 30 segundos máximo por request

## Diferencias con MCP Datos Abiertos

| Aspecto | MCP Datos Abiertos | MCP BCRA |
|---------|-------------------|----------|
| Fuente | datos.gob.ar (CKAN) | api.bcra.gob.ar (v4.0) |
| Índice | Local (index.json, ~3 MB) | Cache en memoria (~1220 vars) |
| Búsqueda | Offline sobre índice | Sobre cache de variables |
| Datos | Preview de CSV/XLSX | Series temporales numéricas |
| Dependencias | mcp, httpx, pandas | mcp, httpx |
| Autenticación | Ninguna | Ninguna |
