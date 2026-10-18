# HealthCore Inventory Manager — Plan técnico

**Estado:** borrador dependiente de aprobación del SPEC y de decisiones de dominio.
**Versión:** 0.1 · **Fecha:** 2026-10-18
**Alcance:** plan de arquitectura e implementación; no se ha ejecutado código.

> El prompt prescribe generar plan y tareas sin aprobación, pero la fase de implementación queda bloqueada hasta aprobación explícita del CTO. Este documento traduce el comportamiento solicitado a la arquitectura comprobada, manteniendo sin decidir lo que el dominio no documenta.

## 1. Reutilización de componentes existentes

- Mantener la API central existente `services/central-api/`, FastAPI y los routers/modulos de dominio registrados en `app/main.py`; no crear un microservicio de inventario. Esto sigue las convenciones de `memory-bank/conventions.md` y `.agents/rules/03-backend-python.md`. (INV-AC-001–020)
- Reutilizar SQLAlchemy async, PostgreSQL, `AsyncSession`/`get_session`, Alembic y `Base` tal como están configurados en `services/central-api/app/db/`, `alembic/` y `pyproject.toml`. No crear esquema paralelo ni otra estrategia de migraciones. (INV-AC-006–019)
- Reutilizar integración de autenticación JWT/capabilities mediante `app/auth/dependencies.py`, `roles.py` y `policies.py`, pero definir capacidades propias de Inventory Manager tras aprobar actores, funciones y ámbito. No heredar las capacidades de incidencias ni convertir `admin` en autorización implícita de producción sin una decisión revisada. (INV-AC-001–005, 006–008, 018–020)
- Aplicar validación de entrada/salida con Pydantic y códigos de error consistentes con las rutas actuales; completar validaciones críticas en transacción y restricciones relacionales. (INV-AC-005–015)
- Si una UI TypeScript necesita tipos compartidos, evaluar `packages/shared/`; la UI queda explícitamente fuera del alcance inicial. No crear o modificar frontends hasta aprobarlo. (No aplica a criterio de UI; respeta alcance)
- Desarrollo y pruebas sólo con datos sintéticos; no guardar secretos en el repositorio y no exponer datos sensibles en logs (`.agents/rules/09-sensitive-data.md`). (INV-AC-016, 020)

## 2. Ubicación del módulo

Propuesta de módulo `services/central-api/app/inventory/` con `models.py`, `schemas.py`, `service.py`, `router.py` y `__init__.py`, registrado desde `app/main.py`. Migraciones en el `alembic/versions/` existente y modelos en el registro metadata de `app/db/models/__init__.py` o mecanismo equivalente comprobado.

La ubicación no introduce un componente independiente, por lo que no se crea nueva carpeta de primer nivel. El componente seguirá las convenciones bilingües de documentación aplicables al componente, y se añadirá el README correspondiente al acordar la estructura definitiva.

## 3. Modelo de datos conceptual y relaciones

Esquema lógico provisional (no es decisión de negocio sobre campos/ámbito):

- **InventoryItem**: identidad estable; atributos de catálogo que Operaciones apruebe; unidad base y punto de reorden sólo después de cerrar política. No contendrá una columna `stock` autoritativa.
- **InventoryMovement**: identidad, referencia obligatoria al artículo, tipo (entrada/salida/ajuste), cantidad de magnitud y unidad, fecha/hora, actor y campos de trazabilidad aprobados. Se almacena la semántica necesaria para interpretar su cantidad firmada de modo estable. El movimiento de apertura/inicial se expresa como movimiento, no como saldo inicial fuera de la bitácora.
- **InventoryLot** (condicional): se crea sólo si Operaciones confirma gestión de lotes; referencia a artículo y, si aplica, dimensión de ubicación/clinic. Los movimientos referencian lote si la política lo exige. No añadir campos de caducidad salvo cambio explícito de alcance.
- **InventoryScope / dimensiones**: no proponer tabla hasta decidir si stock es global, por clínica, ubicación, lote o combinación. Cada movimiento y consulta debe asociarse al ámbito aprobado de forma coherente.
- **Auditoría**: movimientos append-only de negocio; cualquier rectificación se representa mediante mecanismo compensatorio y trazable aprobado, evitando sobrescritura silenciosa. No añadir copia de la infraestructura de Management sin decidir requisitos de auditoría del dominio.

La existencia se calcula agregando cantidades firmadas de movimientos válidos, agrupadas por artículo y ámbito. Punto de reorden en el artículo o en cada dimensión depende de decisión pendiente. Las claves foráneas garantizan existencia de referencias persistidas y las reglas que requieren varias filas (artículo-lote-ámbito) requieren validación transaccional además de FK cuando proceda. (INV-AC-006–019)

## 4. Contratos de API y DTOs

Rutas candidatas, nombres sujetos a contrato aprobado, bajo prefijo `/inventory`:

