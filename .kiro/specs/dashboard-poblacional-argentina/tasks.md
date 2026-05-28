# Implementation Plan: Dashboard Poblacional Argentina

## Overview

Script Python (`generate_dashboard.py`) que carga datos de los últimos 4 censos nacionales (1991, 2001, 2010, 2022), ajusta regresión exponencial por provincia, y genera un archivo HTML estático autocontenido con gráficos Plotly interactivos. El dashboard se abre directamente en el navegador sin servidor.

## Tasks

- [ ] 1. Estructura del proyecto y configuración
  - [x] 1.1 Crear estructura del proyecto y dependencias
    - Crear directorio `dashboard-poblacional/`
    - Crear `dashboard-poblacional/pyproject.toml` con dependencias: plotly, pandas, scipy, numpy, python-dotenv
    - Crear `dashboard-poblacional/requirements.txt` con versiones pinneadas
    - Crear `dashboard-poblacional/data/` con placeholder
    - Crear `dashboard-poblacional/tests/__init__.py` y `tests/conftest.py`
    - Agregar pytest e hypothesis como dependencias de desarrollo
    - _Requirements: 7.1, 7.2_

  - [ ] 1.2 Implementar Configuration Layer en `generate_dashboard.py`
    - Crear `AppConfig` dataclass con campos: data_path, output_path
    - Implementar `load_config()` leyendo variables de entorno con defaults seguros
    - Definir constante `ZONAS` (dict 4 zonas → lista de provincias)
    - Definir `TODAS_LAS_PROVINCIAS` y `ANIOS_PROYECCION = list(range(2028, 2036))`
    - Verificar que las 24 jurisdicciones están asignadas sin duplicados ni omisiones
    - _Requirements: 1.5, 7.1, 7.3_

  - [ ]* 1.3 Write property test for zone partition invariant
    - **Property 2: Zone partition invariant**
    - **Validates: R1.5**

- [ ] 2. Capa de datos: carga y validación
  - [ ] 2.1 Implementar `load_census_data()` en `generate_dashboard.py`
    - Leer CSV con pandas desde path configurable (columnas: provincia + años censales)
    - Detectar automáticamente qué columnas de años censales están presentes (1991, 2001, 2010, 2022)
    - Validar que existe columna `provincia` y al menos 1 columna de año censal numérico
    - Validar que existen las 24 jurisdicciones (warning si faltan, no error fatal)
    - Lanzar `FileNotFoundError` si archivo no existe; `ValueError` si formato inválido
    - _Requirements: 1.1, 1.2, 1.4, 1.6_

  - [ ] 2.2 Implementar `validate_census_data()` en `generate_dashboard.py`
    - Verificar tipos numéricos en columnas de años
    - Verificar valores positivos en columnas de población
    - Retornar DataFrame limpio con solo las columnas válidas
    - _Requirements: 1.1, 1.6_

  - [ ] 2.3 Crear CSV de datos reales de los 4 censos
    - Crear `dashboard-poblacional/data/censos.csv` con datos reales del INDEC
    - Columnas: provincia, 1991, 2001, 2010, 2022
    - Incluir las 24 jurisdicciones con datos de los 4 censos nacionales
    - Fuente: datos oficiales INDEC (censos nacionales de población)
    - _Requirements: 1.1, 1.4_

- [ ] 3. Capa de proyección: regresión exponencial
  - [ ] 3.1 Implementar `fit_exponential()` en `generate_dashboard.py`
    - Ajustar P(t) = a × exp(b × t) usando scipy.optimize.curve_fit
    - Manejar caso de 1 solo punto censal (usar tasa nacional promedio como b)
    - Retornar tupla (a, b) de parámetros
    - _Requirements: 1.3_

  - [ ] 3.2 Implementar `project_population()` en `generate_dashboard.py`
    - Para cada provincia: ajustar curva con todos los puntos censales disponibles
    - Evaluar modelo en años 2028-2035
    - Calcular crecimiento_pct = ((pop_2035 - pop_2028) / pop_2028) * 100
    - Asignar zona a cada provincia usando `get_zona_for_provincia()`
    - Retornar DataFrame maestro: provincia, zona, 2028..2035, crecimiento_pct
    - _Requirements: 1.3, 1.5_

  - [ ] 3.3 Implementar `get_zona_for_provincia()` en `generate_dashboard.py`
    - Buscar provincia en diccionario ZONAS
    - Lanzar ValueError si no encontrada
    - _Requirements: 1.5_

  - [ ]* 3.4 Write property test for projection model validity
    - **Property 1: Projection model produces valid time series**
    - **Validates: R1.3**

  - [ ]* 3.5 Write property test for data completeness
    - **Property 3: Data completeness after processing**
    - **Validates: R1.4**

