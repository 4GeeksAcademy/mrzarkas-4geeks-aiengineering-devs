# HealthCore Inventory Manager — Specification

**Estado:** implementado y validado como prototipo sintético pre-MVP.
**Versión:** 1.0 · **Fecha:** 2026-11-02
**Fuente de autorización:** decisiones D-01–D-08 y continuación aprobadas por el usuario en esta sesión; países como regiones. Revisión simulada de Claire Whitfield: `HC-INV-APPROVAL-2026-11-02`, 02/11/2026. No constituye autorización de piloto, producción ni certificación normativa.

## Propósito y alcance

Gestión de artículos, presentaciones y lotes; entradas, salidas, conteos físicos y compensaciones; stock calculado por clínica; consulta regional por país; reorden e historial autorizado. La implementación reside en `backend/app/inventory/`, siguiendo el traslado documentado de la API a `backend/`. No se implementa una interfaz de inventario ni aprovisionamiento regional automático.

## Decisiones aprobadas

| ID | Decisión implementada |
|---|---|
| D-01 | Existencias independientes por artículo/clínica. Región = país de la clínica (`jurisdiction_id`); consultas regionales, sin movimientos entre países. La reposición se coordina regionalmente; no hay workflow de compra. |
| D-02 | Título, código único y unidad obligatorios. Cantidad obligatoria en entradas/salidas; punto de reorden obligatorio por artículo/clínica antes de movimientos. Código, unidad y uso de lotes inmutables; título/presentación editables. Baja lógica sólo con saldo total cero, conservando historia. |
| D-03 | Cantidades enteras positivas en unidades base; conteo entero no negativo. Presentación opcional con nombre y equivalencia entera positiva (blister/caja). Conversión en backend y snapshot histórico. |
| D-04 | Ajuste mediante conteo físico y motivo obligatorio; delta = conteo − saldo previo. |
| D-05 | Uso de lotes opcional al crear artículo. Cuando se habilita, lote obligatorio en movimientos, existente y del mismo artículo. Saldos por lote y clínica. Sin caducidad. |
| D-06 | Umbral entero positivo obligatorio por artículo/clínica. Alerta si stock < umbral; igualdad no alerta. Sin umbral implícito. |
| D-07 | Movimientos inmutables; corrección por compensación única del movimiento original, con motivo. No se compensan compensaciones ni se permite saldo negativo. |
| D-08 | RBAC de inventario independiente de roles anteriores; alcance validado en backend, mínimo privilegio. |

## Roles y alcance

- `inventoryAdmin`: catálogo, presentaciones, lotes y baja; sin movimientos ni permiso clínico implícito.
- `inventoryOperator`: lectura, entradas/salidas e historial en clínicas asignadas.
- `inventoryManager`: operador más conteos, compensaciones y configuración de reorden.
- `inventoryRegional`: stock, historial y reorden de clínicas del país asignado; sin escrituras.
- `inventoryAuditor`: lectura regional y auditoría dentro del ámbito autorizado.

El JWT temporal incluye scopes firmados; su emisión sólo está habilitada en desarrollo/test. No hay SSO/OIDC de producción. El catálogo es global; stock y eventos clínicos están restringidos por ámbito.

## Requisitos funcionales

| ID | Comportamiento aprobado |
|---|---|
| RF-001 | Alta, consulta, edición y baja lógica del catálogo. |
| RF-002 | Entradas, salidas y conteos físicos registrados como movimientos. |
| RF-003 | Stock derivado de movimientos por clínica/artículo y lote cuando aplica. |
| RF-004 | Rechazo de saldos negativos, incluida concurrencia. |
| RF-005 | Validación de artículo, clínica, lote, cantidades y unidades. |
| RF-006 | Consulta de artículos bajo punto de reorden obligatorio. |
| RF-007 | Trazabilidad histórica inmutable y correcciones compensatorias. |
| RF-008 | Acceso limitado por rol y ámbito geográfico en backend. |

## Invariantes y contratos

Stock = SUM(delta) de movimientos; no hay columna autoritativa de saldo ni operación set-stock. Writes son transaccionales, validan referencias y bloquean filas estables para impedir saldos negativos concurrentes. Requests de inventario rechazan campos extra. Contratos HTTP completos: `backend/app/inventory/router.py`, `schemas.py` y `/docs`. Errores: 401 identidad, 403 permisos/ámbito, 404 referencia, 409 conflicto, 422 validación, 503 imposibilidad de registrar denegación.

## Auditoría y retención

Movimientos y eventos incluyen actor, UTC, artículo, clínica, país histórico cuando aplica, cantidades/unidad/saldos y motivos/referencia original. Denegaciones autenticadas relevantes se guardan duraderamente sin cuerpos libres, tokens ni credenciales. Triggers PostgreSQL impiden UPDATE/DELETE de movimientos y auditoría. Historial regional usa el país del evento; no reclasifica eventos por cambios posteriores de clínica. Eventos anteriores a `0011` conservan país desconocido y quedan fuera de lecturas regionales que no puedan autorizarlos. Detalles sensibles de catálogo/historia se redactan según la vista.

