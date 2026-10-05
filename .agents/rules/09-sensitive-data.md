---
title: "Protección de datos sanitarios sensibles"
description: "Evita exponer datos de pacientes e información sanitaria sensible en código, logs, fixtures o archivos del repositorio."
scope: project
alwaysApply: true
---

Trata los datos de pacientes y la información sanitaria como datos sensibles.

No:
- incluyas datos reales de pacientes en código fuente;
- incluyas datos reales de pacientes en fixtures, ejemplos o tests;
- escribas información sanitaria sensible de pacientes en logs;
- almacenes credenciales, tokens o secretos en el repositorio;
- uses datos reales de pacientes para ejemplos o pruebas.

Para desarrollo, ejemplos y tests utiliza únicamente datos ficticios o anonimizados.

Si una implementación requiere almacenar, transmitir o registrar información sanitaria sensible, identifica explícitamente esa circunstancia antes de implementar una solución que pueda exponerla.

No inventes requisitos específicos de HIPAA o UK GDPR que no estén definidos en `CONTEXT.md` o en los requisitos de la tarea.
