# Requirements Document

## Introduction

Dashboard interactivo de proyecciones poblacionales de Argentina para el período 2028-2035, generado como un archivo HTML estático autocontenido mediante un script Python que utiliza Plotly y pandas. El sistema consume datos oficiales del INDEC correspondientes a los últimos 4 censos nacionales de población (1991, 2001, 2010 y 2022) disponibles en datos.gob.ar, y aplica un modelo de regresión exponencial ajustado a todos los puntos censales disponibles para generar proyecciones. Presenta visualizaciones interactivas de evolución temporal, ranking provincial por crecimiento y análisis por zonas geográficas. El usuario abre el archivo HTML resultante directamente en un navegador sin necesidad de servidor.

## Glossary

- **Dashboard**: Archivo HTML estático autocontenido con visualizaciones interactivas generadas por Plotly, que el usuario abre directamente en un navegador web
- **Script_Generador**: Script Python único que carga datos censales, calcula proyecciones y genera el archivo HTML estático del Dashboard
- **INDEC**: Instituto Nacional de Estadística y Censos de Argentina, fuente oficial de datos censales
- **Censos_Nacionales**: Conjunto de los últimos 4 censos nacionales de población de Argentina (1991, 2001, 2010 y 2022) utilizados como puntos de datos para el modelo de proyección
- **Regresión_Exponencial**: Modelo matemático que ajusta una curva exponencial P(t) = a × e^(b×t) a los puntos de datos de los Censos_Nacionales para estimar población futura
- **Proyección_Poblacional**: Estimación de la cantidad de habitantes futura basada en la Regresión_Exponencial ajustada a los datos de los Censos_Nacionales
- **Filtro_Global**: Componente selector (dropdown) dentro del HTML que permite elegir entre "Argentina (País Completo)" o una provincia específica, implementado con interactividad JavaScript de Plotly
- **Gráfico_Línea_Temporal**: Visualización de tipo línea que muestra la evolución poblacional año a año en el período 2028-2035
- **Gráfico_Barras_Provincial**: Visualización de barras horizontales que muestra todas las provincias ordenadas de mayor a menor porcentaje de crecimiento
- **Gráfico_Zonas**: Visualización que consolida métricas poblacionales en las 4 zonas geográficas definidas
- **Zona_Norte**: Agrupación geográfica que incluye Jujuy, Salta, Tucumán, Catamarca, La Rioja, Santiago del Estero, Chaco, Formosa, Corrientes y Misiones
- **Zona_Este_Centro**: Agrupación geográfica que incluye Buenos Aires, CABA, Córdoba, Santa Fe y Entre Ríos
- **Zona_Oeste**: Agrupación geográfica que incluye Mendoza, San Juan y San Luis
- **Zona_Sur**: Agrupación geográfica que incluye La Pampa, Neuquén, Río Negro, Chubut, Santa Cruz y Tierra del Fuego
- **Formato_Abreviado**: Representación numérica que abrevia valores grandes usando sufijos (e.g., "45M" para 45 millones, "500K" para 500 mil)
- **HTML_Autocontenido**: Archivo HTML que incluye todo el código JavaScript y datos necesarios para funcionar sin dependencias externas ni servidor

## Requirements

### Requirement 1: Carga y procesamiento de datos poblacionales multi-censal

**User Story:** Como usuario del Dashboard, quiero que el sistema utilice datos de los últimos 4 censos nacionales de Argentina para generar proyecciones más precisas mediante regresión exponencial, para que las visualizaciones reflejen una tendencia histórica fundamentada.

#### Acceptance Criteria

1. WHEN el Script_Generador se ejecuta, THE Script_Generador SHALL cargar datos poblacionales de los Censos_Nacionales (1991, 2001, 2010 y 2022) desde una fuente configurable mediante variable de entorno.
2. IF el archivo de datos contiene menos de 4 censos, THEN THE Script_Generador SHALL utilizar todos los censos disponibles en el archivo para ajustar el modelo de Regresión_Exponencial.
3. WHEN los datos de los Censos_Nacionales están cargados, THE Script_Generador SHALL ajustar un modelo de Regresión_Exponencial P(t) = a × e^(b×t) a los puntos censales de cada provincia para generar Proyección_Poblacional en el período 2028-2035.
4. THE Script_Generador SHALL incluir datos para las 24 jurisdicciones de Argentina (23 provincias y CABA).
5. THE Script_Generador SHALL asignar cada provincia a exactamente una de las cuatro zonas definidas: Zona_Norte, Zona_Este_Centro, Zona_Oeste o Zona_Sur.
6. IF la fuente de datos no está disponible o el archivo es inválido, THEN THE Script_Generador SHALL terminar la ejecución con un mensaje de error descriptivo en la salida estándar indicando el problema de carga.

### Requirement 2: Filtro global de selección geográfica

**User Story:** Como usuario del Dashboard, quiero filtrar las visualizaciones por país completo o por provincia específica, para que pueda analizar datos a distintos niveles de granularidad.

#### Acceptance Criteria

