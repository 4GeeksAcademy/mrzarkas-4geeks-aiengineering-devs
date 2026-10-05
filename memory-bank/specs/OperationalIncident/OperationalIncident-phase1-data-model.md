# OperationalIncident — Fase 1: modelo de datos PostgreSQL

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Fase:** 1 — PostgreSQL y modelo  
**Estado:** Diseño inicial preparado; Alembic/SQLAlchemy y configuración por entorno confirmados; implementación pendiente  
**Fecha:** 2026-09-26  
**Referencias:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md), [`OperationalIncident-implementation.md`](./OperationalIncident-implementation.md), [`OperationalIncident-status.md`](./OperationalIncident-status.md)

## 1. Objetivo

Definir el modelo relacional inicial para persistir `OperationalIncident`, sus catálogos configurables, historiales y auditoría, utilizando PostgreSQL gestionado.

Este documento es un diseño de Fase 1. No implica que las tablas o migraciones hayan sido implementadas.

## 2. Principios

- Usar identificadores internos estables, preferiblemente UUID si la infraestructura aprobada no establece otra convención.
- Mantener `incidentIdentifier` como referencia pública estable y legible.
- No almacenar etiquetas visibles como claves de negocio.
- No borrar físicamente valores de catálogo utilizados por registros históricos.
- Guardar marcas temporales en UTC.
- Generar autores y marcas temporales en servidor.
- Mantener operaciones de negocio e historial en la misma transacción.
- Evitar PHI en las columnas operativas y en los eventos de auditoría.
- Añadir índices sólo para consultas justificadas por el listado y las métricas.

## 3. Catálogos

### 3.1 `catalog`

| Campo lógico | Tipo PostgreSQL propuesto | Nulo | Regla |
|---|---|---:|---|
| `id` | `uuid` | No | PK |
| `catalog_name` | `varchar(100)` | No | Único |
| `version` | `integer` | No | Mayor que cero |
| `is_active` | `boolean` | No | Por defecto `true` |
| `created_at` | `timestamptz` | No | UTC, servidor |
| `created_by` | `uuid` | No | Actor técnico o de sistema |
| `updated_at` | `timestamptz` | No | UTC, servidor |
| `updated_by` | `uuid` | No | Actor técnico o de sistema |

### 3.2 `catalog_value`

| Campo lógico | Tipo PostgreSQL propuesto | Nulo | Regla |
|---|---|---:|---|
| `id` | `uuid` | No | PK |
| `catalog_id` | `uuid` | No | FK a `catalog` |
| `key` | `varchar(100)` | No | Único dentro del catálogo |
| `label` | `varchar(200)` | No | Etiqueta configurable |
| `description` | `varchar(1000)` | Sí | Sin PHI |
| `is_active` | `boolean` | No | Por defecto `true` |
| `is_open` | `boolean` | Sí | Sólo para `incidentStatus` |
| `sort_order` | `integer` | No | Mayor o igual que cero |
| `effective_from` | `timestamptz` | No | Inicio de vigencia |
| `effective_to` | `timestamptz` | Sí | Posterior a inicio |
| `created_at` | `timestamptz` | No | UTC, servidor |
| `created_by` | `uuid` | No | Actor técnico o de sistema |
| `updated_at` | `timestamptz` | No | UTC, servidor |
| `updated_by` | `uuid` | No | Actor técnico o de sistema |

Restricciones:

- `UNIQUE (catalog_id, key)`.
- `sort_order >= 0`.
- `effective_to IS NULL OR effective_to >= effective_from`.
- `is_open` debe ser `NULL` para catálogos que no sean `incidentStatus`, o debe validarse en la capa de dominio si la restricción SQL no puede expresarse sin trigger.
- Valores utilizados desde una incidencia no se eliminan físicamente.

## 4. Entidades contextuales y referencias maestras

Las entidades contextuales son referencias a datos maestros de HealthCore. Por ejemplo, `Clinic` representa una de las 12 clínicas; `Reporter` representa la identidad que reporta; `AffectedSystem` representa un sistema tecnológico; y `responsible_area` representa un área organizativa. No son catálogos de etiquetas de la incidencia.

El contexto actual no proporciona tablas maestras implementadas para `Clinic`, `Reporter`, `AffectedSystem`, `Jurisdiction` o áreas responsables. La decisión provisional de Fase 1 es no duplicar esos maestros dentro del gestor:

1. Mantener identificadores estables y validar su existencia contra la API central o maestro propietario.
2. Crear foreign keys locales únicamente cuando las tablas maestras estén en la misma base de datos y exista un propietario confirmado.
3. Crear tablas maestras mínimas en este módulo sólo mediante una decisión posterior explícita.

Por tanto, el modelo documenta contratos de referencia, pero no autoriza todavía foreign keys hacia tablas inexistentes. No se deben inventar datos reales de las 12 clínicas ni de empleados en producción sin una fuente aprobada.

## 5. `operational_incident`

