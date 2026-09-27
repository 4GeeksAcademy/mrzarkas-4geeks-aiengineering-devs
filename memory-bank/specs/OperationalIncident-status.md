# OperationalIncident — Status

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Especificación:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md)  
**Tareas:** [`OperationalIncident-tasks.md`](./OperationalIncident-tasks.md)  
**Implementación:** [`OperationalIncident-implementation.md`](./OperationalIncident-implementation.md)  
**Decisión de catálogos:** [`OperationalIncident-catalogs-decision.md`](./OperationalIncident-catalogs-decision.md)  
**Decisiones de fase:** [`OperationalIncident-initial-decisions.md`](./OperationalIncident-initial-decisions.md)  
**Modelo de Fase 1:** [`OperationalIncident-phase1-data-model.md`](./OperationalIncident-phase1-data-model.md)  
**Migraciones y seeds de Fase 1:** [`OperationalIncident-migrations-seeds.md`](./OperationalIncident-migrations-seeds.md)  
**Última actualización:** 2026-09-26  
**Estado global:** Fase inicial cerrada de forma condicionada; Fase 1 en progreso; esqueleto de API iniciado, módulo de incidencias no iniciado

## 1. Decisión

Sí es necesario mantener este documento separado. La especificación define qué debe hacer el sistema; `OperationalIncident-tasks.md` desglosa el trabajo; `OperationalIncident-implementation.md` explica cómo llevarlo a cabo; este documento registra el avance verificable, decisiones abiertas, bloqueos y evidencias.

No contiene requisitos nuevos. Si una decisión cambia el alcance o el comportamiento, primero debe actualizarse `OperationalIncident-specs.md` y después reflejarse aquí.

## 2. Resumen de avance

| Área | Estado | Observación |
|---|---|---|
| Especificación funcional | Completada | Disponible en `OperationalIncident-specs.md` |
| Configuración de catálogos | Propuesta preparada | Identificadores estables y etiquetas provisionales documentados; falta validación |
| Estados, permisos, datos y auditoría | Diseñados | Consolidado en `OperationalIncident-initial-decisions.md`; falta aprobación de responsables |
| Persistencia PostgreSQL | Migraciones de catálogos e incidencia implementadas | SQLAlchemy async, Alembic, tablas de catálogo e `operational_incident`; ejecución contra PostgreSQL gestionado pendiente |
| Contratos Pydantic | Diseñados | Falta crear el módulo FastAPI |
| API FastAPI | Incidencias básicas implementadas | API central con `/health`, catálogos y alta/listado/detalle de incidencias; conexión de base pendiente |
| Backoffice | No iniciado | No existe UI del gestor |
| Auditoría e historiales | Diseñados | Falta implementar y probar transacciones |
| Pruebas | No iniciadas | No hay suite específica del módulo |
| Piloto | No iniciado | Depende de implementación y revisión de seguridad |

## 2.1 Estado de fases

| Fase | Estado | Progreso verificable | Criterio para cerrar |
|---|---|---|---|
| Fase inicial — configuración y decisiones | **Cerrada condicionada** | Diseño y propuestas documentados; validaciones formales diferidas | Revisar aprobaciones antes de producción |
| Fase 1 — PostgreSQL y modelo | **En progreso** | Diseño relacional y configuración SQLAlchemy/Alembic preparados; falta ejecutar contra PostgreSQL | Esquema, migraciones, restricciones y restauración validados |
| Fase 2 — API FastAPI | Pendiente | Sin código de API | Contratos, endpoints, autorización y pruebas validados |
| Fase 3 — Backoffice | Pendiente | Sin UI | Flujos, permisos y consumo de catálogos validados |
| Fase 4 — Pruebas y migrabilidad | Pendiente | Sin suite específica | Pruebas críticas y migraciones ejecutadas con evidencia |
| Fase 5 — Piloto y operación | Pendiente | Sin piloto | Piloto aprobado y criterios operativos cumplidos |

> La Fase inicial se cierra aquí de forma condicionada para permitir avanzar, no como aprobación funcional o normativa. Las validaciones pendientes siguen siendo obligatorias antes de producción y se tratarán como controles de salida de la Fase 1.

## 3. Entregables documentales

- [x] Especificación funcional.
- [x] Diseño de configuración de catálogos.
- [x] Diseño de persistencia PostgreSQL.
- [x] Desglose de tareas.
- [x] Estrategia de implementación.
- [x] Criterios de aceptación.
- [x] Registro inicial de estado.
- [x] Consolidación de decisiones de estados, permisos, datos, auditoría y PostgreSQL.
- [x] Diseño relacional inicial de Fase 1 y criterios de salida.
- [x] Configuración inicial de SQLAlchemy async y Alembic basada en `DATABASE_URL`.
- [x] Migración `0002_create_catalog_tables` y seed idempotente de los cuatro catálogos provisionales.
- [x] Endpoint de lectura de catálogos activos y vigentes.
- [x] Pruebas iniciales de catálogos y contrato Pydantic.
- [x] Modelo, migración y endpoints básicos de `OperationalIncident`.

