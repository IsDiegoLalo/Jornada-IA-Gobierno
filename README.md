**Jornada de IA para Gobierno para el sector público**

¡Bienvenidos al Jornada de Kiro para el Sector Público Argentino!
Organizado por la Secretaría de Innovación, Ciencia y Tecnología (SICYT), este evento busca impulsar la creación de aplicaciones útiles para la ciudadanía usando datos abiertos del Estado argentino.

> 💻 **Compatibilidad:** Este proyecto funciona en **Windows**, **macOS** y **Linux**. Incluye scripts de setup para cada plataforma.

**Objetivo del Jornada**
Construir aplicaciones prácticas y escalables que demuestren el valor de integrar datos públicos con herramientas de desarrollo avanzadas como Kiro. Los participantes podrán explorar desde la obtención de datos hasta la implementación de soluciones reales para desafíos del sector público argentino.

Al final del evento, los equipos presentarán aplicaciones que:

- Utilicen al menos un dataset público de datos.gob.ar.
- Demuestren el uso de Kiro para acelerar el desarrollo mediante su enfoque spec-driven (basado en especificaciones).
- Resuelvan un problema específico del sector público (ej: gestión de servicios, transparencia, inclusión digital).

**¿Qué es Kiro?** 
Kiro es un IDE agéntico desarrollado por AWS, basado en Code OSS, que integra inteligencia artificial directamente en el flujo de desarrollo. Sus características clave incluyen:

- Enfoque spec-driven: Convierte instrucciones en lenguaje natural en especificaciones estructuradas (requisitos, diseño técnico, tareas secuenciadas).
- Revisión y aprobación: Los desarrolladores pueden revisar y aprobar cada especificación antes de que el agente implemente los cambios en el código.
- Automatización inteligente: Ideal para prototipos rápidos y desarrollo iterativo.
- Integración con AWS: Acceso a servicios como S3, Lambda, API Gateway, entre otros.

Ejemplo de flujo en Kiro:
“Crea una API que consuma datos de incendios forestales de datos.gob.ar y los muestre en un mapa interactivo” → Kiro genera especificaciones → Tú las revisas/aprobas → El agente implementa el código.

***Datasets Públicos Disponibles*** 
Los participantes pueden utilizar cualquier dataset de datos.gob.ar. 

Algunas categorías sugeridas:
- Ambiente	Incendios forestales, calidad del aire, biodiversidad
- Salud	Hospitales públicos, vacunación, registros de enfermedades
- Educación	Matrículas escolares, instituciones educativas, becas
- Gobierno Abierto	Presupuesto público, licitaciones, tramitología
- Transporte	Red de trenes, horarios de colectivos, accidentes viales

Tip: Usa la búsqueda avanzada en datos.gob.ar para filtrar por formato (CSV, JSON, API) y licencia (públicas/CC0).

***Guía Rápida para Comenzar con Kiro***

### **Instrucciones para Descargar, Instalar y Hacer Sign-In con Kiro (Versión Gratis)**  

Aquí tienes un guía paso a paso para obtener, instalar y acceder a **Kiro** en su versión gratuita. Asegúrate de seguir cada paso cuidadosamente.

---
## **1. Descargar Kiro (Gratis)**

### **Paso 1: Acceder al Sitio Oficial**  
1. Abre tu navegador web (**Chrome, Firefox, Edge, Safari**).  
2. Ve a la página oficial de Kiro:  
   - **URL oficial**: `https://kiro.dev`  
   - *Importante*: **Nunca descargues desde sitios de terceros** (ej: Download.com, Softonic), para evitar malware.  

### **Paso 2: Navegar a "Descargar" o "Download"**  

### **Paso 3: Elegir la Versión IDE para tu Sistema Operativo**  
Kiro suele ofrecer versiones para:  
- **Windows** (archivo `.exe` o `.msi`).  
- **macOS** (archivo `.dmg`).  
- **Linux** (archivo `.tar.gz` o `.deb`/`.rpm`).
- Nota: podes bajar la version cli (linea de comando) pero en este jornada usaremos la versión IDE

