# Decisión revisable — eventos sin dominio implementado

Estado: aplazamiento aprobado expresamente por el desarrollador («apruebo»). Rama feature/telemetryEventCapture. Contrato1.2.0 conserva los39 tipos. No código, claves, datos, infraestructura ni Memory Bank/Rules modificados por esta propuesta.

**Reentrada 2026-11-02:** inventario ya tiene implementación. TASK-TEL-030 se reabre con fuentes y diseño en [inventory-producers.md](./inventory-producers.md); no se declara captura implementada. La ausencia de inventario descrita debajo corresponde a la decisión histórica. Los motores/agregadores siguen sin fuente; la reentrada no satisface TEL-FR-018 ni extiende las aprobaciones anteriores a cambios protegidos futuros.

## Evidencia actual

Revisión del árbol completo con rg --files y de los routers/modelos backend/app, backoffice y catálogo SDD. Hay incidencias, maestros, Compliance, catálogos, auth y telemetría; no inventario/pedidos, motores de alertas/notificaciones/jobs ni fuentes de KPI clínicos/departamentales. memory-bank/specs/inventory-manager contiene spec/plan/tasks, sin implementación. scripts/caching_inventory.py es un inventario técnico de caché, no existencias de productos. data/pipelines sólo tiene README; no acredita un pipeline ejecutable. La landing frontend no acredita dominios clínicos.

Fuentes: docs/specs/telemetry-event-capture/spec.md matriz T-CAT-001–039, remaining-producers.md; backend/app árbol real; prompt original TEL-FR-018. Las clasificaciones obligatorias se conservan, no se rebajan por faltar fuente.

## Disposición propuesta por evento

Los20 eventos pasan a DEFERRED_NO_SOURCE para esta entrega por aprobación expresa; ninguno pasa a IMPLEMENTED/DONE ni requisito cumplido.

| Evento | Clasificación del catálogo | Fuente necesaria para retomarlo |
|---|---|---|
| inbound_order_completed | Obligatorio ejercicio | Movimientos de entrada confirmados mediante commit |
| outbound_order_completed | Obligatorio ejercicio | Movimientos de salida confirmados mediante commit |
| inventory_validation_failed | Obligatorio ejercicio | Validador explícito del dominio de inventario |
| stock_direct_update_rejected | Obligatorio ejercicio | Detección de escritura directa de stock |
| inventory_threshold_activated | Obligatorio ejercicio | Stock derivado, umbral y episodios aprobados |
| inventory_viewed | Oportunidad | Consulta autorizada de existencias |
| product_selected | Oportunidad | Flujo de selección de artículo |
| order_started | Oportunidad | Inicio lógico de entrada/salida |
| order_abandoned | Oportunidad | Lifecycle de flujo y política de inactividad |
| inventory_adjustment_completed | Oportunidad | Ajuste mediante movimientos y auditoría |
| inventory_threshold_cleared | Oportunidad | Cierre de episodio de umbral |
| inventory_reconciliation_failed | Oportunidad | Reconciliación real de movimientos/existencias |
| alert_triggered | Obligatorio briefing | Motor de reglas, umbrales y episodios |
| notification_delivery_completed | Oportunidad | Entrega autorizada y ACK/resultado terminal de proveedor |
| job_run_completed | Oportunidad | Job real con inicio/final y resultado |
| appointment_period_aggregated | Obligatorio briefing | Fuente de citas/cohorte y cierre reconciliado |
| billing_period_aggregated | Obligatorio briefing | Fuente de facturación/cohorte y moneda separada |
| experience_period_aggregated | Obligatorio briefing | Encuestas/cohorte y agregación protegida |
| workforce_period_aggregated | Oportunidad | Fuente RRHH y agregación autorizada |
| clinical_workload_aggregated | Oportunidad | Fuente clínica agregada sin notas/personas |

Son20 eventos:9 obligatorios (5 ejercicio y4 briefing),11 oportunidades. Ninguno tiene fuente equivalente hoy. Un error422 de incidencias no es validación de inventario; un sampler de caché no es job de negocio; un fallo técnico no es episodio de alerta; métricas de tickets no son KPI de citas/facturación/satisfacción.

## Decisión recomendada

Aplazar los20 productores hasta construir y aprobar sus fuentes, manteniendo nombres/esquemas/requisitos y criterios pendientes. No construir dominios completos dentro del hito de captura por inferencia ni crear eventos ficticios para aparentar cobertura.

El alcance de entrega técnica pasa a ser captura/receptor y19 tipos con productor al menos parcial en aplicaciones existentes. La aprobación de este aplazamiento NO satisface TEL-FR-018 ni la cobertura obligatoria original: la entrega debe declarar explícitamente esas brechas y no presentarse como cumplimiento integral del prompt. El cierre del alcance reducido necesita además verificar sus propias coberturas pendientes.

## Pendientes dentro de los19 tipos actuales

- Diagnósticos frontend de contrato/entrega: backend implementado, frontend sigue pendiente; revisar sin recursión y política de descarte.
- api_request_completed: sólo cuatro lecturas de incidencias; otras rutas no instrumentadas.
- audit_accessed: sólo incidencia y Management filtrado por clínica activa; consultas globales/otros contextos pendientes.
- management_mutation_completed: sólo clínicas; otros maestros y Compliance sin productor.
- authorization_denied: sólo capacidad explícita; denegaciones contextuales no cubiertas.
- service_health_checked: bajo demanda; sin sondeo externo/programado.
- data_integrity_checked: coherencia event_contract al arranque; references/historical_coverage pendientes.
- Activación/validación conjunta en servicios locales actuales, que aún no incorporan los últimos lotes; requiere autorización específica de reconstrucción.
- Revisión final SDD/evidencia sin contradicciones históricas, pruebas apropiadas y validate-delivery del alcance exacto. Commit/push/PR/producción no autorizados.

No confundir19 tipos con cobertura completa de19 requisitos. No prometer transporte externo, persistencia, retención, exactly-once o cumplimiento regulatorio.

## Reentrada al backlog

Para cada grupo: especificar e implementar su fuente en una tarea independiente autorizada; revisar contratos/disparadores y privacy/región con Tecnología y Cumplimiento cuando proceda; integrar productores tras commit/resultado real; ejecutar positivos, negativos, autorización, fallos y aislamiento regional. KPI requieren cohortes/denominadores/periodos y protección de agregados, no sólo modelos JSON. La aprobación de esta decisión no autoriza esas implementaciones futuras.

## Aprobación solicitada

El desarrollador confirmó el aplazamiento explícito de los20 eventos mediante «apruebo». Se conservan requisitos pendientes y contratos; no se declara cerrada la cobertura obligatoria. Siguiente lote recomendado: diagnósticos frontend en las superficies ya existentes, antes de revisión conjunta final.
