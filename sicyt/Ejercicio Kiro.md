Propuestas de ejercicios - Kiro - Datos Abiertos



Kiro - Datos Abiertos

Caso 1: Monitor de transporte público SUBE - Dashboard de viajes por línea, hora y zona geográfica

a)     Datasets fuente
- SUBE — Transacciones por fecha (datos.transporte.gob.ar) - CSV actualizado con usos diarios 2023–2025 · ~2M filas/año
- Viajes SUBE — día hábil promedio RMBA - Incluye trenes, subtes, colectivos · georeferenciado por línea
b)    Prompt de inicio en Kiro: “Construir un panel de control que muestre el uso del transporte público SUBE por línea y hora utilizando un CSV desde S3. Incluir un gráfico de barras por hora, un mapa de las rutas principales y un filtro por rango de fechas."
 
Caso 2: Mapa de cobertura de salud pública - Geovisualización de hospitales, centros de salud y cobertura por región

a)     Dataset fuente
- Establecimientos de salud por provincia (datos.salud.gob.ar) - Hospitales, CAPS, clínicas · coordenadas lat/lon · nivel de complejidad
- Indicadores de salud por departamento - Mortalidad infantil, vacunación, tasa de médicos/hab por provincia
b)    Prompt de inicio en Kiro "Construir un mapa de cobertura sanitaria para Argentina. Cargar un CSV con ubicaciones de hospitales e indicadores sanitarios por provincia. Mostrar marcadores en un mapa de Leaflet, codificados por color según el nivel de cobertura. Añadir una barra lateral con estadísticas al hacer clic en una provincia."


Caso 3: Análisis comparativo temporal y territorial de la superficie cultivada según cultivo.
a)	Dataset fuente: Series históricas de la superficie sembrada, superficie cosechada, producción y rendimiento de distintos cultivos en la Argentina desde principios del siglo XX a 2026.

b)	Prompt de inicio en Kiro "Construir un dashboard que permita graficar, mapear y comparar la evolución de las superficies cultivadas a nivel departamento según tipo de cultivo.

Caso 4: Mapeo interactivo de producción de hidrocarburos en Argentina.

a)	Dataset fuente: Transporte, producción de hidrocarburos y medidores de petróleo y gas

b)	Prompt de inicio en Kiro “Desarrollar una herramienta de exploración visual de la evolución de la matriz productiva de hidrocarburos, incluyendo un mapa con los datos georreferenciados de transporte y producción”.
