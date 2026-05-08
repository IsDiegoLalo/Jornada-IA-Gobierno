# Spec: Monitor de Transporte Público SUBE

## Objetivo
Construir un dashboard que muestre el uso del transporte público SUBE
por línea y día, con filtros por rango de fechas y visualización por zona geográfica.

## Requerimientos funcionales

### RF-01 — Carga de datos
- Cargar el CSV de transacciones SUBE desde S3 (o path local)
- Parsear columnas: fecha, línea, modo (colectivo/tren/subte), cantidad_viajes, zona

### RF-02 — Visualización temporal
- Gráfico de barras con viajes por día
- Selector de rango de fechas (date picker)
- Filtro por modo de transporte (colectivo / tren / subte)
- Filtro por línea

### RF-03 — Visualización geográfica
- Mapa de calor por zona geográfica usando coordenadas del dataset
- Integrar API Georef para normalizar nombres de localidades
- Colorear zonas según volumen de viajes

### RF-04 — Series de tiempo
- Integrar API Series de Tiempo para mostrar tendencia histórica
- Endpoint sugerido: series de viajes SUBE disponibles en apis.datos.gob.ar/series

### RF-05 — Métricas resumen
- Total de viajes en el período seleccionado
- Línea con mayor uso
- Comparativo día hábil vs. fin de semana

## Requerimientos no funcionales
- Stack sugerido: Python (Streamlit o Dash) o React + D3.js
- El CSV debe poder ser reemplazado sin cambiar el código (configurable por variable de entorno)
- Responsive para pantallas de escritorio

## Criterios de aceptación
- [ ] El dashboard carga y muestra datos sin errores
- [ ] Los filtros funcionan correctamente
- [ ] El mapa muestra zonas georreferenciadas con API Georef
- [ ] La serie temporal se consulta desde la API de Series de Tiempo
- [ ] El README explica cómo correr el proyecto localmente

## Recursos
- Dataset: <REDACTED>
- API Georef: <REDACTED>
- API Series de Tiempo: <REDACTED>
