---
title: "Historial Git incremental y revisable"
description: "Mantiene la implementación dividida en commits pequeños, coherentes y revisables."
scope: project
alwaysApply: true
---

Organiza los cambios en commits pequeños y coherentes por responsabilidad.

No concentres toda una funcionalidad en un único commit cuando implique varias responsabilidades independientes.

Cada commit debe:
- representar un cambio funcional o estructural identificable;
- mantener el repositorio en un estado coherente;
- usar un mensaje que describa el cambio realizado.

Para funcionalidades con modelo, lógica de negocio, API, interfaz y tests, separa los commits cuando esas partes puedan revisarse independientemente.

No realices squash de todos los commits salvo que se solicite explícitamente.
