# Tasks — hito documental

Rama features/telemetryDesignPlan. Dependencias ordenadas; ningún paso instrumenta aplicaciones.

## TASK-TEL-001 — Inspección y baseline

Objetivo: specs.md — matriz baseline. Requisitos: TEL-FR-001–039. Dependencia: ninguna. Archivos afectados: specs.md — matriz baseline.

Pasos: Leer contexto en orden; verificar continuidad services/central-api → backend/app mediante main.py, Dockerfile, Compose e historial; inspeccionar modelos, Git y discrepancias. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: specs.md — matriz baseline y comandos de validation-report.md. Riesgos: R02,R07. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-002 — Identificación de métricas obligatorias

Objetivo: traceability-matrix.md — fuentes obligatorias. Requisitos: TEL-FR-001–005,023,024,032,035–037. Dependencia: TASK-TEL-001. Archivos afectados: traceability-matrix.md — fuentes obligatorias.

Pasos: Extraer cinco obligaciones del ejercicio y seis grupos del briefing; registrar procedencia. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: traceability-matrix.md — fuentes obligatorias y comandos de validation-report.md. Riesgos: R06,R09. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-003 — Mapa del flujo de inventario

Objetivo: telemetry-plan.md — Inventory Instrumentation Map. Requisitos: TEL-FR-001–012. Dependencia: TASK-TEL-002. Archivos afectados: telemetry-plan.md — Inventory Instrumentation Map.

Pasos: Contrastar INV-AC e inexistencia de código; mapear pasos, fallos y commits futuros. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — Inventory Instrumentation Map y comandos de validation-report.md. Riesgos: R02. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-004 — Descubrimiento de eventos adicionales

Objetivo: telemetry-plan.md — Cross-Application Event Catalog. Requisitos: TEL-FR-006–039. Dependencia: TASK-TEL-003. Archivos afectados: telemetry-plan.md — Cross-Application Event Catalog.

Pasos: Relacionar superficies auth, UI, API, operaciones y KPIs con hipótesis/decisión. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — Cross-Application Event Catalog y comandos de validation-report.md. Riesgos: R05,R06. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-005 — Envelope y correlación

Objetivo: telemetry-plan.md — Event Envelope. Requisitos: TEL-DATA-001–003, TEL-SEC-002–003. Dependencia: TASK-TEL-004. Archivos afectados: telemetry-plan.md — Event Envelope.

Pasos: Precisar autoridad de IDs, nulos, región, timestamps y dedup. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — Event Envelope y comandos de validation-report.md. Riesgos: R04,R08. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-006 — Diseño de contratos por evento

Objetivo: event-schemas.json — definitions. Requisitos: TEL-DATA-001, TEL-NFR-004. Dependencia: TASK-TEL-005. Archivos afectados: event-schemas.json — definitions.

Pasos: Enumerar tipos, required, enums y additionalProperties false. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: event-schemas.json — definitions y comandos de validation-report.md. Riesgos: R01,R08. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-007 — Clasificación stream/batch

Objetivo: telemetry-plan.md — Stream vs Batch. Requisitos: TEL-NFR-001,003. Dependencia: TASK-TEL-006. Archivos afectados: telemetry-plan.md — Stream vs Batch.

Pasos: Relacionar urgencia, consumidor, ventana y coste; identificar targets propuestos. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — Stream vs Batch y comandos de validation-report.md. Riesgos: R05,R09. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-008 — Seguridad y privacidad

Objetivo: telemetry-plan.md — Data Privacy & Security. Requisitos: TEL-SEC-001–004. Dependencia: TASK-TEL-007. Archivos afectados: telemetry-plan.md — Data Privacy & Security.

Pasos: Excluir PHI/secretos; separar región y marcar revisiones Claire pendientes. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — Data Privacy & Security y comandos de validation-report.md. Riesgos: R01,R04. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-009 — Arquitectura conceptual

Objetivo: plan.md — decisión arquitectónica. Requisitos: TEL-NFR-001–004. Dependencia: TASK-TEL-008. Archivos afectados: plan.md — decisión arquitectónica.

Pasos: Comparar OTel, broker, batch y outbox; definir límites y fallos. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: plan.md — decisión arquitectónica y comandos de validation-report.md. Riesgos: R03,R07. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-010 — Riesgos y exclusiones

Objetivo: telemetry-plan.md — Riesgos & Exclusions. Requisitos: TEL-SEC-001–004, TEL-NFR-002,003. Dependencia: TASK-TEL-009. Archivos afectados: telemetry-plan.md — Riesgos & Exclusions.

Pasos: Enumerar probabilidad, impacto, propietario y eventos descartados. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — Riesgos & Exclusions y comandos de validation-report.md. Riesgos: R01–R09. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-011 — Consolidación del plan final

Objetivo: telemetry-plan.md — todas las secciones. Requisitos: TEL-FR-001–039 y controles. Dependencia: TASK-TEL-010. Archivos afectados: telemetry-plan.md — todas las secciones.

Pasos: Unificar catálogo, fuentes, decisiones y política; conservar estado PROPOSED. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V06 revisión documental de sección indicada. Evidencia requerida: telemetry-plan.md — todas las secciones y comandos de validation-report.md. Riesgos: R01–R09. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-012 — Generación del JSON Schema

Objetivo: event-schemas.json — oneOf y envelope. Requisitos: TEL-DATA-001–003. Dependencia: TASK-TEL-011. Archivos afectados: event-schemas.json — oneOf y envelope.

Pasos: Serializar contratos y referencias sin añadir dependencias. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V01–V05, V08 draft-07 completo y V06 revisión. Evidencia requerida: event-schemas.json — oneOf y envelope y comandos de validation-report.md. Riesgos: R08. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-013 — Validación cruzada

Objetivo: traceability-matrix.md — todas las filas. Requisitos: TEL-DATA-001, TEL-NFR-004,005. Dependencia: TASK-TEL-012. Archivos afectados: traceability-matrix.md — todas las filas.

Pasos: Comprobar JSON, vocabulario, nombres, cobertura y casos sintéticos negativos. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V01–V05, V08 draft-07 completo y V06 revisión. Evidencia requerida: traceability-matrix.md — todas las filas y comandos de validation-report.md. Riesgos: R08. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

## TASK-TEL-014 — Revisión de entrega

Objetivo: validation-report.md — matriz AC-01–10. Requisitos: Todos los TEL-FR, TEL-DATA, TEL-SEC y TEL-NFR. Dependencia: TASK-TEL-013. Archivos afectados: validation-report.md — matriz AC-01–10.

Pasos: Revisar todos los archivos, scope y comandos; emitir estado limitado a diseño. Aceptación: artefacto indicado presente, consistente con fuentes y sin cambios de aplicación. Validación: V01–V05, V08 draft-07 completo y V06 revisión. Evidencia requerida: validation-report.md — matriz AC-01–10 y comandos de validation-report.md. Riesgos: R01–R09. Estado: DONE (documentación; futuras aprobaciones no ejecutadas).

Quality Gate 3: 14 objetivos documentales, relacionados con requisitos y evidencia; implementación futura fuera de alcance.
