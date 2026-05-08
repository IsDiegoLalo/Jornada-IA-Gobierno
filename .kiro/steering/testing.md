---
inclusion: auto
description: "Estrategia de testing: pirámide de tests, herramientas por lenguaje y buenas prácticas"
---

# Estrategia de Testing

## Pirámide de tests
- Unit tests: 70% de cobertura mínima — rápidos, aislados, sin dependencias externas
- Integration tests: validar contratos entre servicios
- E2E tests: flujos críticos de negocio solamente

## Herramientas
- Python: `pytest` + `moto` para mocks de AWS
- TypeScript: `Jest` + `aws-sdk-mock`
- Java: `JUnit 5` + `Mockito` + `LocalStack` para AWS

## Buenas prácticas
- Cada función/método público debe tener al menos un test unitario
- Tests deben ser deterministas — no depender de datos externos o timestamps fijos
- Nombrar tests: `test_should_{comportamiento}_when_{condicion}`
- Mocks para servicios AWS en unit tests; LocalStack para integration tests
