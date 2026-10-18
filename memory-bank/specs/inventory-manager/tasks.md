# HealthCore Inventory Manager — Tasks de implementación

**Estado:** plan de trabajo preliminar; no iniciado.
**Versión:** 0.1 · **Fecha:** 2026-10-18
**Regla:** ninguna tarea ejecutable se inicia antes de aprobación explícita del CTO del SPEC, PLAN y TASKS y de cerrar las decisiones de dominio que la bloqueen.

## Reglas de ejecución

- Implementar en el orden y dependencias acordados; cada tarea tendrá pruebas y un commit independiente con hash real.
- Las tareas con decisión de dominio pendiente no pueden marcarse listas ni implementarse mediante una suposición. Al aprobar las decisiones, ajustar únicamente las tareas afectadas y mantener estables IDs no afectados.
- Tests abajo son planes, no tests existentes ni ejecutados. Identificadores `INV-TST-*` son identificadores planificados.
- No hacer push ni crear Pull Request sin autorización expresa.

## Decisiones de dominio previas / gates

Aprobación previa requerida para: (D-01) ámbito global/clínica/ubicación/lote; (D-02) campos, unicidad y baja de artículo; (D-03) UOM, escala y conversiones; (D-04) significado/representación de ajustes; (D-05) existencia/obligatoriedad y reglas de lote; (D-06) punto de reorden, alcance y comparación; (D-07) política de corrección de movimientos; (D-08) permisos y alcance de actores. Esas decisiones no se convierten en categorías o valores inventados en tareas de implementación.

## Tareas ordenadas

### INV-TASK-001 — Aprobar decisiones de dominio
- **Objetivo:** registrar la decisión de Operaciones/CTO sobre D-01–D-08, unidades, alcance, datos obligatorios y reglas de negocio faltantes.
- **Criterios EARS asociados:** INV-AC-001–020 (definen el comportamiento a concretar sin presumir valores).
- **Dependencias:** aprobación explícita del SPEC, PLAN y TASKS.
- **Archivos/componentes previstos:** `memory-bank/specs/inventory-manager/spec.md`; actualización asociada de `plan.md` y `tasks.md` sólo si la decisión cambia arquitectura/plan.
- **Implementación acotada:** registrar las decisiones y fuentes; mantener como pendientes las que no sean aprobadas. No crear código, migraciones ni tests ejecutables en esta tarea documental.
- **Tests previstos:** revisión documental de consistencia, `INV-TST-DOC-001` (pendiente de ejecución; comprobar cada D-01–D-08 decidido o explícitamente aplazado).
- **Definition of Done:** CTO/Operaciones han aprobado decisiones o identificado expresamente blockers; spec/plan/tasks reflejan ese resultado y no contienen valores de negocio no aprobados.
- **Commit asociado:** Pendiente.

### INV-TASK-002 — Definir contrato y políticas de inventario
- **Objetivo:** concretar DTOs, filtros, resultados, errores observables y matriz de capabilities a partir de decisiones aprobadas, sin ampliar el alcance.
- **Criterios EARS asociados:** INV-AC-001–005, INV-AC-010, INV-AC-012–014, INV-AC-018–020.
- **Dependencias:** INV-TASK-001.
- **Archivos/componentes previstos:** diseño en `services/central-api/app/inventory/` y `app/auth/` (rutas/DTOs/capabilities exactos por definir); documentos de especificación si se identifica cambio al requisito.
- **Implementación acotada:** acordar la forma de requests/responses, estados de artículo, errores y permisos; prohibir stock como input y decidir si historial de movimientos permite correcciones y con qué traza.
- **Tests previstos:** `INV-TST-CONTRACT-001` (matriz operación→request/response/error), `INV-TST-AUTH-001` (matriz actor×operación y scope). No son ejecutables hasta fijar contratos.
- **Definition of Done:** cada operación del SPEC tiene contrato y error esperado; ningún request de artículo contiene stock; autorización está aprobada por actores responsables.
- **Commit asociado:** Pendiente.

