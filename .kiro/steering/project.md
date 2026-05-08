---
inclusion: always
description: "Contexto del Jornada de IA para Gobierno: APIs oficiales, principios de desarrollo, stack recomendado y recursos"
---

**Jornada de IA para Gobierno — Contexto General del Proyecto**

***Descripción***

Este repositorio contiene los desafíos del Jornada de IA para Gobierno organizado en colaboración con la Dirección Nacional de Datos e Información Pública de Argentina. Los equipos participantes construirán productos de datos usando datasets públicos de datos.gob.ar y las APIs oficiales de la Dirección.

***Objetivo general***

Desarrollar aplicaciones útiles para la ciudadanía usando datos abiertos del Estado argentino, aprovechando las capacidades de Kiro como IDE con IA integrada para acelerar el desarrollo spec-first.

***APIs de soporte oficiales***

***API Series de Tiempo***

* URL base: https://datos.gob.ar/dataset/jgm-base-series-tiempo-administracion-publica-nacional/archivo/jgm_3.13
* Uso: Consulta de series temporales de datos públicos argentinos
* Casos de uso en este jornada: ver el folder casos, alli tendras de detalles de sugerencias de casos para desarrollar pero puedes usar tu imaginación para crear tu propio caso de uso
  
***Datos Espaciales de Argentina***

* URL base: https://www.idera.gob.ar/
* Uso: Normalización y georreferenciación de datos geográficos argentinos (provincias, departamentos, municipios, localidades)
* Catalogo de metadatos: http://catalogo.idera.gob.ar/geonetwork/
* Casos de uso en este jornada: ver el folder casos, alli tendras de detalles de sugerencias de casos para desarrollar pero puedes usar tu imaginación para crear tu propio caso de uso
Fuentes de datos: https://github.com/idera


***Principios de desarrollo***

* Usar las specs de Kiro como punto de partida — no comenzar a codear sin leer la spec del caso
* Usar los agentes de Kiro para implementar requerimientos funcionales descritos en la spec
* Preferir datos configurables — los paths a CSVs y endpoints de APIs deben estar en variables de entorno o archivos de config, nunca hardcodeados
* Normalizar geografía siempre con API Georef antes de cruzar datasets de distintas fuentes
* Documentar en el README cómo correr el proyecto y las fuentes de datos utilizadas


***Stack recomendado***

* Python: Streamlit o Dash para dashboards · Folium para mapas
* JavaScript: React + Leaflet.js para mapas interactivos · D3.js para visualizaciones
* IA: AWS Bedrock para funcionalidades de lenguaje natural
* Datos: pandas / polars para procesamiento de CSVs


***Contacto y recursos***

* Repositorio del jornada: https://github.com/Eduvilascoder/Jornada-IA-Gobierno
* Organización: Dirección Nacional de Datos e Información Pública
* Soporte técnico durante el evento: a traves de los facilitadores de AWS y partners de AWS.