## 4. Decisiones confirmadas en diseño

- [x] `OperationalIncident` es la entidad principal.
- [x] El backend será un módulo de la API centralizada FastAPI.
- [x] La persistencia inicial será PostgreSQL gestionado.
- [x] Pydantic validará los contratos de entrada y salida.
- [x] Los catálogos tendrán identificadores estables y etiquetas configurables.
- [x] Los valores inactivos no se utilizarán en nuevas incidencias, pero permanecerán disponibles para históricos.
- [x] Los cambios de estado y responsable tendrán historial con autor y marca temporal.
- [x] La UI no decidirá reglas de transición ni utilizará etiquetas hardcodeadas.
- [x] No se crearán microservicios prematuramente.

## 5. Decisiones pendientes

- [ ] Confirmar el formato físico final de versionado de `catalog` y `catalog_value`.
- [x] Confirmar herramienta de migraciones: Alembic integrado con SQLAlchemy.
- [x] Confirmar ubicación prevista: API centralizada bajo `services/`; `docker-compose.yml` en la raíz.
- [x] Confirmar configuración local inicial mediante `.env` ignorado por Git y variables de entorno.
- [ ] Confirmar la instancia PostgreSQL gestionada, backups, retención y secretos.
- [ ] Confirmar los permisos y roles de la aplicación.
- [ ] Validar el catálogo inicial de canales, tipos, severidades y estados. Propuesta preparada en `OperationalIncident-catalogs-decision.md`.
- [ ] Confirmar la matriz de transiciones.
- [ ] Confirmar qué estados tienen `isOpen = true`.
- [ ] Confirmar reglas de escalado a `ComplianceReview`.
- [ ] Confirmar tratamiento de incidencias multi-jurisdicción.
- [ ] Confirmar límites de texto y estrategia de control de PHI.
- [ ] Confirmar propietario y mecanismo de validación de las referencias maestras de clínica, reportante, sistema afectado y área responsable.

Documento consolidado: [`OperationalIncident-initial-decisions.md`](./OperationalIncident-initial-decisions.md). Las decisiones documentadas allí siguen siendo propuestas hasta que se añada evidencia de aprobación.

Estas decisiones no bloquean la preparación documental ni el diseño inicial. Sí deben resolverse antes de una puesta en producción o de fijar contratos de negocio definitivos.

## 5.1 Cierre condicionado de la fase inicial

Se autoriza iniciar la Fase 1 con decisiones provisionales. La validación formal queda diferida y no se considera completada.

| Orden | Frente | Estado | Evidencia requerida |
|---:|---|---|---|
| 1 | Formato e identificadores de catálogos | Diferido | [`OperationalIncident-catalogs-decision.md`](./OperationalIncident-catalogs-decision.md); validar antes de producción |
| 2 | Estados, transiciones e `isOpen` | Diferido | Matriz en `OperationalIncident-initial-decisions.md`; validar antes de producción |
| 3 | Permisos y responsabilidades | Diferido | Matriz en `OperationalIncident-initial-decisions.md`; validar antes de producción |
| 4 | Política de datos y no-PHI | Diferido | Reglas en `OperationalIncident-initial-decisions.md`; validar antes de producción |
| 5 | Auditoría y retención | Diferido | Eventos definidos; validar retención y acceso antes de producción |
| 6 | PostgreSQL y migraciones | En Fase 1 | Herramienta confirmada; concretar proveedor, RPO/RTO y restauración |

La fase se considera **cerrada de forma condicionada**, no validada definitivamente: la documentación permite comenzar el trabajo técnico, pero no autoriza producción ni elimina las revisiones pendientes.

### Avance registrado

- Se preparó la propuesta de catálogos y valores provisionales.
- Se documentaron identificadores estables y reglas de activación.
- Se documentó la propiedad `isOpen` para los estados.
- La validación funcional y de Cumplimiento queda diferida y es obligatoria antes de producción.
- Se consolidaron propuestas de transiciones, permisos, no-PHI, auditoría y recuperación.

### Evidencia que debe recopilarse

- Decisión o aprobación registrada por Tecnología.
- Revisión de Cumplimiento para datos, auditoría y accesos.
- Matrices de estados y permisos con versión y fecha.
- Decisión sobre PostgreSQL gestionado, migraciones, backups y restauración.
- Actualización de este documento después de cada revisión.

## 6. Bloqueos actuales

