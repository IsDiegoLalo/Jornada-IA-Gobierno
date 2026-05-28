# Design Document: Dashboard Poblacional Argentina

## Overview

Dashboard interactivo de proyecciones poblacionales de Argentina (2028-2035) generado como un archivo HTML estático autocontenido. Un script Python (`generate_dashboard.py`) carga datos de los últimos 4 censos nacionales (1991, 2001, 2010, 2022), ajusta un modelo de regresión exponencial por provincia, y produce un HTML con gráficos Plotly interactivos. El usuario abre el HTML en el navegador sin necesidad de servidor.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              generate_dashboard.py                   │
├─────────────────────────────────────────────────────┤
│  1. Configuration Layer  (env vars, constants)       │
│  2. Data Layer           (load CSV, validate)        │
│  3. Projection Layer     (exponential regression)    │
│  4. Transform Layer      (aggregation, formatting)   │
│  5. Chart Layer          (Plotly figures → JSON)     │
│  6. HTML Export Layer    (render template → .html)   │
└─────────────────────────────────────────────────────┘
```

Flujo de datos:

```
censos.csv → Carga → Validación → Regresión Exponencial → DataFrame maestro
                                                                  │
                                              ┌───────────────────┼───────────────────┐
                                              ▼                   ▼                   ▼
                                         Línea Temporal     Barras Ranking       Zonas
                                         (Plotly JSON)      (Plotly JSON)     (Plotly JSON)
                                              │                   │                   │
                                              └───────────────────┴───────────────────┘
                                                                  │
                                                    HTML template + JS interactivity
                                                                  │
                                                         dashboard.html
```

## Components and Interfaces

### 1. Configuration Layer

```python
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    """Configuración inmutable de la aplicación."""
    data_path: str
    output_path: str

def load_config() -> AppConfig:
    """Carga configuración desde variables de entorno con defaults seguros."""
    return AppConfig(
        data_path=os.environ.get("DASHBOARD_DATA_PATH", "data/censos.csv"),
        output_path=os.environ.get("DASHBOARD_OUTPUT_PATH", "dashboard.html"),
    )

# Constantes de zonas geográficas
ZONAS: dict[str, list[str]] = {
    "Norte": [
        "Jujuy", "Salta", "Tucumán", "Catamarca", "La Rioja",
        "Santiago del Estero", "Chaco", "Formosa", "Corrientes", "Misiones",
    ],
    "Este/Centro": ["Buenos Aires", "CABA", "Córdoba", "Santa Fe", "Entre Ríos"],
    "Oeste": ["Mendoza", "San Juan", "San Luis"],
    "Sur": ["La Pampa", "Neuquén", "Río Negro", "Chubut", "Santa Cruz", "Tierra del Fuego"],
}

TODAS_LAS_PROVINCIAS: list[str] = [p for provs in ZONAS.values() for p in provs]
ANIOS_PROYECCION: list[int] = list(range(2028, 2036))
```

### 2. Data Layer

```python
import pandas as pd

def load_census_data(path: str) -> pd.DataFrame:
    """Carga datos multi-censales desde CSV.

    Expected CSV format:
        provincia,1991,2001,2010,2022
        Buenos Aires,12594974,13827203,15625084,17541141
        ...

    Returns:
        DataFrame con columnas: provincia + columnas de años censales disponibles.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas o provincias.
    """
    ...

def validate_census_data(df: pd.DataFrame) -> pd.DataFrame:
    """Valida estructura y completitud del DataFrame censal.

    Raises:
        ValueError: Si el formato es inválido, faltan provincias, o no hay
                    al menos 1 año censal numérico.
    """
    ...
```

### 3. Projection Layer

```python
import numpy as np
from scipy.optimize import curve_fit