### INV-TASK-003 — Modelar artículos y persistencia base
- **Objetivo:** incorporar el modelo persistido de artículos con atributos aprobados y política de baja, sin almacenar stock como verdad independiente.
- **Criterios EARS asociados:** INV-AC-001–005, INV-AC-010, INV-AC-016.
- **Dependencias:** INV-TASK-001, INV-TASK-002.
- **Archivos/componentes previstos:** `services/central-api/app/inventory/models.py`, integración en `app/db/models/__init__.py`, nueva revisión en `alembic/versions/`.
- **Implementación acotada:** columnas sólo según D-02 y D-01; claves y constraints aprobadas; ninguna columna `stock`; decisión explícita sobre preservar referencias de movimientos al dar de baja.
- **Tests previstos:** `INV-TST-ITEM-MODEL-001` (constraints/uniqueness según aprobación), `INV-TST-MIG-001` (upgrade y downgrade/procedimiento de recuperación), `INV-TST-NO-STOCK-COLUMN-001` (metadata/modelo no contiene campo stock independiente).
- **Definition of Done:** migración pasa en base de prueba vacía y desde head actual; modelo cumple atributos aprobados y no contiene saldo autoritativo; pruebas sintéticas pasan.
- **Commit asociado:** Pendiente.

### INV-TASK-004 — Implementar contratos de artículo
- **Objetivo:** exponer alta, consulta, edición y baja de artículos con validación y autorización aprobadas.
- **Criterios EARS asociados:** INV-AC-001–005, INV-AC-010, INV-AC-020.
- **Dependencias:** INV-TASK-002, INV-TASK-003.
- **Archivos/componentes previstos:** `services/central-api/app/inventory/schemas.py`, `service.py`, `router.py`, `app/main.py`; pruebas bajo `services/central-api/tests/`.
- **Implementación acotada:** CRUD de atributos autorizados; la respuesta no ofrece stock editable; baja de acuerdo con la política aprobada; cambios sin mutación parcial.
- **Tests previstos:** `INV-TST-ITEM-HTTP-001` create/read/update/deactivate; `INV-TST-ITEM-VALIDATION-001` inválidos/no encontrado/conflicto; `INV-TST-ITEM-NO-STOCK-INPUT-001` rechazo del campo stock; `INV-TST-AUTH-ITEM-001` acceso denegado y permitido.
- **Definition of Done:** todas las operaciones aprobadas tienen tests HTTP con datos sintéticos; intentos inválidos no producen cambios; endpoints requieren los permisos acordados.
- **Commit asociado:** Pendiente.

### INV-TASK-005 — Implementar validaciones de unidades, ámbito y lotes
- **Objetivo:** aplicar consistencia entre artículo, cantidad/unidad y el ámbito aprobado, incluyendo lote sólo si D-05 lo confirma.
- **Criterios EARS asociados:** INV-AC-012–014, INV-AC-018.
- **Dependencias:** INV-TASK-001, INV-TASK-002, INV-TASK-003.
- **Archivos/componentes previstos:** módulo `services/central-api/app/inventory/` (schemas/service/models), migración de lote/scope sólo si aprobada; `tests/`.
- **Implementación acotada:** FKs y validación transaccional de referencia/combinaciones. No incluir caducidad ni conversiones que no estén aprobadas.
- **Tests previstos:** `INV-TST-REF-ITEM-001`, `INV-TST-REF-LOT-001` (condicional a lote habilitado), `INV-TST-UOM-001`, `INV-TST-SCOPE-001`.
- **Definition of Done:** referencias inexistentes/incoherentes y cantidades/unidades inválidas se rechazan sin mutación; cobertura refleja exactamente políticas aprobadas. Si lote queda fuera, documentar inaplicabilidad de `INV-TST-REF-LOT-001`.
- **Commit asociado:** Pendiente.

