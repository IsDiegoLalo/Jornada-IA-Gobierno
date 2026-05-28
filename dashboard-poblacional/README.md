# Dashboard Poblacional Argentina 2028-2035

Dashboard interactivo de proyecciones poblacionales de Argentina para el período 2028-2035, generado como un archivo HTML estático autocontenido. El script Python carga datos oficiales del INDEC, aplica regresión exponencial por provincia y produce un HTML con gráficos Plotly interactivos que el usuario abre directamente en el navegador.

## Descripción

El dashboard presenta tres visualizaciones interactivas:

- **Evolución temporal**: Gráfico de línea con la población proyectada año a año (2028-2035) para el país completo o una provincia seleccionada.
- **Ranking provincial**: Barras horizontales con las 24 jurisdicciones ordenadas por porcentaje de crecimiento proyectado.
- **Análisis por zonas**: Barras verticales con las 4 zonas geográficas (Norte, Este/Centro, Oeste, Sur) ordenadas por crecimiento.

Un dropdown en la parte superior permite filtrar todas las visualizaciones por "Argentina (País Completo)" o por cualquiera de las 24 jurisdicciones.

## Fuentes de datos

Los datos provienen de los censos nacionales de población del **INDEC (Instituto Nacional de Estadística y Censos de Argentina)**:

| Censo | Año | Fuente |
|-------|-----|--------|
| Censo Nacional de Población, Hogares y Viviendas | 1991 | INDEC |
| Censo Nacional de Población, Hogares y Viviendas | 2001 | INDEC |
| Censo Nacional de Población, Hogares y Viviendas | 2010 | INDEC |
| Censo Nacional de Población, Hogares y Viviendas | 2022 | INDEC |

Los datos están disponibles en [datos.gob.ar](https://datos.gob.ar) y en las publicaciones oficiales del INDEC.

El archivo `data/censos.csv` contiene las 24 jurisdicciones argentinas (23 provincias + CABA) con los valores de población de los 4 censos.

## Metodología de proyección

Se aplica un modelo de **regresión exponencial** de la forma:

```
P(t) = a × e^(b × t)
```

donde:
- `t` es el año
- `a` y `b` son parámetros ajustados por mínimos cuadrados no lineales (`scipy.optimize.curve_fit`)
- El ajuste utiliza **todos los puntos censales disponibles** para cada provincia (hasta 4 puntos: 1991, 2001, 2010, 2022)

**Supuestos del modelo:**
- La tasa de crecimiento histórica observada en los censos se mantiene constante en el período 2028-2035.
- Si una provincia tiene un solo punto censal disponible, se utiliza una tasa de crecimiento nacional promedio de 1.2% anual como fallback.
- Los años se normalizan internamente (restando el año mínimo) para evitar overflow numérico en el ajuste.

**Limitaciones:**
- El modelo no incorpora factores socioeconómicos, migratorios ni políticas públicas futuras.
- Las proyecciones son estimaciones basadas en tendencias históricas y no deben usarse como pronósticos oficiales.

## Instalación

Requiere Python 3.11 o superior.

```bash
# Clonar o descargar el proyecto
cd dashboard-poblacional

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Desde el directorio dashboard-poblacional/
python generate_dashboard.py
```

El script genera el archivo `dashboard.html` en el directorio actual. Abrir ese archivo en cualquier navegador web moderno.

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DASHBOARD_DATA_PATH` | Ruta al archivo CSV de datos censales | `data/censos.csv` |
| `DASHBOARD_OUTPUT_PATH` | Ruta del archivo HTML de salida | `dashboard.html` |

Ejemplo con variables de entorno personalizadas:

```bash
# Linux / macOS
DASHBOARD_DATA_PATH=/ruta/a/mis_datos.csv DASHBOARD_OUTPUT_PATH=/tmp/mi_dashboard.html python generate_dashboard.py

# Windows (PowerShell)
$env:DASHBOARD_DATA_PATH="C:\datos\censos.csv"; $env:DASHBOARD_OUTPUT_PATH="C:\output\dashboard.html"; python generate_dashboard.py
```

## Salida

El archivo `dashboard.html` generado es completamente autocontenido:
- No requiere servidor web ni conexión a internet (excepto para cargar Plotly desde CDN al abrir el HTML).
- Todos los datos de proyección están embebidos como JSON en el HTML.
- La interactividad del filtro está implementada en JavaScript puro.

## Estructura del proyecto

```
dashboard-poblacional/
├── generate_dashboard.py   # Script principal
├── requirements.txt        # Dependencias pinneadas
├── pyproject.toml          # Configuración del proyecto
├── README.md               # Este archivo
├── data/
│   └── censos.csv          # Datos censales INDEC (1991-2022)
└── tests/
    ├── __init__.py
    └── conftest.py
```

## Dependencias principales

- [plotly](https://plotly.com/python/) — Visualizaciones interactivas
- [pandas](https://pandas.pydata.org/) — Procesamiento de datos
- [scipy](https://scipy.org/) — Regresión exponencial (`curve_fit`)
- [numpy](https://numpy.org/) — Operaciones numéricas
