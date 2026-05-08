---
inclusion: always
description: "Seguridad: mínimo privilegio IAM, código seguro, manejo de secrets y cifrado de datos"
---

## Principio de mínimo privilegio
- Roles IAM con permisos específicos — nunca usar `*` en recursos o acciones salvo justificación documentada
- Usar IAM Roles para servicios, no access keys de larga duración
- Rotar secrets cada 90 días via Secrets Manager

## Código seguro
- Validar y sanitizar TODOS los inputs del usuario
- No logear datos sensibles (PII, credenciales, tokens)
- HTTPS/TLS en todas las comunicaciones
- Dependencias: escanear con `pip-audit` (Python), `npm audit` (Node), `trivy` (containers)

## Secrets
- NUNCA commitear credenciales, tokens, o API keys al repositorio
- Usar `.env` (no commitear) + AWS Secrets Manager en producción
- Pre-commit hook obligatorio para detección de secrets (ver hooks)

## Data
- Cifrado at-rest en S3 (SSE-S3 mínimo, SSE-KMS para datos sensibles)
- Cifrado in-transit obligatorio
- Clasificar datos según sensibilidad antes de elegir el servicio de almacenamiento