### INV-TASK-006 — Registrar movimientos de entrada, salida y ajuste
- **Objetivo:** crear movimientos trazables para los tres tipos permitidos y establecer la cantidad firmada correspondiente.
- **Criterios EARS asociados:** INV-AC-006–008, INV-AC-012–014, INV-AC-016, INV-AC-020.
- **Dependencias:** INV-TASK-001, INV-TASK-002, INV-TASK-003, INV-TASK-005.
- **Archivos/componentes previstos:** `inventory/models.py`, migración Alembic de movimientos, `schemas.py`, `service.py`, `router.py`, `tests/`.
- **Implementación acotada:** insertar registro de movimiento dentro de transacción; signo de entrada/salida explícito; ajuste según D-04; actor/timestamp/campos de auditoría aprobados. No alterar stock directamente.
- **Tests previstos:** `INV-TST-MOVEMENT-IN-001`, `INV-TST-MOVEMENT-OUT-001`, `INV-TST-MOVEMENT-ADJUST-001`, `INV-TST-MOVEMENT-REFERENCE-001`, `INV-TST-MOVEMENT-ATOMICITY-001`.
- **Definition of Done:** cada movimiento aceptado queda persistido con referencia coherente; rechazos no dejan escrituras parciales; prueba de contrato demuestra ajuste como movimiento y no escritura de saldo.
- **Commit asociado:** Pendiente.

### INV-TASK-007 — Consultar stock calculado e historial
- **Objetivo:** permitir consultas de existencia derivada y movimientos históricos, agregados por artículo y dimensiones aprobadas.
- **Criterios EARS asociados:** INV-AC-002, INV-AC-009, INV-AC-016, INV-AC-018, INV-AC-020.
- **Dependencias:** INV-TASK-003, INV-TASK-005, INV-TASK-006.
- **Archivos/componentes previstos:** `inventory/service.py`, `schemas.py`, `router.py`; pruebas en `services/central-api/tests/`.
- **Implementación acotada:** agregar cantidades firmadas desde movimientos en PostgreSQL; devolver unidad/ámbito; ordenar historial de forma estable; no mantener saldo editable ni proyección autoritativa.
- **Tests previstos:** `INV-TST-STOCK-SUM-001` suma con movimientos entrada/salida/ajuste; `INV-TST-STOCK-SCOPE-001`; `INV-TST-HISTORY-001`; `INV-TST-STOCK-NO-DIRECT-SET-001`.
- **Definition of Done:** la respuesta calculada coincide con la suma de movimientos válidos para múltiples secuencias sintéticas; no existe operación pública set-stock; historial mantiene datos tras baja lógica.
- **Commit asociado:** Pendiente.

### INV-TASK-008 — Rechazar stock negativo con concurrencia
- **Objetivo:** serializar validación de salida/ajuste frente a stock disponible del mismo ámbito y probar colisiones concurrentes en PostgreSQL.
- **Criterios EARS asociados:** INV-AC-011, INV-AC-015.
- **Dependencias:** INV-TASK-001, INV-TASK-005, INV-TASK-006, INV-TASK-007.
- **Archivos/componentes previstos:** `inventory/service.py`, modelos/constraints sólo si justificadas, pruebas de integración PostgreSQL en `services/central-api/tests/`.
- **Implementación acotada:** escoger una estrategia transaccional con lock/aislamiento sobre ámbito estable, implementar rollback/reintento limitado si aplica; no asumir `SELECT FOR UPDATE` sobre conjunto vacío suficiente.
- **Tests previstos:** `INV-TST-NONNEGATIVE-001` salida/ajuste que excede disponible; `INV-TST-CONCURRENCY-001` solicitudes coordinadas para el mismo scope, incluyendo saldo vacío si procede; `INV-TST-CONCURRENCY-ATOMICITY-001` una sola mutación aceptada cuando el total requerido excede saldo.
- **Definition of Done:** en PostgreSQL la prueba concurrente demuestra que no se acepta saldo negativo, cada aceptación tiene un movimiento y cada rechazo carece de mutación parcial; estrategia y límites documentados.
- **Commit asociado:** Pendiente.

