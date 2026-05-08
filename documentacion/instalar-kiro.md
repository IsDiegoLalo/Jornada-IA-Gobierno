# Instalar Kiro y Autenticarse

## 1. Descargar Kiro

Ir a **https://kiro.dev** y descargar la versión para tu sistema operativo.

| Sistema | Archivo |
|---------|---------|
| Windows | `.exe` |
| macOS | `.dmg` |
| Linux | `.deb` o `.tar.gz` |

## 2. Instalar

### Windows
1. Ejecutar el `.exe` descargado
2. Seguir el asistente → Next → Next → Finish

### macOS
1. Abrir el `.dmg`
2. Arrastrar Kiro a la carpeta **Aplicaciones**
3. Si aparece advertencia de seguridad: Preferencias del Sistema → Seguridad → Permitir

### Linux (Ubuntu/Debian)
```bash
sudo dpkg -i kiro_*.deb
sudo apt --fix-broken install   # si hay errores de dependencias
```

### Linux (.tar.gz)
```bash
tar -xzvf kiro-linux.tar.gz
./kiro
```

## 3. Autenticarse con AWS Builder ID

1. Abrir Kiro
2. Hacer clic en **"Sign In"**
3. Seleccionar **"Use for Free with Builder ID"**
4. Se abre el navegador → Hacer clic en **"Create AWS Builder ID"** (si no tenés cuenta)
5. Ingresar tu email → Verificar con el código que llega al correo
6. Crear una contraseña
7. Autorizar a Kiro cuando lo pida
8. Listo — Kiro queda conectado

> **Nota:** AWS Builder ID es gratuito y no requiere tarjeta de crédito. No es lo mismo que una cuenta de AWS.

## 4. Verificar

Una vez autenticado, deberías ver tu nombre en la esquina inferior izquierda de Kiro. Podés abrir el chat con `Cmd+I` (macOS) o `Ctrl+I` (Windows/Linux) y hacer una pregunta para confirmar que funciona.