| Campo lógico | Tipo PostgreSQL propuesto | Nulo | Regla |
|---|---|---:|---|
| `id` | `uuid` | No | PK |
| `incident_identifier` | `varchar(40)` | No | Único, generado por servidor |
| `title` | `varchar(200)` | No | No vacío |
| `description` | `text` | No | Límite aplicado por API |
| `reporter_id` | `uuid` | No | Referencia a `Reporter` o identidad aprobada |
| `clinic_id` | `uuid` | No | Referencia a `Clinic` |
| `jurisdiction_id` | `uuid` | No | `US` o `UK` inicialmente |
| `affected_system_id` | `uuid` | No | Referencia a `AffectedSystem` |
| `entry_channel_value_id` | `uuid` | No | Valor de `entryChannel` |
| `incident_type_value_id` | `uuid` | No | Valor de `incidentType` |
| `severity_value_id` | `uuid` | No | Valor de `severity` |
| `status_value_id` | `uuid` | No | Valor actual de `incidentStatus` |
| `responsible_area_id` | `uuid` | No | Área contextual |
| `compliance_review_id` | `uuid` | Sí | Referencia cuando aplique |
| `created_at` | `timestamptz` | No | UTC, servidor |
| `created_by` | `uuid` | No | Actor |
| `updated_at` | `timestamptz` | No | UTC, servidor |
| `updated_by` | `uuid` | No | Actor |

Restricciones e índices:

- `UNIQUE (incident_identifier)`.
- Campos obligatorios no nulos.
- Índices para `status_value_id`, `severity_value_id`, `responsible_area_id`, `created_at` y `updated_at`.
- Índice compuesto para la consulta de abiertas por severidad, según el plan de ejecución validado.
- No incluir índices de texto completo hasta justificar la necesidad y sus implicaciones de privacidad.

## 6. Historial de estado

### `incident_status_history`

| Campo lógico | Tipo | Regla |
|---|---|---|
| `id` | `uuid` | PK |
| `incident_id` | `uuid` | FK obligatoria |
| `previous_status_value_id` | `uuid` | Nullable sólo para alta inicial |
| `new_status_value_id` | `uuid` | Obligatorio |
| `reason` | `varchar(1000)` | Según transición |
| `changed_at` | `timestamptz` | UTC, servidor |
| `changed_by` | `uuid` | Actor |

Índices: `(incident_id, changed_at)`.

## 7. Historial de responsable

### `incident_assignment_history`

| Campo lógico | Tipo | Regla |
|---|---|---|
| `id` | `uuid` | PK |
| `incident_id` | `uuid` | FK obligatoria |
| `previous_area_id` | `uuid` | Nullable sólo para asignación inicial |
| `new_area_id` | `uuid` | Obligatorio |
| `reason` | `varchar(1000)` | Según política |
| `assigned_at` | `timestamptz` | UTC, servidor |
| `assigned_by` | `uuid` | Actor |

Índices: `(incident_id, assigned_at)`.

## 8. Auditoría

### `incident_audit_event`

| Campo lógico | Tipo | Regla |
|---|---|---|
| `id` | `uuid` | PK |
| `incident_id` | `uuid` | Nullable para cambios de catálogo global |
| `event_type` | `varchar(100)` | Catálogo técnico de eventos |
| `field_name` | `varchar(100)` | Nullable |
| `previous_value` | `jsonb` | Minimizado |
| `new_value` | `jsonb` | Minimizado |
| `occurred_at` | `timestamptz` | UTC, servidor |
| `actor_id` | `uuid` | Actor |
| `correlation_id` | `uuid` | Trazabilidad técnica |
| `metadata` | `jsonb` | Sin payload completo ni PHI |

La auditoría se insertará en la misma transacción que la operación descrita. El acceso a esta tabla debe restringirse y auditarse.

## 9. Transacciones

Las siguientes operaciones deben ser atómicas:

- Crear incidencia + estado inicial + asignación inicial + auditoría.
- Cambiar estado + historial de estado + auditoría.
- Cambiar responsable + historial de asignación + auditoría.
- Editar campos + auditoría.
- Cambiar configuración + auditoría de catálogo.

Si una parte falla, ninguna parte del cambio debe confirmarse.

## 10. Migraciones, seeds y configuración

La herramienta de migraciones será **Alembic integrado con SQLAlchemy**. La estrategia es:

1. Migración de extensiones y tipos auxiliares aprobados.
2. Migración de tablas de catálogos.
3. Seed idempotente de catálogos provisionales.
4. Migración de tablas contextuales o contratos de referencia.
5. Migración de `operational_incident`.
6. Migración de historiales y auditoría.
7. Migración de índices y restricciones.
8. Prueba desde base limpia.
9. Prueba de rollback o procedimiento de recuperación documentado.

Los seeds deben hacer `upsert` por `catalog_name` y `key`, actualizar etiquetas sólo mediante una operación de configuración explícita y no reactivar valores deshabilitados accidentalmente.

La conexión al PostgreSQL gestionado se configurará mediante variables de entorno. Para desarrollo local se prevé un `.env` excluido de Git y un `.env.example` sin secretos. Las credenciales no deben aparecer en código, migraciones, seeds, logs ni documentación versionada.

## 11. Criterios de salida de Fase 1

- [ ] Estrategia de tablas maestras contextual validada.
- [ ] Esquema relacional revisado.
- [ ] Herramienta de migraciones confirmada.
- [ ] Migración inicial implementada.
- [ ] Seeds provisionales implementados e idempotentes.
- [ ] Restricciones e índices implementados.
- [ ] Transacciones de historial definidas.
- [ ] Prueba desde base limpia ejecutada.
- [ ] Prueba de restauración ejecutada en entorno no productivo.
- [ ] Validaciones diferidas de la fase inicial revisadas antes de producción.
- [ ] `OperationalIncident-status.md` actualizado con evidencia.
