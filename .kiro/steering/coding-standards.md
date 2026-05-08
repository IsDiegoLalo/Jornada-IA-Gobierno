---
inclusion: always
description: "Estándares de código: Clean Code, SOLID, PEP 8, ESLint, type hints y convenciones por lenguaje"
---

## General
- Seguir los principios de Clean Code y SOLID
- Funciones con responsabilidad única (máximo 30 líneas)
- Variables y funciones nombradas en inglés, comentarios en español si el equipo lo prefiere
- Evitar magic numbers — usar constantes con nombre

## Python
- PEP 8 estricto
- Type hints obligatorios en todas las funciones públicas
- Usar `dataclasses` o `pydantic` para modelos de datos
- Preferred formatter: `black`, linter: `ruff`

## TypeScript / JavaScript
- ESLint + Prettier obligatorio
- `strict: true` en tsconfig
- Preferir `const` sobre `let`, evitar `var`
- Async/await sobre callbacks o `.then()` encadenados

## Java
- Seguir Google Java Style Guide
- Usar `Optional` para valores que pueden ser null
- Lombock está permitido para DTOs
