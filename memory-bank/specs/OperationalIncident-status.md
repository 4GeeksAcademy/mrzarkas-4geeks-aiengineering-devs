# OperationalIncident — Status

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Especificación:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md)  
**Tareas:** [`OperationalIncident-tasks.md`](./OperationalIncident-tasks.md)  
**Implementación:** [`OperationalIncident-implementation.md`](./OperationalIncident-implementation.md)  
**Decisión de catálogos:** [`OperationalIncident-catalogs-decision.md`](./OperationalIncident-catalogs-decision.md)  
**Decisiones de fase:** [`OperationalIncident-initial-decisions.md`](./OperationalIncident-initial-decisions.md)  
**Modelo de Fase 1:** [`OperationalIncident-phase1-data-model.md`](./OperationalIncident-phase1-data-model.md)  
**Migraciones y seeds de Fase 1:** [`OperationalIncident-migrations-seeds.md`](./OperationalIncident-migrations-seeds.md)  
**Maestros externos:** [`OperationalIncident-external-masters.md`](./OperationalIncident-external-masters.md)
**Última actualización:** 2026-09-28
**Estado global:** Prototipo técnico pre-MVP. Fase inicial cerrada de forma condicionada; Fase 1 parcialmente implementada y pendiente de validación en PostgreSQL local; Fase 2 parcialmente implementada en API; Fases 3 a 5 no iniciadas.

## 1. Decisión

Sí es necesario mantener este documento separado. La especificación define qué debe hacer el sistema; `OperationalIncident-tasks.md` desglosa el trabajo; `OperationalIncident-implementation.md` explica cómo llevarlo a cabo; este documento registra el avance verificable, decisiones abiertas, bloqueos y evidencias.

No contiene requisitos nuevos. Si una decisión cambia el alcance o el comportamiento, primero debe actualizarse `OperationalIncident-specs.md` y después reflejarse aquí.

## 2. Resumen de avance

| Área | Estado | Observación |
|---|---|---|
| Especificación funcional | Completada | Disponible en `OperationalIncident-specs.md` |
| Configuración de catálogos | Propuesta preparada | Identificadores estables y etiquetas provisionales documentados; falta validación |
| Estados, permisos, datos y auditoría | Diseñados | Consolidado en `OperationalIncident-initial-decisions.md`; falta aprobación de responsables |
| Persistencia PostgreSQL | Parcialmente validada localmente | Migraciones para catálogos, incidencia, historiales y fundación de maestros compartidos. Un PostgreSQL temporal vacío validó instalación limpia; otro entorno temporal validó restauración de un dump, migración idempotente y 18 pruebas. Faltan validación de referencias, servicio gestionado, backups operativos y RPO/RTO. |
| Contratos Pydantic | Parcialmente implementados | Existen contratos de creación, edición, listado, detalle, transición, historial y auditoría; faltan contratos de asignación, métricas y referencias maestras. |
| API FastAPI | Parcialmente implementada | Existen catálogos, alta validada contra maestros, listado resumido, detalle, edición, transición, asignación/reasignación, historiales, auditoría, métricas y JWT propio. Dirección sólo puede consultar listados resumidos y métricas. Faltan `ComplianceReview` y administración de catálogos. |
| Backoffice | No iniciado | No existe UI del gestor |
| Auditoría e historiales | Parcialmente implementados | Se persisten historiales de estado y asignación, y eventos de creación, edición, transición y asignación en la misma operación; falta revisar minimización/retención. |
| Pruebas | Parcialmente validadas localmente | Hay pruebas de catálogos, JWT/roles, HTTP de autenticación/autorización y flujos de incidencias. El servicio reproducible `test` de Podman ejecuta 18 pruebas contra PostgreSQL local; la imagen de producción permanece sin dependencias de desarrollo. |
| Piloto | No iniciado | Depende de implementación y revisión de seguridad |

## 2.1 Estado de fases

| Fase | Estado | Progreso verificable | Criterio para cerrar |
|---|---|---|---|
| Fase inicial — configuración y decisiones | **Cerrada condicionada** | Diseño y propuestas documentados; validaciones formales diferidas | Revisar aprobaciones antes de producción |
| Fase 1 — PostgreSQL y modelo | **En progreso** | Tablas y migraciones de catálogos, incidencias, historiales y maestros compartidos implementadas; instalación limpia, seed, restauración y pruebas verificadas | Cargar maestros aprobados y aplicar validación/restricciones; decidir servicio gestionado, backups y RPO/RTO |
| Fase 2 — API FastAPI | **En progreso** | Endpoints y contratos básicos, JWT temporal, autorización por capacidades e historial/auditoría implementados | Completar asignación, métricas, `ComplianceReview`, catálogos y pruebas HTTP/integración |
| Fase 3 — Backoffice | Pendiente | Sin UI | Flujos, permisos y consumo de catálogos validados |
| Fase 4 — Pruebas y migrabilidad | **En progreso** | Migración idempotente, seed y 14 pruebas superadas contra PostgreSQL local | Suite crítica automatizada, reconstrucción desde esquema vacío y restauración verificadas |
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
- [x] Migración de historial de estado y auditoría (`0004_history_audit`).
- [x] Autenticación JWT temporal y autorización por capacidades para desarrollo local.

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
- [x] Disponer de entorno local con PostgreSQL mediante Podman.
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