- `POST /items`, `GET /items`, `GET /items/{item_id}`, `PATCH /items/{item_id}`, `POST /items/{item_id}/deactivation` (operación de baja lógica como candidata; no asumir que está aprobada).
- `POST /movements` y `GET /items/{item_id}/movements`.
- `GET /items/{item_id}/stock` o endpoint de consulta agregado según ámbito aprobado.
- `GET /reorder` con filtro/segmentación aprobados.

DTOs candidatos: creación/actualización/lectura de artículo; alta de movimiento; respuesta de movimiento; consulta de stock (cantidad calculada, unidad y ámbito); resultado de reorden. No se incluirá ningún `stock` en DTOs de alta/edición de artículo ni un DTO/operación “set stock”. La respuesta de existencias puede contener propiedad de salida derivada, nunca input editable. La representación de ajuste y signo se bloquea hasta aprobación.

Errores a mapear de forma coherente: 401/403 identidad/capacidad; 404 artículo/lote/recurso; 409 insuficiencia de stock, conflicto por baja/historial o idempotencia si se aprueba; 422 cantidad, unidad, lote, ámbito o referencia semánticamente inválidos. Contratos exactos y los códigos se revisarán con las convenciones reales del servicio. (INV-AC-001–020)

## 5. Validación y autorización

- Esquemas Pydantic limitan formas/tipos y rechazan campos no permitidos, especialmente cualquier intento de enviar stock en operaciones de catálogo. El comportamiento de campos desconocidos deberá ser explícito, no silenciosamente ignorado. (INV-AC-010, 014)
- El dominio verifica artículo activo/existente, lotes según regla aprobada, unidad compatible, cantidad/precisión, tipo de movimiento y dimensión de existencias. FK y restricciones SQL complementan esas validaciones. (INV-AC-005, 012–014)
- La autorización se implementa con dependencias/capabilities y políticas contextuales del estilo ya usado, sujetas a matriz aprobada por Operaciones/Tecnología/Cumplimiento. Identidad de actor procede del principal verificado, no del body. (INV-AC-020)
- El acceso a auditoría/historial y la información de salida se limitan según política aprobada; no incluir secretos ni PHI en logs o fixtures. (INV-AC-016, 020)

## 6. Persistencia, migraciones y transacciones

- Usar una migración Alembic reversible o con procedimiento explícito documentado, sobre PostgreSQL existente. Registrar nuevos modelos en metadata y revisar aplicación desde esquema vacío y actualización desde la revisión vigente. No se ejecutan migraciones en esta fase documental.
- Persistir encabezados de movimientos como fuente durable. Para mantener trazabilidad, evitar borrar/editar directamente movimientos aceptados; si se aprueba corrección, representar reversa/ajuste compensatorio preservando actor, momento y razón.
- Una transacción incluye verificación de existencia/saldo, inserción del movimiento y cualquier auditoría; rollback completo si falla cualquiera de las validaciones. Ningún saldo independiente se persiste como fuente de verdad. (INV-AC-006–016)

## 7. Cálculo de stock y prevención de negativos bajo concurrencia

Consulta: agregar el efecto firmado de movimientos válidos por artículo y ámbito aprobado. La regla exacta de cantidad firmada para entradas/salidas es positiva/negativa; para ajustes depende de la decisión sobre ajuste como delta o conteo físico.

Para serializar validación de escrituras concurrentes se seleccionará una estrategia PostgreSQL al detallar implementación: bloqueo transaccional de una fila estable por artículo/ámbito antes de leer agregado e insertar movimiento, o aislamiento serializable/reintento controlado. Debe elegirse una estrategia concreta mediante pruebas; un “read then insert” sin sincronización no es aceptable. Restricción sobre saldo materializado no sustituye la fuente de movimientos. Si no existe una fila natural para bloquear, diseñar una clave/scope estable o usar advisory lock con key determinista tras revisión.

La estrategia debe demostrar que solicitudes concurrentes de salida/ajuste producen un resultado equivalente a serializar: las operaciones que causen negativo se rechazan; las aceptadas quedan completas con un movimiento auditable. No afirmar que un simple `SELECT ... FOR UPDATE` sobre movimientos existentes protege el caso de saldo vacío/phantom sin una fila de ámbito estable. (INV-AC-009, 011, 015)

## 8. Lotes y puntos de reorden

No implementar tabla, obligatoriedad o reglas de lote hasta decisión de Operaciones. Si se confirma lote, definir unicidad, pertenencia al artículo/ámbito, obligatoriedad por tipo de movimiento y validaciones de referencia antes de migración. Caducidad sigue fuera de alcance. (INV-AC-013)

No codificar valores o política de reorden por defecto. Tras aprobar si el umbral vive en artículo o ámbito, su unidad y regla de igualdad, la consulta devuelve los artículos para los que `stock_calculado < reorder_point` según el criterio aprobado. Definir qué ocurre con umbral nulo/inactivo e incompatibilidad de unidad. (INV-AC-017, 019)