> **Ejemplo**:  
> - En Windows: Haz clic en *"Download for Windows"*.  
> - En macOS: Haz clic en *"Download for Mac"*.  

---

## **2. Instalar Kiro**  

### **Para Windows**  
1. **Ejecutar el archivo descargado** (ej: `KiroSetup.exe`).  
2. Seguir el **Asistente de Instalación**:  
   - Haz clic en **"Next"** → Acepta los términos y condiciones → Elige la ruta de instalación (por defecto `C:\Program Files\Kiro`).  
   - Espera a que termine la instalación (puede tomar 1-2 minutos).  
3. **Finalizar**: Haz clic en **"Finish"**.  
   - *Opcional*: Desmarca la casilla **"Launch Kiro"** si no quieres abrirlo ahora.  

### **Para macOS**  
1. **Abrir el archivo `.dmg** descargado.  
2. Arrastrar el ícono de **Kiro** desde la ventana del disco a la carpeta **"Applications"** (en el escritorio).  
3. Cerrar la ventana del disco.  
4. **Abrir Kiro**:  
   - Ve a **Aplicaciones** → Haz clic en el ícono de Kiro.  
   - *Si aparece una advertencia de seguridad*:  
     - Ve a **Preferencias del Sistema** → **Seguridad y Privacidad** → **General** → Haz clic en *"Permitir"* junto a la aplicación descargada.  

### **Para Linux**  
#### **Opción 1: Archivo `.tar.gz`**  
1. **Descomprimir el archivo**:  
   ```bash
   tar -xzvf kiro-linux.tar.gz
   ```  
2. **Ejecutar la aplicación**:  
   ```bash
   cd kiro-linux
   ./kiro
   ```  

#### **Opción 2: Archivo `.deb` (para Ubuntu/Debian)**  
1. **Instalar con terminal**:  
   ```bash
   sudo dpkg -i kiro.deb
   ```  
2. **Arreglar errores dependientes** (si los hay):  
   ```bash
   sudo apt --fix-broken install
   ```  
3. **Abrir Kiro**:  
   - Busca la aplicación en tu menú de inicio o ejecútala desde la terminal:  
     ```bash
     kiro
     ```  
---

## **3. Hacer Sign-In (Iniciar Sesión)**  

### **Paso 1: Abrir Kiro**  
- Después de instalar, abre la aplicación desde:  
  - **Windows**: Menú Inicio → **Kiro**.  
  - **macOS**: **Aplicaciones** → **Kiro**.  
  - **Linux**: Ejecuta el archivo como se indicó arriba.  

### **Paso 2: Acceder a la Página de Iniciar Sesión**  
1. En la pantalla de inicio de Kiro, busca opciones como:  
   - **"Sign In"**, **"Log In"**, o **"Iniciar Sesión"**.  
2. Haz clic en esa opción.  

### **Paso 3: Elegir Método de Registro/Inicio**  
#### **Opción A: Con Correo Electrónico (Gratis)**  
1. Ingresa tu **correo electrónico** (ej: `tucorreo@example.com`).  
2. Crea una **contraseña segura** (mínimo 8 caracteres, con mayúsculas, números y símbolos).  
3. Haz clic en **"Sign Up"** o **"Registrarse"**.  
4. **Verifica tu correo**:  
   - Recibirás un correo de Kiro con un enlace de verificación.  
   - Haz clic en el enlace para confirmar tu cuenta.  

#### **Opción B: Con Redes Sociales (Más Rápido)**  
1. Haz clic en **"Continue with Google"**, **"Sign in with GitHub"**, o **"Continue with Microsoft"**.  
2. Inicia sesión con tu cuenta de la red elegida.  
3. ¡Listo! Kiro creará automáticamente tu cuenta gratuita.  

### **Paso 4: Seleccionar el Plan Gratis**  
- Si Kiro ofrece planes de pago, asegúrate de seleccionar:  
  - **"Free Plan"**, **"Basic"**, o **"Starter"**.  
  - *Normalmente, al usar un método de registro como Google, automáticamente entra al plan gratis*.  

### **Paso 5: Comenzar a Usar Kiro**  
- Una vez iniciada la sesión, podrás:  
  - Configurar tu perfil.  
  - Explorar las funciones básicas (gratis).  
  - Sigue los tutoriales en pantalla si están disponibles.  

---

## **⚠️ Soluciones a Problemas Comunes**  

### **1. Error al Instalar en Windows**  
- **Solución**:  
  - Desactiva el antivirus temporalmente.  
  - Ejecuta el archivo como **administrador** (clic derecho → *"Run as administrator"*).  

### **2. Error de Permisos en macOS**  
- **Solución**:  
  - Ve a **Preferencias del Sistema** → **Seguridad y Privacidad** → **General** → Haz clic en *"Permitir"* junto a la aplicación.  

### **3. No Recibes el Correo de Verificación**  
- **Solución**:  
  - Revisa la carpeta de **Spam/Reciclaje**.  
  - Asegúrate de que el correo no esté bloqueado por tu filtro anti-spam.  

### **4. Kiro No Se Abre Después de Instalar**  
- **Solución**:  
  - **Windows**: Reinicia tu PC y vuelve a abrirlo.  
  - **macOS/Linux**: Cierra todos los procesos de Kiro en la barra de tareas y vuelve a abrirlo.  

---

## **💡 Consejos Adicionales**  
- **Actualizaciones**: Kiro suele actualizarse automáticamente. Si no es así, ve a **"Acerca de Kiro"** o **"Settings"** → **"Check for Updates"**.  
- **Soporte**: Si necesitas ayuda, visita la sección de **"Help"** o **"Support"** en el sitio oficial o envía un correo a **support@kiro.com**.  
- **Privacidad**: Lee los **Términos de Servicio** y **Política de Privacidad** para entender cómo se usan tus datos.  

---

¡Con estos pasos ya puedes disfrutar de **Kiro** en su versión gratuita! 🎉 Si tienes algún problema específico, comenta y te ayudo a resolverlo.

***Tutoriales y documentación oficial***

- Documentación oficial de Kiro: https://kiro.dev/docs/
- Tutoriales espec-driven: https://www.youtube.com/@kirodotdev
- Kiro para estudiantes (1000 creditos): https://kiro.dev/students/

---

## 🇦🇷 MCP Datos Abiertos Argentina

Este repositorio incluye un **servidor MCP (Model Context Protocol)** que permite a Kiro consultar los 1,233 datasets del portal [datos.gob.ar](https://datos.gob.ar) en lenguaje natural.

### ¿Para qué sirve?

En vez de navegar manualmente el portal de datos abiertos, podés preguntarle directamente a Kiro:

> **"¿Qué datasets hay sobre educación en Argentina?"**

Y Kiro busca, filtra y te muestra los resultados relevantes usando las herramientas del MCP.

### Arquitectura básica

```
┌────────────────────┐                 ┌──────────────────────┐
│ build_index.py     │ ── HTTPS ──▶   │ datos.gob.ar         │
│ (se ejecuta 1 vez) │                 │  API CKAN v3         │
└────────┬───────────┘                 └──────────────────────┘
         │
         ▼
    index.json  (~3 MB, 1,233 datasets)
         │
         ▼
