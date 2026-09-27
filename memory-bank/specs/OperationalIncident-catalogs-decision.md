# OperationalIncident — Decisión de catálogos

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Estado:** Propuesta preparada; pendiente de validación funcional  
**Versión:** 0.1  
**Fecha:** 2026-09-26  
**Referencias:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md), [`OperationalIncident-tasks.md`](./OperationalIncident-tasks.md), [`OperationalIncident-status.md`](./OperationalIncident-status.md)

## 1. Objetivo

Permitir que el desarrollo avance con identificadores técnicos estables y etiquetas provisionales configurables. La aprobación posterior de los nombres visibles no deberá obligar a reescribir las incidencias existentes.

Esta propuesta no fija todavía los valores de negocio como definitivos. Requiere validación de Tecnología y de las áreas funcionales correspondientes antes de pasar a producción.

## 2. Reglas de configuración

Cada catálogo tendrá un nombre técnico estable. Cada valor tendrá:

- `key`: identificador técnico estable.
- `label`: etiqueta visible configurable.
- `description`: descripción operativa configurable.
- `isActive`: habilitado para nuevas incidencias.
- `sortOrder`: orden de presentación.
- `version`: versión de la configuración.
- `effectiveFrom`: inicio de vigencia.
- `effectiveTo`: fin de vigencia opcional.
- `createdAt`, `createdBy`, `updatedAt`, `updatedBy`.

Reglas:

1. La UI consume los valores desde la API.
2. La UI no codifica etiquetas ni decide reglas de negocio.
3. Un cambio de etiqueta conserva el `key` y no requiere migrar incidencias.
4. Un valor utilizado históricamente no se elimina físicamente.
5. Un valor inactivo no puede utilizarse en nuevas incidencias.
6. Los valores históricos siguen siendo legibles.
7. Un cambio semántico requiere migración, mapeo y auditoría.

## 3. Catálogos y valores provisionales

### 3.1 `entryChannel`

| `key` | Etiqueta provisional | Activo |
|---|---|---:|
| `clinicPhone` | Teléfono de clínica | Sí |
| `email` | Correo electrónico | Sí |
| `backofficeForm` | Formulario de backoffice | Sí |
| `technicalMonitoring` | Monitorización técnica | Sí |
| `internalEscalation` | Escalado interno | Sí |
| `other` | Otro | Sí |

### 3.2 `incidentType`

| `key` | Etiqueta provisional | Activo |
|---|---|---:|
| `systemAvailability` | Disponibilidad del sistema | Sí |
| `performanceDegradation` | Degradación de rendimiento | Sí |
| `functionalError` | Error funcional | Sí |
| `integration` | Integración | Sí |
| `accessOrAuthentication` | Acceso o autenticación | Sí |
| `dataOrSynchronization` | Datos o sincronización | Sí |
| `complianceOrAudit` | Cumplimiento o auditoría | Sí |
| `billingOrClaim` | Facturación o reclamación | Sí |
| `appointmentOrScheduling` | Citas y agenda | Sí |

### 3.3 `severity`

| `key` | Etiqueta provisional | Activo |
|---|---|---:|
| `critical` | Crítica | Sí |
| `high` | Alta | Sí |
| `medium` | Media | Sí |
| `low` | Baja | Sí |

### 3.4 `incidentStatus`

| `key` | Etiqueta provisional | `isOpen` | Activo |
|---|---|---:|---:|
| `new` | Nueva | Sí | Sí |
| `underAnalysis` | En análisis | Sí | Sí |
| `assigned` | Asignada | Sí | Sí |
| `inResolution` | En resolución | Sí | Sí |
| `resolved` | Resuelta | No | Sí |
| `closed` | Cerrada | No | Sí |
| `onHold` | En espera | Sí | Sí |
| `reopened` | Reabierta | Sí | Sí |
| `cancelled` | Cancelada | No | Sí |

## 4. Decisiones que deben validar los responsables

### Tecnología

- [ ] Acepta el formato de identificadores y valores.
- [ ] Acepta la administración mediante PostgreSQL y migraciones.
- [ ] Confirma que `key` será el identificador utilizado por API y persistencia.
- [ ] Confirma la gestión de versiones y concurrencia.

### Áreas funcionales

- [ ] Confirman que los tipos cubren los casos operativos.
- [ ] Confirman que los canales representan los puntos reales de entrada.
- [ ] Confirman la nomenclatura visible.

### Cumplimiento y Gobierno del Dato

- [ ] Revisa la trazabilidad de cambios de catálogo.
- [ ] Revisa la retención de valores históricos.
- [ ] Revisa permisos de administración.
- [ ] Revisa que las descripciones no incentiven el registro de PHI.

## 5. Regla de aprobación

Esta propuesta sólo podrá marcarse como **Validada** cuando exista evidencia de revisión por los responsables definidos. Hasta entonces, los valores son utilizables únicamente como configuración provisional de desarrollo y pruebas.

Una aprobación parcial debe indicar explícitamente qué catálogo o regla queda validado y cuál permanece pendiente.

## 6. Evidencia

| Fecha | Revisor | Alcance | Resultado | Referencia |
|---|---|---|---|---|
| 2026-09-26 | Pendiente | Propuesta inicial | Pendiente de validación | Este documento |
