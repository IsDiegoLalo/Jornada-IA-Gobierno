# Tips Prácticos para Kiro

Guía rápida de atajos y funcionalidades útiles de Kiro para sacarle el máximo provecho durante el jornada.

---

## 📄 Preview de Markdown

| Acción | Mac | Linux | Windows |
|--------|-----|-------|---------|
| Preview en pestaña nueva | `⌘ + Shift + V` | `Ctrl + Shift + V` | `Ctrl + Shift + V` |
| Preview lado a lado (split) | `⌘ + K, V` | `Ctrl + K, V` | `Ctrl + K, V` |

---

## 💬 Chat con Kiro

| Acción | Mac | Linux | Windows |
|--------|-----|-------|---------|
| Abrir chat de Kiro | `⌘ + Shift + I` | `Ctrl + Shift + I` | `Ctrl + Shift + I` |
| Referenciar un archivo en el chat | Escribir `#File` y seleccionar | Escribir `#File` y seleccionar | Escribir `#File` y seleccionar |
| Referenciar un folder | Escribir `#Folder` y seleccionar | Escribir `#Folder` y seleccionar | Escribir `#Folder` y seleccionar |
| Ver problemas del archivo actual | Escribir `#Problems` en el chat | Escribir `#Problems` en el chat | Escribir `#Problems` en el chat |
| Ver terminal en contexto | Escribir `#Terminal` en el chat | Escribir `#Terminal` en el chat | Escribir `#Terminal` en el chat |
| Ver diff de Git | Escribir `#Git Diff` en el chat | Escribir `#Git Diff` en el chat | Escribir `#Git Diff` en el chat |
| Adjuntar imagen | Arrastrar imagen al chat o click en 📎 | Arrastrar imagen al chat o click en 📎 | Arrastrar imagen al chat o click en 📎 |
| Adjuntar documento (PDF, DOCX) | Arrastrar archivo al chat o click en 📎 | Arrastrar archivo al chat o click en 📎 | Arrastrar archivo al chat o click en 📎 |

---

## 🔍 Navegación y Búsqueda

| Acción | Mac | Linux | Windows |
|--------|-----|-------|---------|
| Command Palette | `⌘ + Shift + P` | `Ctrl + Shift + P` | `Ctrl + Shift + P` |
| Buscar archivo por nombre | `⌘ + P` | `Ctrl + P` | `Ctrl + P` |
| Buscar texto en todo el proyecto | `⌘ + Shift + F` | `Ctrl + Shift + F` | `Ctrl + Shift + F` |
| Ir a definición | `F12` | `F12` | `F12` |
| Ir a símbolo en archivo | `⌘ + Shift + O` | `Ctrl + Shift + O` | `Ctrl + Shift + O` |
| Ir a línea | `⌘ + G` | `Ctrl + G` | `Ctrl + G` |

---

## ✏️ Edición

| Acción | Mac | Linux | Windows |
|--------|-----|-------|---------|
| Mover línea arriba/abajo | `⌥ + ↑/↓` | `Alt + ↑/↓` | `Alt + ↑/↓` |
| Duplicar línea | `⌥ + Shift + ↑/↓` | `Alt + Shift + ↑/↓` | `Alt + Shift + ↑/↓` |
| Eliminar línea | `⌘ + Shift + K` | `Ctrl + Shift + K` | `Ctrl + Shift + K` |
| Comentar/descomentar línea | `⌘ + /` | `Ctrl + /` | `Ctrl + /` |
| Multi-cursor | `⌥ + Click` | `Alt + Click` | `Alt + Click` |
| Seleccionar siguiente ocurrencia | `⌘ + D` | `Ctrl + D` | `Ctrl + D` |
| Renombrar símbolo | `F2` | `F2` | `F2` |
| Formatear documento | `⌥ + Shift + F` | `Alt + Shift + F` | `Alt + Shift + F` |

---

## 📐 Paneles y Layout

| Acción | Mac | Linux | Windows |
|--------|-----|-------|---------|
| Toggle sidebar | `⌘ + B` | `Ctrl + B` | `Ctrl + B` |
| Toggle terminal | `` ⌘ + ` `` | `` Ctrl + ` `` | `` Ctrl + ` `` |
| Nuevo terminal | `` ⌘ + Shift + ` `` | `` Ctrl + Shift + ` `` | `` Ctrl + Shift + ` `` |
| Split editor | `⌘ + \` | `Ctrl + \` | `Ctrl + \` |
| Cerrar pestaña | `⌘ + W` | `Ctrl + W` | `Ctrl + W` |
| Cambiar entre pestañas | `⌘ + 1/2/3...` | `Ctrl + 1/2/3...` | `Ctrl + 1/2/3...` |

---

## 🤖 Funcionalidades de IA en Kiro

### Specs (Desarrollo guiado por especificación)

Las Specs son la forma estructurada de construir features en Kiro:

1. **Crear una spec**: Desde el Command Palette → "Create Spec"
2. **Iterar**: Kiro te guía por requirements → design → tasks
3. **Implementar**: El agente trabaja task por task según la spec

> 💡 **Tip**: Siempre empezá con una spec antes de codear. Es el approach "spec-first" que Kiro promueve.

### Steering (Reglas del proyecto)

Los steering files en `.kiro/steering/` guían el comportamiento de Kiro:

- `inclusion: always` — Se incluye en toda interacción
- `inclusion: fileMatch` — Se incluye solo cuando trabajás con ciertos archivos
- `inclusion: manual` — Se incluye solo cuando lo referenciás con `#` en el chat

### Hooks (Automatización)

Los hooks ejecutan acciones automáticas ante eventos:

- **Ver hooks**: Explorer → sección "Agent Hooks"
- **Crear hook**: Command Palette → "Open Kiro Hook UI"
- **Eventos disponibles**: fileEdited, fileCreated, promptSubmit, agentStop, preToolUse, postToolUse

### MCP (Model Context Protocol)

Servidores MCP extienden las capacidades de Kiro:

- **Configurar**: Editar `.kiro/settings/mcp.json`
- **Ver estado**: Command Palette → buscar "MCP"
- **Reconectar**: Los servidores se reconectan automáticamente al cambiar la config

---

## 🚀 Tips para el Jornada

1. **Usá `#File` en el chat** para dar contexto específico a Kiro sobre qué archivo querés modificar
2. **Arrastrá imágenes** (mockups, diagramas) al chat para que Kiro entienda lo que querés construir
3. **Pedí specs** antes de implementar features complejas
4. **Usá el MCP de datos abiertos** preguntando en lenguaje natural sobre datos del Estado argentino
5. **Revisá los steering** en `.kiro/steering/` para entender las convenciones del proyecto
6. **Preview de Markdown** (`⌘/Ctrl + Shift + V`) para leer la documentación con formato
7. **Multi-cursor** (`⌥/Alt + Click`) para editar múltiples líneas a la vez
8. **Modo Autopilot** para que Kiro implemente cambios sin pedir confirmación en cada paso
9. **Modo Supervised** cuando querés revisar cada cambio antes de aplicarlo

---

## 🔧 Troubleshooting rápido

| Problema | Solución |
|----------|----------|
| Kiro no responde | Recargar ventana: `⌘/Ctrl + Shift + P` → "Reload Window" |
| MCP no conecta | Verificar `.kiro/settings/mcp.json` y reconectar desde panel MCP |
| Steering no se aplica | Verificar front-matter (`inclusion`, `description`) en el .md |
| Chat lento | Cerrar pestañas innecesarias, reducir archivos abiertos |
| Preview MD no muestra tablas | Asegurarse de que las tablas tengan el header separator (`|---|`) |