def fit_exponential(years: list[int], populations: list[float]) -> tuple[float, float]:
    """Ajusta modelo exponencial P(t) = a * exp(b * t) a los datos censales.

    Args:
        years: Lista de años censales disponibles (mínimo 1).
        populations: Población correspondiente a cada año.

    Returns:
        Tupla (a, b) de parámetros del modelo.
    """
    ...

def project_population(census_df: pd.DataFrame) -> pd.DataFrame:
    """Genera proyecciones 2028-2035 usando regresión exponencial por provincia.

    Para cada provincia:
      1. Toma todos los años censales disponibles como puntos de ajuste.
      2. Ajusta P(t) = a * exp(b * t) con scipy.optimize.curve_fit.
      3. Evalúa el modelo en 2028-2035.

    Args:
        census_df: DataFrame con columnas provincia + años censales.

    Returns:
        DataFrame con columnas: provincia, zona, 2028, 2029, ..., 2035, crecimiento_pct
    """
    ...

def get_zona_for_provincia(provincia: str) -> str:
    """Retorna la zona geográfica de una provincia.

    Raises:
        ValueError: Si la provincia no está en ninguna zona.
    """
    ...
```

### 4. Transform Layer

```python
def format_population(value: float) -> str:
    """Formatea valores poblacionales en formato abreviado.

    Rules:
        >= 1_000_000 → "45.0M"
        >= 1_000     → "500K"
        < 1_000      → "750"
    """
    ...

def calculate_growth_percentage(pop_start: float, pop_end: float) -> float:
    """Calcula ((end - start) / start) * 100. Retorna 0.0 si start == 0."""
    ...

def aggregate_by_zona(df: pd.DataFrame) -> pd.DataFrame:
    """Suma población por zona para cada año proyectado y calcula crecimiento_pct."""
    ...

def rank_provinces_by_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena provincias descendentemente por crecimiento_pct."""
    ...
```

### 5. Chart Layer

```python
import plotly.graph_objects as go
import json

def build_line_chart_data(proj_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el gráfico de línea temporal.

    Returns:
        Dict con traces para cada provincia + total país, serializable a JSON.
    """
    ...