- [ ] 4. Checkpoint - Verificar carga y proyección
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Capa de transformación
  - [ ] 5.1 Implementar `format_population()` en `generate_dashboard.py`
    - >= 1_000_000 → sufijo "M" (e.g., "45.0M")
    - >= 1_000 y < 1_000_000 → sufijo "K" (e.g., "500K")
    - < 1_000 → entero sin sufijo
    - _Requirements: 6.1, 6.2_

  - [ ] 5.2 Implementar `calculate_growth_percentage()` en `generate_dashboard.py`
    - ((end - start) / start) * 100; retornar 0.0 si start == 0
    - _Requirements: 4.1, 5.1_

  - [ ] 5.3 Implementar `aggregate_by_zona()` en `generate_dashboard.py`
    - Sumar población de provincias miembro por zona para cada año 2028-2035
    - Calcular crecimiento_pct por zona
    - Retornar DataFrame: zona, 2028..2035, crecimiento_pct
    - _Requirements: 5.3_

  - [ ] 5.4 Implementar `rank_provinces_by_growth()` en `generate_dashboard.py`
    - Ordenar DataFrame descendentemente por crecimiento_pct
    - _Requirements: 4.2_

  - [ ]* 5.5 Write property test for number formatting
    - **Property 10: Number formatting correctness**
    - **Validates: R6.1, R6.2**

  - [ ]* 5.6 Write property test for zone aggregation
    - **Property 6: Zone aggregation equals sum of member provinces**
    - **Validates: R5.3**

  - [ ]* 5.7 Write property test for ranking order
    - **Property 7: Growth rankings are sorted in descending order**
    - **Validates: R4.2, R5.1**

- [ ] 6. Checkpoint - Verificar transformaciones
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Capa de gráficos y exportación HTML
  - [ ] 7.1 Implementar `build_line_chart_data()` en `generate_dashboard.py`
    - Construir traces Plotly para total país y cada provincia (2028-2035)
    - Serializar a JSON para embeber en HTML
    - Eje Y con tickvals/ticktext en Formato_Abreviado
    - _Requirements: 3.1, 3.4, 6.3_

  - [ ] 7.2 Implementar `build_bar_chart_data()` en `generate_dashboard.py`
    - Barras horizontales ordenadas por crecimiento descendente
    - Incluir colores: color base para todas, color highlight para provincia seleccionada
    - Serializar a JSON
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 7.3 Implementar `build_zone_chart_data()` en `generate_dashboard.py`
    - Barras verticales por zona ordenadas por crecimiento descendente
    - Serializar a JSON
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 7.4 Implementar `render_html()` en `generate_dashboard.py`
    - Template HTML con Plotly CDN
    - Embeber datos JSON de los 3 gráficos como variables JS
    - Embeber mapa provincia→zona como variable JS
    - Dropdown de filtro global con "Argentina (País Completo)" + 24 provincias
    - Lógica JS: al cambiar filtro → actualizar los 3 gráficos con Plotly.react()
    - Lógica JS: filtro provincia → highlight en barras + mostrar solo su zona
    - Escribir archivo HTML en output_path
    - _Requirements: 2.1, 2.2, 2.3, 7.1, 7.6_

- [ ] 8. Punto de entrada y wiring final
  - [ ] 8.1 Implementar bloque `if __name__ == "__main__"` en `generate_dashboard.py`
    - Cargar config → cargar datos → validar → proyectar → transformar → generar HTML
    - Manejo de errores con mensajes descriptivos en stderr y sys.exit(1)
    - Imprimir ruta del archivo generado al finalizar exitosamente
    - _Requirements: 1.6, 7.1, 7.6_

  - [ ] 8.2 Crear README.md del proyecto dashboard
    - Documentar fuentes de datos (INDEC censos 1991, 2001, 2010, 2022)
    - Documentar metodología de regresión exponencial y supuestos
    - Instrucciones de instalación (pip install) y ejecución (python generate_dashboard.py)
    - Variables de entorno configurables (DASHBOARD_DATA_PATH, DASHBOARD_OUTPUT_PATH)
    - _Requirements: 7.4, 7.5_

- [ ] 9. Final checkpoint - Verificación completa
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property tests
- El script principal es `generate_dashboard.py` (no `app.py`)
- No se usa Dash — solo Plotly + pandas + scipy para generar HTML estático
- La interactividad del filtro se implementa en JavaScript puro dentro del HTML
- El CSV de entrada tiene columnas: provincia, 1991, 2001, 2010, 2022
- Formato de código: black + ruff, type hints obligatorios (PEP 8)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "2.1"] },
    { "id": 3, "tasks": ["2.2", "2.3"] },
    { "id": 4, "tasks": ["3.1"] },
    { "id": 5, "tasks": ["3.2", "3.3"] },
    { "id": 6, "tasks": ["3.4", "3.5", "5.1", "5.2"] },
    { "id": 7, "tasks": ["5.3", "5.4"] },
    { "id": 8, "tasks": ["5.5", "5.6", "5.7", "7.1"] },
    { "id": 9, "tasks": ["7.2", "7.3"] },
    { "id": 10, "tasks": ["7.4"] },
    { "id": 11, "tasks": ["8.1"] },
    { "id": 12, "tasks": ["8.2"] }
  ]
}
```
