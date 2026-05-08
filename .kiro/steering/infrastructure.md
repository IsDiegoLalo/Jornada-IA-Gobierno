---
inclusion: fileMatch
fileMatchPattern: "**/*.tf,**/*.yaml,**/*.yml,**/cdk/**"
description: "IaC con Terraform y AWS CDK: módulos, estado remoto, constructs L2 y buenas prácticas"
---

# IaC – Terraform y AWS CDK

## Terraform
- Usar módulos para recursos reutilizables
- Estado remoto en S3 + DynamoDB para locking
- `terraform fmt` y `terraform validate` antes de cada PR
- Separar workspaces por ambiente (dev/staging/prod)

## AWS CDK
- Constructs de nivel 2 (L2) preferidos sobre L1
- Usar `cdk.RemovalPolicy.RETAIN` en recursos de datos en producción
- Stacks separados por dominio funcional, no por ambiente
- Validar con `cdk synth` en el pipeline de CI

## Buenas prácticas comunes
- Evitar hard-coding de Account IDs y Regions — usar `Stack.of(this).account`
- Outputs exportados para referencias cross-stack
- Revisión de `cdk diff` antes de `cdk deploy` en producción