def build_bar_chart_data(ranked_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el gráfico de barras horizontales."""
    ...

def build_zone_chart_data(zone_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el gráfico de zonas."""
    ...
```

### 6. HTML Export Layer

```python
def render_html(
    line_data: dict,
    bar_data: dict,
    zone_data: dict,
    provinces: list[str],
    zone_map: dict[str, str],
    output_path: str,
) -> None:
    """Genera el archivo HTML autocontenido con todos los gráficos y la lógica JS.

    El HTML incluye:
    - Plotly.js embebido (CDN con fallback inline)
    - Datos de gráficos serializados como JSON en variables JS
    - Dropdown de filtro global
    - Lógica JS para actualizar los 3 gráficos al cambiar el filtro
    """
    ...
```

## Interfaces

### Input Interface (CSV multi-censal)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `provincia` | `str` | Nombre de la jurisdicción (exacto, 24 filas) |
| `1991` | `int` | Población censo 1991 (opcional si no disponible) |
| `2001` | `int` | Población censo 2001 (opcional si no disponible) |
| `2010` | `int` | Población censo 2010 (opcional si no disponible) |
| `2022` | `int` | Población censo 2022 (requerido como mínimo) |

Al menos una columna de año censal debe estar presente. Las columnas faltantes se ignoran.

### Internal Data Model

```python
@dataclass
class ProvinceProjection:
    """Proyección poblacional de una provincia."""
    provincia: str
    zona: str
    poblacion: dict[int, float]   # año → población proyectada
    crecimiento_pct: float         # crecimiento 2028→2035
```

### DataFrame Maestro (en memoria)

```
┌──────────────┬──────────────┬──────────┬──────────┬───┬──────────┬────────────────┐
│ provincia    │ zona         │ 2028     │ 2029     │...│ 2035     │ crecimiento_pct│
├──────────────┼──────────────┼──────────┼──────────┼───┼──────────┼────────────────┤
│ Buenos Aires │ Este/Centro  │ 18200000 │ 18350000 │...│ 19100000 │ 4.95           │
│ CABA         │ Este/Centro  │ 3100000  │ 3110000  │...│ 3180000  │ 2.58           │
│ ...          │ ...          │ ...      │ ...      │...│ ...      │ ...            │
└──────────────┴──────────────┴──────────┴──────────┴───┴──────────┴────────────────┘
```

### Modelo de Regresión Exponencial

```
P(t) = a × exp(b × t)

donde:
  - t: año (e.g., 1991, 2001, 2010, 2022, 2028..2035)
  - a, b: parámetros ajustados por scipy.optimize.curve_fit
  - Ajuste usa todos los puntos censales disponibles para la provincia
  - Si solo hay 1 punto censal, se usa tasa de crecimiento nacional promedio como b
```

## Error Handling

| Escenario | Acción | Output |
|-----------|--------|--------|
| Archivo CSV no encontrado | `sys.exit(1)` | Mensaje descriptivo en stderr |
| CSV sin columna `provincia` | `sys.exit(1)` | Mensaje descriptivo en stderr |
| CSV sin ningún año censal numérico | `sys.exit(1)` | Mensaje descriptivo en stderr |
| Provincia no reconocida en CSV | Warning en stderr, excluir fila | Continuar con provincias válidas |
| Fallo en ajuste de curva (curve_fit) | Usar tasa nacional promedio | Warning en stderr |
| División por cero en crecimiento | Retornar 0.0 | Silencioso |

## Testing Strategy

### Unit Tests
- `load_census_data`: CSV válido → DataFrame correcto
- `load_census_data`: archivo inexistente → FileNotFoundError
- `load_census_data`: CSV con menos de 4 censos → usa los disponibles
- `fit_exponential`: 4 puntos → parámetros válidos
- `format_population`: valores en cada rango → sufijo correcto
- `calculate_growth_percentage`: casos normales y división por cero

### Property Tests (hypothesis)
- Property 1: Regresión produce exactamente 8 valores positivos para 2028-2035
- Property 2: Partición de zonas es invariante (24 provincias, sin duplicados)
- Property 3: DataFrame maestro tiene exactamente 24 filas y 8 columnas de años
- Property 5: Total país = suma de provincias para cada año
- Property 6: Agregación por zona = suma de provincias miembro
- Property 7: Rankings ordenados descendentemente
- Property 10: Formato numérico correcto por rango

## Correctness Properties

### Property 1: Projection model produces valid time series
*For any* valid census data (≥1 data point, positive populations), the projection model SHALL produce exactly 8 positive values for years 2028-2035, monotonically consistent with the fitted growth rate.
**Validates: R1.3**

### Property 2: Zone partition invariant
*For any* province in the system, it SHALL belong to exactly one zone. The union of all zones SHALL equal exactly the 24 jurisdictions with no overlaps or omissions.
**Validates: R1.5**

### Property 3: Data completeness after processing
*For any* valid input, the resulting DataFrame SHALL contain exactly 24 rows with population values for all 8 projection years.
**Validates: R1.4**

### Property 5: Country total equals sum of provincial populations
*For any* projection year, the country total SHALL equal the sum of all 24 provincial populations.
**Validates: R3.2**

### Property 6: Zone aggregation equals sum of member provinces
*For any* zone and projection year, the zone population SHALL equal the sum of its member provinces.
**Validates: R5.3**

### Property 7: Growth rankings are sorted in descending order
*For any* valid dataset, provincial and zone rankings SHALL be in strictly non-increasing order of growth percentage.
**Validates: R4.2, R5.1**

### Property 10: Number formatting correctness
*For any* positive number, `format_population` SHALL return a string with suffix "M" if ≥1M, "K" if ≥1K, or plain integer otherwise.
**Validates: R6.1, R6.2**
