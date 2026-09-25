---
title: "Convenciones del backend Python"
description: "Mantiene el backend FastAPI centralizado y las convenciones establecidas para la gestión de dependencias Python."
scope: project
alwaysApply: false
globs:
  - "services/**/*.py"
  - "packages/**/*.py"
  - "shared/**/*.py"
  - "scripts/**/*.py"
  - "pyproject.toml"
  - "uv.lock"
---

El backend del proyecto está inicialmente centralizado sobre FastAPI.

Reglas:
- Añade nuevas funcionalidades backend al servicio FastAPI existente cuando pertenezcan al mismo dominio funcional.
- No crees un microservicio nuevo sin que la tarea lo requiera explícitamente.
- No dividas funcionalidad existente en microservicios por preferencia arquitectónica.
- Gestiona las dependencias Python mediante `uv`.
- No introduzcas un segundo gestor de dependencias Python.

Si consideras necesario introducir un microservicio, documenta primero la propuesta en `memory-bank/proposals.md`.
