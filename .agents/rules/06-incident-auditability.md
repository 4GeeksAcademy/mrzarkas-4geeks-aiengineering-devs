---
title: "Trazabilidad de las incidencias"
description: "Garantiza que los cambios de estado y responsable de una incidencia puedan reconstruirse posteriormente."
scope: project
alwaysApply: false
globs:
  - "services/**/*incident*"
  - "services/**/*incidence*"
  - "packages/**/*incident*"
  - "packages/**/*incidence*"
  - "uis/**/*incident*"
  - "uis/**/*incidence*"
---

Todo cambio de estado o responsable de una incidencia debe generar un registro de auditoría persistente.

El registro debe permitir reconstruir como mínimo:
- qué incidencia cambió;
- qué campo cambió;
- cuál era el valor anterior;
- cuál es el valor nuevo;
- quién realizó el cambio;
- cuándo se realizó.

Reglas:
- No actualices directamente el estado o el responsable mediante una operación que evite la creación del registro de auditoría.
- No elimines registros históricos de auditoría como consecuencia de actualizar una incidencia.
- La implementación debe permitir reconstruir cronológicamente el historial de cambios de estado y responsable.