## 9. Errores, trazabilidad, logging y seguridad

- Respuestas de error identificables y sin fuga de datos; preservar convenciones FastAPI existentes.
- Actor verificado y timestamps UTC para trazabilidad. Cantidades se expresan con precisión/unidad aprobadas; su tipo numérico concreto se fija con esas reglas.
- Los movimientos aceptados son evidencia histórica. Las respuestas de historial deben presentar orden cronológico estable y no borrar entradas por baja de artículo. (INV-AC-016)
- Registrar eventos operativos mínimos sin datos de paciente ni secretos. Retención, consulta de auditoría y alcance multi-jurisdiccional requieren revisión de Cumplimiento; no inferir obligaciones regulatorias específicas del briefing general.
- Utilizar sólo datos sintéticos en tests y pruebas locales; sin promoción de datos reales sin aprobación explícita. (INV-AC-020)

## 10. Estrategia de pruebas

Las pruebas se escribirán sólo después de la aprobación para implementar. Plan previsto:

1. **Unitarias de dominio:** tipos/signos de entrada y salida, ajuste conforme a política, validación de cantidad/unidad/lote, y cálculo de agregación. (INV-AC-006–009, 013–014)
2. **HTTP de contrato:** CRUD del artículo (create/read/update/deactivate), DTO sin stock input, validación de referencias y errores observables. Utilizar el patrón `httpx.AsyncClient`/`ASGITransport` que ya emplean las pruebas del servicio. (INV-AC-001–005, 010, 012, 020)
3. **Integración PostgreSQL:** migración, FK, agregado de movimientos, existencia consultada, reorden, rechazo sin cambios parciales, historial de cambios/bajas. (INV-AC-009, 011–019)
4. **Concurrencia PostgreSQL:** dos o más transacciones coordinadas para competir por el saldo de un mismo ámbito; probar saldo inicialmente vacío si aplica, resultado no negativo e integridad de movimientos. No usar una simulación puramente unitaria como prueba suficiente. (INV-AC-011, 015)
5. **Regresión del monorepo/API:** suite de `services/central-api` y migración desde estado actual, siempre en entorno de prueba con base sintética. (Todos los criterios según trazabilidad)

Los identificadores de tests se proponen en `tasks.md`; no hay tests ejecutados ni implementados para Inventory Manager.

## 11. Decisiones relevantes, alternativas y riesgos

| Tema | Decisión de plan | Alternativa/riesgo |
|---|---|---|
| Servicio | Módulo dentro de la API central existente. | Microservicio añade operación y consistencia distribuida sin necesidad documentada; no se propone. |
| Fuente de stock | Movimientos durables y agregado de lectura; no columna autoritativa de stock. | Saldo editable/almacenado como verdad viola invariante; caché derivada sólo si evidencia futura y reconciliable. |
| Concurrencia | Bloqueo/aislamiento a elegir y probar en PostgreSQL, con ámbito estable. | Agregar sin serialización crea oversell y saldo negativo. El scope aún no está decidido, impide seleccionar bloqueo definitivo. |
| Corrección | No borrar/editar sin decisión; preferir corrección compensatoria trazable como candidata. | Compensación no es requisito ya aprobado; debe definirse antes de habilitar ajustes correctivos. |
| Ámbito | No fijar tabla/llave de inventario hasta aprobar scope. | Elegir clínica o global sin evidencia distorsiona stock, reorden y concurrencia. |
| Artículos/lotes/UOM | Campos y relaciones pendientes. | Inventarlos causaría esquema y catálogo incorrectos; cambio tardío requeriría migración. |
| Reorden | Umbral y comparación configurables sólo según decisión aprobada. | Valor o política por defecto puede generar alertas incorrectas. |
| Autorización | Reutilizar infraestructura, diseñar capabilities de dominio nuevas. | Reusar roles de incidentes sin validación da permisos excesivos o insuficientes. |
| Interfaz | Fuera de alcance inicial; endpoints primero. | Construir UI antes de aprobar workflow/campos afianza decisiones no confirmadas. |
| Privacidad | Minimización, datos sintéticos, logging sin PHI/secrets. | El briefing no define controles específicos del módulo; Cumplimiento debe aprobarlos sin inventar obligaciones concretas. |

## 12. Condiciones de entrada a implementación

No comenzar trabajo ejecutable hasta que el CTO apruebe los tres documentos y se resuelvan, o se delimite explícitamente como bloqueantes de tareas separables, estas decisiones: ámbito, atributos de artículo, unidades/precisión, ajuste, lotes, reorden, ciclo de vida/corrección de movimientos y matriz de autorización. Cambios de requisito posteriores se incorporan primero a `spec.md`, después al plan si altera arquitectura y luego sólo a tareas afectadas.
