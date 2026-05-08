# Guía de Uso — Ejemplos de Prompts

## Cómo funciona la interacción

El MCP expone 6 herramientas al agente de IA. Cuando le hacés una pregunta sobre datos públicos argentinos, el agente decide automáticamente qué tools llamar y en qué orden. Vos solo preguntás en lenguaje natural.

## Ejemplos por categoría

### 🔍 Búsqueda de datasets

```
"¿Qué datasets hay sobre educación en Argentina?"
"Busca datos de transporte público"
"¿Hay información sobre COVID-19?"
"Datos de presupuesto del sector público"
"¿Qué publica el ENACOM?"
```

**Tool invocada:** `search_datasets`

---

### 📋 Detalle de un dataset

```
"Dame más información sobre el dataset de precios SEPA"
"¿Cuál es la licencia del dataset de casos COVID?"
"¿Quién publica el dataset de estadísticas educativas?"
```

**Tool invocada:** `get_dataset_info`

---

### 📁 Listar recursos de un dataset

```
"¿Qué archivos tiene el dataset de precios SEPA?"
"Mostrame los recursos disponibles del dataset de transporte"
"¿En qué formatos están los datos de salud?"
```

**Tool invocada:** `list_dataset_resources`

---

### 📊 Preview de datos

```
"Trae las primeras 10 filas del CSV de precios"
"Mostrame una preview del archivo de estadísticas"
"¿Qué columnas tiene ese CSV?"
```

**Tool invocada:** `query_resource_data`

---

### 🏛️ Organizaciones publicadoras

```
"¿Cuántas entidades publican datos abiertos?"
"Lista los organismos que publican en datos.gob.ar"
"¿Qué ministerios tienen datasets?"
```

**Tool invocada:** `list_organizations`

---

### 📈 Estado del índice

```
"¿Cuántos datasets tiene el catálogo?"
"¿Cuándo se actualizó el índice?"
"Dame estadísticas del portal"
```

**Tool invocada:** `index_stats`

---

## Flujos encadenados (el agente combina tools)

### Flujo 1: Explorar y previsualizar

```
Usuario: "Busca datos sobre inflación y mostrame las primeras filas del CSV más relevante"
```

El agente ejecuta:
1. `search_datasets(query="inflación")` → encuentra datasets
2. `list_dataset_resources(dataset_id="...")` → obtiene URLs de archivos
3. `query_resource_data(resource_url="...csv", rows=10)` → preview

---

### Flujo 2: Investigar una entidad

```
Usuario: "¿Qué publica el Ministerio de Salud? Dame detalles del dataset más reciente"
```

El agente ejecuta:
1. `search_datasets(query="ministerio salud")` → lista datasets
2. `get_dataset_info(dataset_id="...")` → metadata completa del más reciente

---

### Flujo 3: Análisis exploratorio

```
Usuario: "Necesito datos de empleo. Buscá qué hay, mostrame las columnas del CSV principal y decime si sirve para un análisis por provincia"
```

El agente ejecuta:
1. `search_datasets(query="empleo")` → encuentra opciones
2. `list_dataset_resources(dataset_id="...")` → identifica el CSV
3. `query_resource_data(resource_url="...", rows=5)` → inspecciona estructura
4. Analiza columnas y responde si hay datos por provincia

---

## Tips para mejores resultados

| Tip | Ejemplo |
|-----|---------|
| Usá palabras clave específicas | "precios supermercado" en vez de "economía" |
| Mencioná la entidad si la conocés | "datos del INDEC sobre pobreza" |
| Pedí preview para entender la estructura | "mostrame las primeras filas" |
| Combiná búsqueda + análisis | "busca datos de X y decime qué columnas tiene" |
| Preguntá por formatos | "¿en qué formato están los datos de Y?" |

## Limitaciones

- La búsqueda es sobre metadata (título, descripción, tags), no sobre el contenido de los archivos
- Preview de datos limitado a archivos CSV/XLSX de hasta 20 MB
- El índice es un snapshot; datasets muy nuevos pueden no estar hasta regenerar
- No soporta archivos ZIP, PDF, ni APIs en vivo (solo metadata)


## Ejemplo de Uso mas completo - Turismo 

Usa el MCP de datos abiertos de Argentina. Busca datasets sobre turismo en Argentina, trae un preview del CSV y genera un script Python que grafique la evolucion mensual de llegadas internacionales. Guardalo como Turismo.py y correlo

