# Documentación — MCP BCRA (Banco Central de la República Argentina)

Esta carpeta contiene la documentación completa del servidor MCP para la API pública del BCRA.

## Contenido

| Archivo | Descripción |
|---------|-------------|
| [arquitectura.md](arquitectura.md) | Arquitectura técnica, flujo de datos, decisiones de diseño |
| [instalacion.md](instalacion.md) | Guía paso a paso de instalación y configuración |
| [uso.md](uso.md) | Ejemplos de prompts y cómo invocar las herramientas |
| [api-reference.md](api-reference.md) | Referencia completa de las 4 tools del MCP |

## Sobre la API del BCRA

La API de Estadísticas del BCRA (`api.bcra.gob.ar`, versión 4.0) es pública y no requiere autenticación. Provee acceso a las principales variables macroeconómicas de Argentina:

- Reservas internacionales
- Tipo de cambio (minorista y mayorista)
- Base monetaria
- Tasas de interés (BADLAR, etc.)
- Depósitos y préstamos del sistema financiero
- Series monetarias históricas
- Y muchas más (~1220 variables)

## Links útiles

- [API BCRA - Estadísticas](https://api.bcra.gob.ar)
- [BCRA - Sitio oficial](https://www.bcra.gob.ar/)
- [Código fuente del MCP](../../mcp-bcra/)
