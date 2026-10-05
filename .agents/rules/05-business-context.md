---
title: "Usar el contexto de negocio de HealthCore"
description: "Utiliza CONTEXT.md como fuente de verdad para los conceptos, categorías y restricciones de negocio de HealthCore."
scope: project
alwaysApply: false
---

Cuando una tarea dependa de información de negocio de HealthCore:

1. Consulta `CONTEXT.md` antes de implementar.
2. Usa únicamente tipos, categorías, áreas, restricciones y conceptos respaldados por `CONTEXT.md` o por requisitos explícitos de la tarea.
3. No inventes valores de negocio para completar enumeraciones, modelos o reglas.
4. Si un valor necesario no aparece en `CONTEXT.md` ni en los requisitos de la tarea:
   - no lo inventes;
   - identifica explícitamente la ausencia;
   - solicita aclaración o documenta la decisión pendiente.

`CONTEXT.md` es la fuente de verdad del contexto de negocio de HealthCore.