1. Existe un esqueleto FastAPI, pero todavía no hay módulo de incidencias, UI, autenticación ni base de datos implementados.
2. Alembic y SQLAlchemy están integrados, pero aún no se han ejecutado contra PostgreSQL gestionado.
3. `CONTEXT.md` no fija los valores definitivos de canal, tipo, severidad ni estado.
4. No existe aún una matriz aprobada de permisos, SLA o transiciones.
5. No existe evidencia de aprobación formal por parte de Tecnología, Cumplimiento ni las áreas funcionales; este punto queda como control de salida.

## 7. Próximo incremento recomendado — Fase 1

1. Ejecutar la migración base contra PostgreSQL con `DATABASE_URL`.
2. Crear la migración inicial de catálogos y los seeds provisionales.
3. Crear los modelos Pydantic y las pruebas de contrato.
4. Implementar alta, listado y detalle.
5. Añadir auditoría y transacciones.
6. Implementar estados, asignaciones e historiales.
7. Implementar filtros y resumen por severidad.
8. Construir el backoffice.
9. Mantener una lista de validaciones diferidas y resolverla antes de producción.
10. Actualizar este documento después de cada incremento con evidencia verificable.

### Trabajo iniciado

- Diseño relacional documentado en [`OperationalIncident-phase1-data-model.md`](./OperationalIncident-phase1-data-model.md).
- Secuencia y comportamiento de migraciones/seeds documentados en [`OperationalIncident-migrations-seeds.md`](./OperationalIncident-migrations-seeds.md).
- Esqueleto en `services/central-api/` con `/health`, `uv.lock` y `docker-compose.yml` en raíz. Prueba HTTP local: 200 y `{"status":"ok"}`. Arranque con Docker pendiente de verificar por falta de Docker en este entorno.
- SQLAlchemy async y Alembic configurados en `services/central-api/`; la migración base `0001_initial_schema` está preparada y requiere `DATABASE_URL` para ejecutarse.
- La ejecución contra PostgreSQL, pruebas de idempotencia con una base real y pruebas de restauración siguen pendientes.

## 8. Evidencia y registro de cambios

| Fecha | Cambio | Evidencia | Responsable |
|---|---|---|---|
| 2026-09-26 | Se separaron specs, tasks, implementation y status | Documentos presentes en `memory-bank/specs/` | HealthCore Digital |
| 2026-09-26 | Se definieron configuración de catálogos y PostgreSQL | `OperationalIncident-specs.md` | HealthCore Digital |
| 2026-09-26 | Se preparó la propuesta inicial de catálogos | `OperationalIncident-catalogs-decision.md`; validación pendiente | HealthCore Digital |
| 2026-09-26 | Se consolidaron las decisiones de fase inicial | `OperationalIncident-initial-decisions.md`; aprobaciones pendientes | HealthCore Digital |
| 2026-09-26 | Se autorizó avanzar a Fase 1 con decisiones provisionales | Cierre condicionado; validaciones transferidas a controles de salida | HealthCore Digital |
| 2026-09-26 | Se preparó el modelo relacional de Fase 1 | `OperationalIncident-phase1-data-model.md`; implementación pendiente | HealthCore Digital |
| 2026-09-26 | Se confirmaron Alembic/SQLAlchemy, Docker Compose en raíz y configuración por variables de entorno | `conventions.md`, `OperationalIncident-migrations-seeds.md`; implementación pendiente | HealthCore Digital |
| 2026-09-26 | Se creó el esqueleto ejecutable de la API centralizada | `services/central-api/`, `docker-compose.yml`; `/health` comprobado localmente, Docker no disponible | HealthCore Digital |
| 2026-09-26 | Se configuraron SQLAlchemy async y Alembic | `app/core/config.py`, `app/db/`, `alembic/`, `alembic.ini`; ejecución contra PostgreSQL pendiente | HealthCore Digital |
| 2026-09-26 | Se implementaron tablas de catálogos y seed idempotente | `0002_create_catalog_tables.py`, `app/db/models/catalog.py`, `app/catalogs/seed.py`; compilación e historial Alembic validados localmente | HealthCore Digital |
| 2026-09-26 | Se añadió lectura API de catálogos y pruebas iniciales | `app/catalogs/router.py`, `app/catalogs/schemas.py`, `tests/test_catalogs.py`; 3 pruebas pasando | HealthCore Digital |
| 2026-09-26 | Se implementaron modelo y API básica de incidencias | `0003_create_operational_incident.py`, `app/incidents/`; pruebas y compilación locales validadas | HealthCore Digital |

## 9. Regla de actualización

Actualizar este documento cuando ocurra cualquiera de estos eventos:

- Se complete una tarea P0, P1 o P2.
- Se tome una decisión pendiente.
- Se modifique una migración o un contrato.
- Se detecte un bloqueo.
- Se ejecute una prueba relevante.
- Se realice una revisión de seguridad o Cumplimiento.

Cada actualización debe incluir fecha, estado y evidencia concreta; no se marcará como completada una tarea únicamente por haberla diseñado.
