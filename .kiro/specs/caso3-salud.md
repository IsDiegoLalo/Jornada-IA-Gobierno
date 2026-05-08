Jornada de IA para Gobierno — Specs de Desafíos
This canvas was generated using AI, which can produce inaccurate or harmful responses. Review for accuracy and safety before using.

Jornada de IA para Gobierno — Specs de Desafíos

Specs para los desafíos del jornada usando datasets de datos.gob.ar y APIs de la Dirección.

APIs de soporte disponibles

* API Series de Tiempo →  — consulta de series temporales de datos públicos
* API Georef →  — normalización y georreferenciación de datos geográficos argentinos


CASO 1 — Monitor de Transporte Público SUBE

Descripción

Dashboard que muestra el uso del transporte público SUBE por línea y día, con filtros por rango de fechas y visualización geográfica de zonas de mayor uso.

Nota: la granularidad disponible es a nivel día (no hora). El mapa de rutas no es posible dado que no se dispone del dato de descenso de pasajeros.

Datasets

Dataset
	Fuente
	Formato
	Descripción

Transacciones SUBE por fecha
	datos.transporte.gob.ar
	CSV
	Usos diarios 2023–2025 · ~2M filas/año

Viajes SUBE — día hábil promedio RMBA
	datos.transporte.gob.ar
	CSV
	Trenes, subtes, colectivos · georeferenciado por línea


APIs integradas

* API Georef → para normalizar nombres de localidades/municipios presentes en el dataset y enriquecer la visualización geográfica por zona
* API Series de Tiempo → para consultar la evolución temporal de viajes y graficar tendencias diarias/semanales

Spec Kiro (.kiro/specs/caso1-sube.md)

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


CASO 3 — Mapa de Cobertura de Salud Pública

Descripción

Geovisualización interactiva de hospitales, centros de salud y cobertura sanitaria por región, cruzando datos del Ministerio de Salud con indicadores del INDEC.

Datasets

Dataset
	Fuente
	Formato
	Descripción

Establecimientos de salud por provincia
	datos.salud.gob.ar
	CSV
	Hospitales, CAPS, clínicas · lat/lon · nivel de complejidad

Indicadores de salud por departamento
	datos.salud.gob.ar
	CSV
	Mortalidad infantil, vacunación, tasa médicos/hab

Datos sociodemográficos
	indec.gob.ar
	CSV
	Población por departamento/provincia — para cruzar cobertura relativa


APIs integradas

* API Georef → para normalizar y georreferenciar nombres de provincias y departamentos en todos los datasets, unificando criterios entre fuentes (Salud vs. INDEC)
* API Series de Tiempo → para mostrar evolución temporal de indicadores sanitarios (ej: tasa de vacunación, mortalidad infantil por año)

Spec Kiro (.kiro/specs/caso3-salud.md)

# Spec: Mapa de Cobertura de Salud Pública

## Objetivo
Construir una geovisualización interactiva de la cobertura de salud pública
en Argentina, cruzando establecimientos sanitarios con indicadores del INDEC
y datos del Ministerio de Salud.

## Requerimientos funcionales

### RF-01 — Carga de datos
- Cargar CSV de establecimientos de salud (lat, lon, tipo, provincia, complejidad)
- Cargar CSV de indicadores sanitarios por departamento
- Cruzar con datos INDEC de población para calcular cobertura relativa
- Usar API Georef para normalizar nombres de provincias y departamentos entre datasets

### RF-02 — Mapa principal (Leaflet)
- Mostrar marcadores para cada establecimiento de salud
- Color del marcador según nivel de complejidad:
  - 🟢 Verde: alta complejidad
  - 🟡 Amarillo: mediana complejidad
  - 🔴 Rojo: baja complejidad / CAPS
- Capa de coropletas por provincia/departamento según índice de cobertura

### RF-03 — Panel lateral (sidebar)
- Al hacer clic en una provincia mostrar:
  - Cantidad de establecimientos
  - Tasa de médicos por habitante
  - Mortalidad infantil
  - Cobertura de vacunación
  - Comparativo vs. media nacional

### RF-04 — Series de tiempo
- Integrar API Series de Tiempo para mostrar evolución histórica de indicadores
- Gráfico de línea con selector de indicador (mortalidad, vacunación, etc.)
- Filtro por provincia

### RF-05 — Filtros
- Filtrar mapa por tipo de establecimiento (hospital, CAPS, clínica)
- Filtrar por provincia
- Filtrar por nivel de complejidad

### RF-06 — Normalización geográfica
- Usar API Georef para resolver inconsistencias en nombres entre datasets
- Endpoint: <REDACTED>

## Requerimientos no funcionales
- Stack sugerido: React + Leaflet.js o Python con Folium + Streamlit
- Los CSVs deben ser configurables por variables de entorno o archivo de config
- La app debe funcionar offline una vez cargados los datos (excepto APIs)

## Criterios de aceptación
- [ ] El mapa carga todos los establecimientos correctamente
- [ ] Los marcadores se colorean según complejidad
- [ ] El sidebar muestra indicadores al seleccionar una provincia
- [ ] La serie temporal funciona con la API de Series de Tiempo
- [ ] La normalización geográfica usa API Georef
- [ ] El README incluye instrucciones de instalación y fuentes de datos

## Recursos
- Dataset establecimientos: <REDACTED>
- Dataset indicadores: <REDACTED>
- INDEC datos poblacionales: <REDACTED>
- API Georef: <REDACTED>
- API Series de Tiempo: <REDACTED>


Estructura de repositorio sugerida

Jornada-IA-Gobierno/
├── .kiro/
│   ├── specs/
│   │   ├── caso1-sube.md
│   │   └── caso3-salud.md
│   ├── hooks/
│   │   └── pre-commit.sh
│   └── steering/
│       └── project.md
├── datasets/
│   ├── sube/
│   │   └── README.md   ← links a fuentes y descripción de columnas
│   └── salud/
│       └── README.md
├── caso1-sube/
│   └── README.md
├── caso3-salud/
│   └── README.md
└── README.md

