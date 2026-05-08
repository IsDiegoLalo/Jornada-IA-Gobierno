# Contribuir al MCP Datos Abiertos Argentina

¡Gracias por tu interés en contribuir! Este proyecto es parte del Jornada de IA para Gobierno.

## Cómo contribuir

1. **Fork** del repositorio
2. **Clonar** tu fork: `git clone https://github.com/TU-USUARIO/Jornada-IA-Gobierno.git`
3. **Crear branch**: `git checkout -b feature/mi-mejora`
4. **Instalar dependencias**: `pip install -e ".[dev]"`
5. **Hacer cambios** y escribir tests
6. **Correr tests**: `pytest tests/ -v`
7. **Commit**: `git commit -m 'Agrega mi mejora'`
8. **Push**: `git push origin feature/mi-mejora`
9. **Abrir Pull Request** contra `main`

## Estándares de código

- Python 3.10+ con type hints
- PEP 8 (enforced por `ruff`)
- Tests para toda funcionalidad nueva
- Documentar funciones públicas con docstrings

## Ideas para contribuir

- Agregar soporte para la API de Series de Tiempo
- Integrar con API Georef para normalización geográfica
- Mejorar el algoritmo de búsqueda (fuzzy matching, sinónimos)
- Agregar tool de validación de calidad de datos
- Mejorar la documentación con más ejemplos
- Traducir documentación al inglés

## Reportar bugs

Abrí un issue en GitHub con:
- Descripción del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Versión de Python y sistema operativo

## Código de conducta

Sé respetuoso y constructivo. Este es un proyecto educativo y colaborativo.