### INV-TASK-009 — Implementar consulta de punto de reorden
- **Objetivo:** detectar artículos cuyo stock calculado está por debajo del umbral aprobado, en su unidad y alcance definidos.
- **Criterios EARS asociados:** INV-AC-017, INV-AC-019.
- **Dependencias:** INV-TASK-001, INV-TASK-003, INV-TASK-005, INV-TASK-007.
- **Archivos/componentes previstos:** `inventory/service.py`, DTO y router; migración sólo si la ubicación aprobada del umbral requiere columna/relación; pruebas PostgreSQL.
- **Implementación acotada:** comparar el agregado de movimientos con punto de reorden configurado según igualdad/unidad/ámbito aprobados; tratamiento explícito de umbral nulo/incompatible.
- **Tests previstos:** `INV-TST-REORDER-BELOW-001`, `INV-TST-REORDER-EQUAL-001`, `INV-TST-REORDER-ABOVE-001`, `INV-TST-REORDER-UNIT-001`, `INV-TST-REORDER-NULL-001` según políticas aprobadas.
- **Definition of Done:** casos debajo/igual/encima concuerdan con política aprobada; los tests de unidad/valor nulo verifican el comportamiento aprobado; sin valor de umbral codificado por defecto.
- **Commit asociado:** Pendiente.

### INV-TASK-010 — Completar auditoría, permisos y regresión de integración
- **Objetivo:** verificar trazabilidad, aislamiento de acceso y compatibilidad del módulo con el API existente y toda su suite.
- **Criterios EARS asociados:** INV-AC-001–020, especialmente INV-AC-016, INV-AC-020.
- **Dependencias:** INV-TASK-004, INV-TASK-006, INV-TASK-007, INV-TASK-008, INV-TASK-009.
- **Archivos/componentes previstos:** inventory module, `app/auth/` sólo si ajustes aprobados, `services/central-api/tests/`, documentación del módulo si afecta uso.
- **Implementación acotada:** completar pruebas faltantes de historial, permisos, referencias, reorden, concurrencia y migración; revisar logs para evitar secretos/PHI; ejecutar suite central y migración de instalación limpia/desde head.
- **Tests previstos:** `INV-TST-AUDIT-001`, `INV-TST-AUTH-MATRIX-001`, `INV-TST-API-REGRESSION-001`, `INV-TST-MIGRATION-FRESH-001`, `INV-TST-MIGRATION-UPGRADE-001`, `INV-TST-LOG-SENSITIVITY-001`.
- **Definition of Done:** matriz criterio→test completa; suite API y pruebas de migración aplicables pasan y se registra comando/evidencia; revisión confirma no hay endpoint/formulario/campo de stock editable ni log con secretos/datos reales; cada commit contiene cambios acotados y hash real registrado.
- **Commit asociado:** Pendiente.

## Matriz preliminar de trazabilidad

Los test IDs son planificación futura, no tests ejecutados. Las referencias D-01–D-08 indican decisiones de dominio que condicionan implementación.

