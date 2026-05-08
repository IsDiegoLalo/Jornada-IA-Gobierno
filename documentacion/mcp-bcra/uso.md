# Guía de Uso — Ejemplos de Prompts

## Cómo funciona la interacción

El MCP BCRA expone 4 herramientas al agente de IA. Cuando le hacés una pregunta sobre variables económicas del Banco Central, el agente decide automáticamente qué tools llamar y en qué orden. Vos solo preguntás en lenguaje natural.

## Ejemplos por categoría

### 📋 Listar variables disponibles

```
"¿Qué variables publica el BCRA?"
"¿Cuáles son las principales variables económicas disponibles?"
"Listame todo lo que puedo consultar del Banco Central"
```

**Tool invocada:** `list_variables`

---

### 🔍 Buscar variables

```
"Buscá variables relacionadas con tipo de cambio"
"¿Hay datos de inflación?"
"¿Qué variables de tasas de interés tiene el BCRA?"
"Buscá reservas"
```

**Tool invocada:** `search_variables`

---

### 📊 Último valor de una variable

```
"¿Cuánto están las reservas internacionales hoy?"
"¿Cuál es el tipo de cambio oficial actual?"
"Dame el último dato de inflación mensual"
"¿Cuánto está la tasa de política monetaria?"
```

**Tool invocada:** `get_latest_values`

---

### 📈 Serie temporal

```
"Mostrame la evolución del dólar oficial en los últimos 3 meses"
"¿Cómo evolucionaron las reservas desde enero?"
"Dame la inflación mensual de todo 2025"
"Evolución de la tasa BADLAR en el último semestre"
```

**Tool invocada:** `get_variable_data`

---

## Flujos encadenados (el agente combina tools)

### Flujo 1: Buscar y consultar

```
Usuario: "¿Cuánto está el dólar oficial hoy?"
```

El agente ejecuta:
1. `search_variables(query="tipo cambio")` → encuentra variable ID 4
2. `get_latest_values(variable_ids=[4])` → último valor

---

### Flujo 2: Análisis temporal

```
Usuario: "Mostrame cómo evolucionó la inflación mensual en 2025"
```

El agente ejecuta:
1. `search_variables(query="inflación mensual")` → encuentra variable ID 27
2. `get_variable_data(variable_id=27, desde="2025-01-01", hasta="2025-12-31")` → serie

---

### Flujo 3: Comparación de variables

```
Usuario: "Comparame la evolución del tipo de cambio oficial vs las reservas en el último trimestre"
```

El agente ejecuta:
1. `search_variables(query="tipo cambio minorista")` → ID 4
2. `search_variables(query="reservas internacionales")` → ID 1
3. `get_variable_data(variable_id=4, desde="2026-02-23", hasta="2026-05-23")`
4. `get_variable_data(variable_id=1, desde="2026-02-23", hasta="2026-05-23")`
5. Presenta ambas series para comparación

---

### Flujo 4: Resumen macroeconómico

```
Usuario: "Dame un resumen de las principales variables macro de Argentina hoy"
```

El agente ejecuta:
1. `get_latest_values(variable_ids=[1, 4, 5, 6, 15, 27, 28])` → reservas, TC, tasa, base monetaria, inflación
2. Sintetiza un resumen con todos los valores

---

## Tips para mejores resultados

| Tip | Ejemplo |
|-----|---------|
| Usá nombres descriptivos | "tipo de cambio" en vez de "variable 4" |
| Especificá el período | "últimos 3 meses" o "desde enero 2025" |
| Pedí comparaciones | "comparame X con Y" |
| Combiná con datos abiertos | "buscá datos de empleo en datos.gob.ar y cruzalos con la inflación del BCRA" |
| Pedí gráficos | "graficame la evolución del dólar" (el agente puede generar código Python) |

## Ejemplo completo — Análisis de tipo de cambio

```
Usando el MCP del BCRA, buscá la variable de tipo de cambio minorista,
traé los datos de los últimos 6 meses, y generá un script Python que
grafique la evolución con matplotlib. Guardalo como tipo_cambio.py y correlo.
```

## Limitaciones

- Los datos dependen de la disponibilidad de la API del BCRA
- La API puede tener latencia en horarios de alta demanda
- Las variables se actualizan según el calendario del BCRA (no en tiempo real)
- No incluye datos históricos anteriores a lo que la API expone
- La búsqueda es solo sobre la descripción de las variables, no sobre los datos
