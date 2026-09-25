---
title: "Estructura del repositorio"
description: "Ubica el código y los componentes respetando la estructura establecida del monorepo."
scope: project
alwaysApply: false
globs:
  - "uis/**"
  - "services/**"
  - "agents/**"
  - "skills/**"
  - "mcps/**"
  - "workflows/**"
  - "packages/**"
  - "shared/**"
  - "infra/**"
  - "scripts/**"
---

Mantén la estructura existente del monorepo.

Ubicación por responsabilidad:
- `uis/`: interfaces de usuario.
- `services/`: servicios backend.
- `agents/`: agentes.
- `skills/`: skills.
- `mcps/`: servidores o integraciones MCP.
- `workflows/`: automatizaciones y orquestación.
- `packages/`: código reutilizable.
- `shared/`: recursos comunes simples.
- `infra/`: infraestructura y despliegue.
- `scripts/`: scripts operativos.

Reglas:
- No añadas código funcional nuevo en la raíz del repositorio.
- Cada componente independiente debe tener su propio `README.md`.
- Mantén `docker-compose.yml` en la raíz.
- No crees nuevas carpetas de primer nivel sin una necesidad explícita.
- Usa `_template/` como base al crear nuevos agentes o skills.