| Requisito | Criterio EARS | Tarea | Test planificado | Commit |
|---|---|---|---|---|
| RF-001 Alta de artículo | INV-AC-001 | INV-TASK-002, 003, 004 | INV-TST-ITEM-HTTP-001 | Pendiente |
| RF-001 Consulta de artículo sin editar stock | INV-AC-002 | INV-TASK-004, 007 | INV-TST-ITEM-HTTP-001, INV-TST-ITEM-NO-STOCK-INPUT-001 | Pendiente |
| RF-001 Edición de atributos | INV-AC-003 | INV-TASK-002, 004 | INV-TST-ITEM-HTTP-001, INV-TST-ITEM-VALIDATION-001 | Pendiente |
| RF-001 Baja e historial | INV-AC-004 | INV-TASK-003, 004, 007 | INV-TST-ITEM-HTTP-001, INV-TST-HISTORY-001 | Pendiente |
| RF-001 rechazo de artículo/datos inválidos | INV-AC-005 | INV-TASK-004 | INV-TST-ITEM-VALIDATION-001 | Pendiente |
| RF-002 entrada incrementa | INV-AC-006 | INV-TASK-005, 006, 007 | INV-TST-MOVEMENT-IN-001, INV-TST-STOCK-SUM-001 | Pendiente |
| RF-002 salida reduce | INV-AC-007 | INV-TASK-005, 006, 007 | INV-TST-MOVEMENT-OUT-001, INV-TST-STOCK-SUM-001 | Pendiente |
| RF-002 ajuste vía movimiento | INV-AC-008 | INV-TASK-001, 006, 007 | INV-TST-MOVEMENT-ADJUST-001 | Pendiente |
| RF-003 stock suma firmada | INV-AC-009 | INV-TASK-006, 007 | INV-TST-STOCK-SUM-001, INV-TST-STOCK-SCOPE-001 | Pendiente |
| RF-003 prohibición de edición directa | INV-AC-010 | INV-TASK-002, 003, 004, 007, 010 | INV-TST-ITEM-NO-STOCK-INPUT-001, INV-TST-STOCK-NO-DIRECT-SET-001 | Pendiente |
| RF-004 evitar negativo | INV-AC-011 | INV-TASK-006, 008 | INV-TST-NONNEGATIVE-001, INV-TST-CONCURRENCY-001 | Pendiente |
| RF-005 artículo existente | INV-AC-012 | INV-TASK-005, 006 | INV-TST-MOVEMENT-REFERENCE-001, INV-TST-REF-ITEM-001 | Pendiente |
| RF-005 lote según política | INV-AC-013 | INV-TASK-001, 005, 006 | INV-TST-REF-LOT-001 (condicional) | Pendiente |
| RF-005 cantidad/unidad/referencias coherentes | INV-AC-014 | INV-TASK-001, 005, 006 | INV-TST-UOM-001, INV-TST-SCOPE-001, INV-TST-MOVEMENT-REFERENCE-001 | Pendiente |
| RF-004 concurrencia | INV-AC-015 | INV-TASK-008 | INV-TST-CONCURRENCY-001, INV-TST-CONCURRENCY-ATOMICITY-001 | Pendiente |
| RF-007 trazabilidad histórica | INV-AC-016 | INV-TASK-003, 006, 007, 010 | INV-TST-HISTORY-001, INV-TST-AUDIT-001 | Pendiente |
| RF-006 identificación bajo reorden | INV-AC-017 | INV-TASK-001, 009 | INV-TST-REORDER-BELOW-001, INV-TST-REORDER-EQUAL-001 | Pendiente |
| RF-003 consulta de stock | INV-AC-018 | INV-TASK-005, 007 | INV-TST-STOCK-SUM-001, INV-TST-STOCK-SCOPE-001 | Pendiente |
| RF-006 listado bajo reorden | INV-AC-019 | INV-TASK-009 | INV-TST-REORDER-BELOW-001, INV-TST-REORDER-ABOVE-001 | Pendiente |
| RF-008 autorización | INV-AC-020 | INV-TASK-002, 004, 006, 010 | INV-TST-AUTH-ITEM-001, INV-TST-AUTH-MATRIX-001 | Pendiente |

## Estado de los commits

Todos los commits están `Pendiente`. Ningún test está implementado ni ejecutado para este módulo. Los commits reales se anotarán tras implementar y verificar cada tarea, sin fabricar hashes.