Retención funcional aprobada: 24 meses de calendario desde UTC (`retention_until`). Se conserva todo el historial; no se filtra ni borra al vencer. Procedimiento de disposición controlada y auditable descrito en el README del módulo; su mecanismo ejecutable y purga automática quedan pendientes de diseño y validación. No se permite borrar evidencia que comprometa trazabilidad o stock.

## Criterios de aceptación EARS


Se conservan los IDs y comportamientos EARS originales; las reglas referidas como aprobadas se concretan en D-01–D-08 de esta versión. La evidencia ejecutada se encuentra en tasks.md.

| ID | Tipo | Criterio |
|---|---|---|
| INV-AC-001 | Evento | Cuando un actor autorizado da de alta un artículo con los campos y valores requeridos aprobados, el sistema debe crear y devolver una referencia estable al artículo. |
| INV-AC-002 | Evento | Cuando se consulta un artículo existente, el sistema debe devolver sus atributos autorizados sin exponer un campo editable de stock. |
| INV-AC-003 | Evento | Cuando un actor autorizado edita atributos permitidos de un artículo existente, el sistema debe persistirlos y devolver el artículo actualizado sin modificar movimientos ni stock. |
| INV-AC-004 | Evento | Cuando un actor autorizado da de baja un artículo, el sistema debe aplicar la política aprobada y conservar el historial de movimientos asociado. |
| INV-AC-005 | Comportamiento no deseado | Si una alta, edición o baja referencia un artículo inexistente o contiene datos inválidos, entonces el sistema debe rechazar la operación con un error observable y no producir una mutación parcial. |
| INV-AC-006 | Evento | Cuando se acepta una entrada de cantidad válida para un artículo existente, el sistema debe registrar un movimiento y aumentar la existencia calculada en esa cantidad, expresada en la unidad aprobada. |
| INV-AC-007 | Evento | Cuando se acepta una salida de cantidad válida para un artículo existente, el sistema debe registrar un movimiento y reducir la existencia calculada en esa cantidad, expresada en la unidad aprobada. |
| INV-AC-008 | Evento | Cuando se acepta un ajuste, el sistema debe registrar un movimiento de ajuste y calcular el cambio de stock mediante la semántica de ajuste aprobada, sin editar directamente la existencia. |
| INV-AC-009 | Ubicuo | El sistema debe calcular toda existencia consultada como suma de cantidades firmadas de movimientos válidos dentro del ámbito aprobado. |
| INV-AC-010 | Comportamiento no deseado | Si una solicitud intenta establecer stock, sobrescribir stock o cambiarlo mediante CRUD de artículo sin registrar un movimiento, entonces el sistema debe rechazarla y mantener intactas la existencia y los movimientos. |
| INV-AC-011 | Comportamiento no deseado | Si una salida o ajuste produce stock negativo en su ámbito, entonces el sistema debe rechazar el movimiento y no registrar una mutación parcial. |
| INV-AC-012 | Comportamiento no deseado | Si un movimiento referencia un artículo inexistente, entonces el sistema debe rechazarlo y no registrar movimiento ni alterar existencias. |
| INV-AC-013 | Comportamiento no deseado | Si la política aprobada exige lote para el movimiento y el lote falta, no existe, no corresponde al artículo o no corresponde al ámbito aplicable, entonces el sistema debe rechazar el movimiento sin mutación parcial. |
| INV-AC-014 | Comportamiento no deseado | Si la cantidad, unidad, precisión o referencia de un movimiento no cumple las reglas aprobadas, entonces el sistema debe rechazarlo y no cambiar la existencia. |
| INV-AC-015 | Comportamiento no deseado | Si operaciones concurrentes sobre la misma existencia podrían producir un resultado negativo, entonces el sistema debe aceptar como máximo las operaciones compatibles con el stock disponible y rechazar el resto. |
| INV-AC-016 | Ubicuo | El sistema debe conservar para cada movimiento aceptado los datos históricos necesarios para identificar su artículo, tipo, cantidad/unidad, referencias aplicables y momento, sin que una edición o baja posterior borre esa traza. |
| INV-AC-017 | Estado | Mientras un artículo tenga un punto de reorden configurado y una existencia calculable en unidad y ámbito comparables, el sistema debe identificarlo como bajo reorden cuando la existencia sea menor que el punto de reorden aprobado. |
| INV-AC-018 | Evento | Cuando un actor autorizado consulta existencias, el sistema debe devolver un valor calculado a partir de movimientos y señalar el ámbito y unidad a los que corresponde. |
| INV-AC-019 | Evento | Cuando un actor autorizado consulta artículos bajo reorden, el sistema debe devolver únicamente artículos cuya existencia calculada cumpla la regla de reorden aprobada. |
| INV-AC-020 | Comportamiento no deseado | Si un actor carece de autorización para una operación, entonces el sistema debe denegarla y no alterar artículos, movimientos ni existencias. |

## Fuera de alcance y límites

Interfaz de inventario, compras automáticas, caducidades, traslados, datos reales, PHI, SSO/OIDC, piloto/producción y purga ejecutable. Los productos y umbrales de demostración son sintéticos, no decisiones empresariales para clínicas reales. Ver `plan.md`, `tasks.md` y README del módulo para evidencia y límites operativos.