1. THE Dashboard SHALL presentar un Filtro_Global en la parte superior de la interfaz con la opción "Argentina (País Completo)" seleccionada por defecto.
2. THE Filtro_Global SHALL listar las 24 jurisdicciones argentinas como opciones seleccionables además de "Argentina (País Completo)".
3. WHEN el usuario selecciona una opción en el Filtro_Global, THE Dashboard SHALL actualizar el Gráfico_Línea_Temporal, el Gráfico_Barras_Provincial y el Gráfico_Zonas para reflejar la selección.

### Requirement 3: Gráfico de evolución temporal

**User Story:** Como usuario del Dashboard, quiero ver la evolución poblacional en un gráfico de línea para el período 2028-2035, para que pueda identificar tendencias de crecimiento.

#### Acceptance Criteria

1. THE Dashboard SHALL mostrar un Gráfico_Línea_Temporal con el eje X representando los años 2028 a 2035 y el eje Y representando la población.
2. WHEN el Filtro_Global tiene seleccionado "Argentina (País Completo)", THE Gráfico_Línea_Temporal SHALL mostrar la curva de población total del país.
3. WHEN el Filtro_Global tiene seleccionada una provincia específica, THE Gráfico_Línea_Temporal SHALL mostrar la curva de población de esa provincia.
4. THE Gráfico_Línea_Temporal SHALL mostrar valores de población en Formato_Abreviado en el eje Y.

### Requirement 4: Gráfico de ranking provincial por crecimiento

**User Story:** Como usuario del Dashboard, quiero ver un ranking de provincias ordenado por porcentaje de crecimiento, para que pueda comparar el dinamismo demográfico entre jurisdicciones.

#### Acceptance Criteria

1. THE Dashboard SHALL mostrar un Gráfico_Barras_Provincial con barras horizontales representando el porcentaje de crecimiento poblacional de cada provincia en el período 2028-2035.
2. THE Gráfico_Barras_Provincial SHALL ordenar las provincias dinámicamente de mayor a menor porcentaje de crecimiento.
3. WHEN el Filtro_Global tiene seleccionada una provincia específica, THE Gráfico_Barras_Provincial SHALL resaltar visualmente la provincia seleccionada dentro del ranking completo.

### Requirement 5: Gráfico de análisis por zonas geográficas

**User Story:** Como usuario del Dashboard, quiero ver métricas consolidadas por zona geográfica, para que pueda comparar el crecimiento entre regiones del país.

#### Acceptance Criteria

1. WHEN el Filtro_Global tiene seleccionado "Argentina (País Completo)", THE Dashboard SHALL mostrar el Gráfico_Zonas con las 4 zonas (Zona_Norte, Zona_Este_Centro, Zona_Oeste, Zona_Sur) ordenadas por porcentaje de crecimiento.
2. WHEN el Filtro_Global tiene seleccionada una provincia específica, THE Dashboard SHALL mostrar en el Gráfico_Zonas únicamente la zona a la que pertenece la provincia seleccionada.
3. THE Gráfico_Zonas SHALL consolidar la población de todas las provincias pertenecientes a cada zona para calcular las métricas de crecimiento.

### Requirement 6: Formato de visualización de valores numéricos

**User Story:** Como usuario del Dashboard, quiero que los valores poblacionales grandes se muestren en formato abreviado, para que las visualizaciones sean legibles y fáciles de interpretar.

#### Acceptance Criteria

1. THE Dashboard SHALL mostrar valores de población iguales o superiores a 1.000.000 en Formato_Abreviado con sufijo "M" (e.g., "45M" para 45.000.000).
2. THE Dashboard SHALL mostrar valores de población entre 1.000 y 999.999 en Formato_Abreviado con sufijo "K" (e.g., "500K" para 500.000).
3. THE Dashboard SHALL aplicar el Formato_Abreviado en los ejes y etiquetas de todos los gráficos que muestren valores absolutos de población.

### Requirement 7: Arquitectura y estándares de código

**User Story:** Como desarrollador, quiero que el proyecto siga estándares de código definidos y genere un archivo HTML estático autocontenido, para que sea mantenible, reproducible y fácil de distribuir.

#### Acceptance Criteria

1. THE Script_Generador SHALL implementarse como un único archivo Python que utiliza Plotly y pandas para generar un HTML_Autocontenido con las visualizaciones interactivas del Dashboard.
2. THE Script_Generador SHALL seguir el estándar PEP 8, utilizar type hints en todas las funciones públicas, y ser compatible con el formateador black y el linter ruff.
3. THE Script_Generador SHALL obtener rutas a archivos de datos y configuraciones mediante variables de entorno, sin credenciales ni rutas hardcodeadas en el código fuente.
4. THE Script_Generador SHALL incluir un archivo README documentando las fuentes de datos utilizadas (Censos_Nacionales 1991, 2001, 2010, 2022), instrucciones de ejecución y dependencias del proyecto.
5. THE Script_Generador SHALL documentar en el README la metodología de Regresión_Exponencial y los supuestos aplicados para la Proyección_Poblacional.
6. WHEN el Script_Generador se ejecuta exitosamente, THE Script_Generador SHALL generar un archivo HTML_Autocontenido que funciona sin servidor web ni dependencias externas al abrirse en un navegador.