┌────────────────────┐      stdio      ┌────────────────────┐
│ main.py (MCP)      │ ◀────────────▶  │ Kiro / Claude /... │
│ búsqueda local     │                 │                    │
│ + fetch en vivo    │ ── HTTPS ──▶   │ datos.gob.ar       │
└────────────────────┘  (solo datos)   └────────────────────┘
```

**¿Cómo funciona?**
1. `build_index.py` descarga el catálogo completo una vez y genera `index.json`
2. `main.py` carga ese índice y expone 6 herramientas al agente de IA
3. La búsqueda es instantánea (local), solo la preview de datos va al portal en vivo

### Herramientas disponibles

| Tool | Qué hace |
|------|----------|
| `search_datasets` | Busca datasets por palabras clave |
| `get_dataset_info` | Metadata completa de un dataset |
| `list_dataset_resources` | Lista archivos (CSV/XLSX) con URLs |
| `query_resource_data` | Preview de filas de un CSV/XLSX |
| `list_organizations` | Entidades publicadoras del Estado |
| `index_stats` | Info del índice (fecha, cantidad) |

### Ejemplo de uso en Kiro

Después de configurar el MCP, simplemente preguntá en el chat:

```
"Busca datos sobre COVID-19 y decime qué publicó el Ministerio de Salud"
```

Kiro automáticamente:
1. Llama a `search_datasets(query="COVID-19")` → encuentra 10 datasets
2. Filtra los del Ministerio de Salud
3. Te muestra un resumen con títulos, formatos y links

### Setup rápido (1 minuto)

#### macOS / Linux
```bash
chmod +x setup.sh
./setup.sh
```

#### Windows (CMD o PowerShell)
```cmd
setup.bat
```

El script (ambas versiones hacen lo mismo):
1. Verifica que tengas Python 3.10+ instalado
2. Instala las dependencias Python (`mcp`, `httpx`, `pandas`, `openpyxl`)
3. Genera el índice si no existe
4. Crea `.kiro/settings/mcp.json` con la ruta correcta de tu máquina

> **Nota Windows:** El comando de Python en Windows es `python` (no `python3`). El `setup.bat` lo detecta automáticamente. Si Python no está en tu PATH, durante la instalación de Python marcá la casilla **"Add Python to PATH"**.

Después abrí el folder en Kiro y el MCP se conecta solo. No hay que configurar nada más.

📖 Documentación completa en [`documentacion/mcp/`](documentacion/mcp/README.md)

> 💡 **Créditos**: La idea original del MCP para datos abiertos fue de **Pablo Sierra** — AWS WWSO GTM Specialists-LATAM, quien desarrolló el [MCP de Datos Abiertos de Perú](https://github.com/deltamacuro/datos-abiertos-peru-mcp-demo) como prueba de concepto para la sesión "IA aplicada al sector público basada en datos". Esta versión para Argentina fue adaptada para el Jornada de IA para Gobierno.

---

**Instrucciones para Participantes**
***1. Formación de Equipos***
- Máximo 4 miembros por equipo.
- Cada equipo debe registrar su repositorio en GitHub con el siguiente formato:
- Jornada-IA-Gobierno-[nombre-equipo].

***2. Entregables***
- Código fuente: En un repositorio público en GitHub.
- README detallado: Incluye:
   - Descripción del problema que resuelve.
   - Datasets utilizados (con enlaces a datos.gob.ar).
   - Instrucciones para ejecutar la aplicación.
   - Capturas de pantalla del producto.
- Presentación final: 10 minutos por equipo (ver criterios de evaluación).
  
***3. Criterios de Evaluación***
- Innovación	30%
- Uso de datos públicos	10%
- Calidad técnica	20%
- Presentación	15%
- Impacto social	25%

***📅 Calendario del Jornada***
- Fecha	Actividad - Martes 19 de Mayo de 2026
- Lugar: Auditorio de la Secretaria de Ciencia y Tecnologia
  
***Agenda***
-9 a 12:  IA en AWS - clase teórica y demo de productos
-12 a 13: Almuerzo
-13 a 16: Jornada de IA para Gobierno
-16 a 17: Evaluación y entrega de premios

***❓ Soporte y Preguntas ***
Canal de Discord: #Jornada-IA-Gobierno-sicyt (enlace proporcionado al inscribirse).
Correo de contacto: jornada@sicyt.gob.ar

***📜 Licencia***
Todos los proyectos desarrollados durante el jornada deben licenciarse bajo Creative Commons Attribution 4.0 International (CC BY 4.0) para garantizar la reutilización y transparencia.

¡Construyamos juntos soluciones que transformen datos públicos en herramientas para una Argentina más innovadora y conectada! 🇦🇷✨

***Organizado por:***
- Secretaría de Innovación, Ciencia y Tecnología (SICYT) en colaboración con AWS y Partners de AWS.