1. El backoffice no está implementado.
2. Faltan `ComplianceReview` y administración de catálogos.
3. Los maestros compartidos existen con fixtures sintéticos de jurisdicción, áreas y sistemas, pero las incidencias aún aceptan UUID sin validación real; faltan clínicas aprobadas y el vínculo de reportante a identidad.
4. El JWT propio se mantiene como mecanismo vigente. La emisión libre de tokens sólo está habilitada en `development` y `test`; los despliegues compartidos deben establecer explícitamente `APP_ENVIRONMENT=staging` o `production`.
5. Falta la decisión de servicio gestionado, backups operativos y RPO/RTO para entornos no locales.
6. `CONTEXT.md` no fija los valores definitivos de canal, tipo, severidad ni estado, y no existe una matriz aprobada de permisos, SLA o transiciones.
7. No existe evidencia de aprobación formal por parte de Tecnología, Cumplimiento ni las áreas funcionales; este punto queda como control de salida.

## 7. Próximo incremento recomendado — Fase 1

1. Ejecutar en el PostgreSQL local de Podman, desde una base limpia, las migraciones, el seed y la suite de integración; registrar la evidencia.
2. Completar la asociación con `ComplianceReview`.
3. Aplicar validación de clínica, reportante, jurisdicción, sistema afectado y área responsable conforme a `OperationalIncident-external-masters.md`; cargar maestros aprobados antes de piloto.
4. Fijar el contrato público de rutas antes de construir clientes: la implementación usa `/incidents` y `/catalogs`, mientras el diseño propone `/operational-incidents`.
5. Construir el backoffice consumiendo catálogos desde API.
6. Completar las revisiones de Tecnología, Cumplimiento y áreas funcionales, especialmente capacidades de Tecnología y Cumplimiento; `admin` se mantiene como rol técnico y el JWT propio permanece vigente hasta que una decisión aprobada requiera cambiarlo.

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
| 2026-09-28 | Se completó parcialmente el flujo técnico de incidencias | `0004_add_incident_history_and_audit.py`, endpoints de edición, transición, historial y auditoría; JWT temporal y roles en `app/auth/` | HealthCore Digital |
| 2026-09-28 | Se registró el entorno de desarrollo local | Proyecto montado en Podman con PostgreSQL; `api` y `postgres` activos y Alembic comprobado en `0004_history_audit` (head) tras limpiar datos | HealthCore Digital |
| 2026-09-28 | Se validaron migración idempotente y seed en PostgreSQL local | `alembic upgrade head` sin cambios pendientes; `seed-catalogs` ejecutado; `entryChannel:6`, `incidentStatus:9`, `incidentType:9`, `severity:4`, `incidents:0` | HealthCore Digital |
| 2026-09-28 | Se detectó bloqueo de ejecución de pruebas en la imagen API | `uv run pytest -q` devolvió `no tests ran` y exit 5: el `Dockerfile` usa `uv sync --no-dev` y no copia `tests/` | HealthCore Digital |
| 2026-09-28 | Se validó la suite actual contra PostgreSQL local | Contenedor API preparado temporalmente con `pytest` y `tests/`; `uv run pytest -q`: 14 passed en 0.38 s | HealthCore Digital |
| 2026-09-28 | Se implementaron asignación y su historial | Migración `0005_assignment_history`; `POST /incidents/{id}/assignments`, `GET /incidents/{id}/assignment-history`, auditoría transaccional y 14 pruebas superadas | HealthCore Digital |
| 2026-09-28 | Se implementó el resumen de abiertas por severidad | `GET /incidents/metrics/open-by-severity` calcula desde `incidentStatus.isOpen`; cobertura añadida y 14 pruebas superadas contra PostgreSQL local | HealthCore Digital |
| 2026-09-28 | Se automatizó la ejecución de pruebas en Podman | Target `test` en `services/central-api/Dockerfile` y servicio con perfil `test`; `podman compose --profile test run --rm --build test`: 14 passed en 1.56 s | HealthCore Digital |
| 2026-09-28 | Se restringió la emisión libre de JWT por entorno | `POST /auth/tokens` responde 404 fuera de `development` y `test`; cobertura añadida y `podman compose --profile test run --rm --build test`: 15 passed en 1.05 s | HealthCore Digital |
| 2026-09-28 | Se centralizó la autorización contextual | `app/auth/policies.py` concentra alcance por área, filtros de listado y autorización de transiciones; routers refactorizados y 15 pruebas superadas | HealthCore Digital |
| 2026-09-28 | Se añadieron pruebas HTTP de autenticación | Cobertura de token ausente, inválido y emisor bloqueado en producción; `httpx` sólo en dependencias de desarrollo y 17 pruebas superadas | HealthCore Digital |
| 2026-09-28 | Se desplegaron localmente las mejoras de seguridad | `podman compose up -d --build api`; servicios `api` y `postgres` activos | HealthCore Digital |
| 2026-09-28 | Se resolvió la advertencia del cliente HTTP de pruebas | `TestClient` sustituido por `httpx.AsyncClient` con `ASGITransport`; `podman compose --profile test run --rm --build test`: 17 passed sin advertencias | HealthCore Digital |
| 2026-09-28 | Se validaron límites HTTP de autorización | Área propia: 200; área ajena: 403; auditoría para área responsable: 403; auditoría para Cumplimiento: 200; asignación para Tecnología: 403. Se liberó el pool async por prueba y la suite terminó con 18 passed | HealthCore Digital |
| 2026-09-28 | Se restringió Dirección a datos resumidos | `GET /incidents` excluye descripción, reportante, `ComplianceReview` y metadatos de auditoría; Dirección obtiene 403 en `GET /incidents/{id}`; 18 pruebas superadas | HealthCore Digital |
| 2026-09-28 | Se confirmó la conservación de `admin` | El rol técnico `admin` se mantiene para soporte y administración; discrepancia y código actualizados | HealthCore Digital |
| 2026-09-28 | Se verificó instalación limpia de PostgreSQL | Proyecto temporal aislado: migraciones `0001`→`0005`, seed y 18 pruebas superadas; contenedor, red y volumen temporales eliminados al finalizar | HealthCore Digital |
| 2026-09-28 | Se verificó restauración de PostgreSQL | Dump de la base local restaurado en proyecto temporal aislado; Alembic confirmó `0005_assignment_history` y `upgrade head` idempotente; 18 pruebas superadas. Entorno y dumps temporales eliminados | HealthCore Digital |
| 2026-09-28 | Se definió arquitectura de maestros externos | `OperationalIncident-external-masters.md`: datos de referencia compartidos, reportante derivado de identidad y `ComplianceReview` como dominio de Cumplimiento | HealthCore Digital |
| 2026-09-28 | Se implementó la fundación de maestros compartidos | Migración `0006_reference_data`, modelos y seed sintético de jurisdicciones, áreas y sistemas; API reconstruida y 18 pruebas superadas | HealthCore Digital |
| 2026-09-28 | Se estabilizaron fixtures sintéticos de maestros | UUID deterministas para 5 áreas y 6 sistemas US/UK; seed ejecutado dos veces sin duplicados y 6 relaciones sistema–jurisdicción verificadas | HealthCore Digital |
| 2026-09-28 | Se creó helper de fixtures de referencia para pruebas | `tests/reference_fixtures.py` resuelve por `key` los UUID sintéticos de clínica, jurisdicción, sistema y área | HealthCore Digital |
| 2026-09-28 | Se migraron pruebas de incidencias a maestros sintéticos | Creación, reasignación y autorización HTTP usan fixtures US/UK y áreas estables; `podman compose --profile test run --rm --build test`: 18 passed | HealthCore Digital |
| 2026-09-28 | Se activó validación de maestros en incidencias | Creación valida clínica/jurisdicción/sistema/área; edición y asignación validan área activa; `reporter_id` deriva del actor JWT; migración `0007` añade FKs y suite: 18 passed | HealthCore Digital |
| 2026-09-28 | Se cubrieron incompatibilidades US/UK | Clínica US con jurisdicción UK y sistema UK en incidencia US devuelven `422`; suite Podman: 18 passed sin advertencias | HealthCore Digital |

## 9. Regla de actualización

Actualizar este documento cuando ocurra cualquiera de estos eventos:

- Se complete una tarea P0, P1 o P2.
- Se tome una decisión pendiente.
- Se modifique una migración o un contrato.
- Se detecte un bloqueo.
- Se ejecute una prueba relevante.
- Se realice una revisión de seguridad o Cumplimiento.

Cada actualización debe incluir fecha, estado y evidencia concreta; no se marcará como completada una tarea únicamente por haberla diseñado.
