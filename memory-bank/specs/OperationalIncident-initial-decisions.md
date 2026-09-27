# OperationalIncident — Decisiones de fase inicial

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Fase:** Inicial — configuración y decisiones  
**Versión:** 0.1  
**Fecha:** 2026-09-26  
**Estado:** Cierre condicionado; aprobación de responsables diferida a controles de salida

## 1. Propósito

Este documento consolida las decisiones operativas necesarias antes de iniciar la implementación de PostgreSQL y la API. Los catálogos mantienen identificadores estables y etiquetas configurables según [`OperationalIncident-catalogs-decision.md`](./OperationalIncident-catalogs-decision.md).

Se autoriza avanzar a la Fase 1 con decisiones provisionales. Este cierre es condicionado: no representa aprobación funcional o normativa y las validaciones pendientes deben completarse antes de producción.

## 2. Estados y transiciones

### 2.1 Estados iniciales

| `key` | Etiqueta | `isOpen` | Final |
|---|---|---:|---:|
| `new` | Nueva | Sí | No |
| `underAnalysis` | En análisis | Sí | No |
| `assigned` | Asignada | Sí | No |
| `inResolution` | En resolución | Sí | No |
| `onHold` | En espera | Sí | No |
| `reopened` | Reabierta | Sí | No |
| `resolved` | Resuelta | No | Sí |
| `closed` | Cerrada | No | Sí |
| `cancelled` | Cancelada | No | Sí |

### 2.2 Transiciones propuestas

| Origen | Destino | Permitida | Condición |
|---|---|---:|---|
| `new` | `underAnalysis` | Sí | Existe un actor autorizado |
| `new` | `cancelled` | Sí | Motivo obligatorio |
| `underAnalysis` | `assigned` | Sí | Área responsable asignada |
| `underAnalysis` | `onHold` | Sí | Motivo obligatorio |
| `assigned` | `inResolution` | Sí | Área responsable válida |
| `assigned` | `onHold` | Sí | Motivo obligatorio |
| `inResolution` | `resolved` | Sí | Resolución documentada sin PHI |
| `inResolution` | `onHold` | Sí | Motivo obligatorio |
| `onHold` | `underAnalysis` | Sí | Revisión retomada |
| `onHold` | `inResolution` | Sí | Área responsable mantiene el control |
| `resolved` | `closed` | Sí | Cierre autorizado |
| `resolved` | `reopened` | Sí | Motivo obligatorio |
| `reopened` | `underAnalysis` | Sí | Nueva revisión iniciada |
| `closed` | `reopened` | Pendiente | Requiere aprobación de negocio |
| `cancelled` | `reopened` | Pendiente | Requiere aprobación de negocio |

### 2.3 Reglas

- Toda transición debe validarse en backend.
- La UI sólo presenta las transiciones que el backend devuelve como permitidas.
- `resolved`, `closed` y `cancelled` no cuentan como abiertas.
- `onHold` y `reopened` cuentan como abiertas.
- Los motivos son obligatorios para `cancelled`, `onHold` y `reopened`.
- Cada transición genera historial y auditoría en la misma transacción.
- El cierre no elimina ni archiva físicamente la incidencia.

## 3. Permisos propuestos

Los permisos se expresan como capacidades y deben mapearse al mecanismo de autenticación que exista en el monorepo.

| Capacidad | Tecnología | Área responsable | Cumplimiento | Dirección |
|---|---:|---:|---:|---:|
| `incident:create` | Sí | Sí | Sí | Pendiente |
| `incident:list` | Sí | Sí, según alcance | Sí | Agregado |
| `incident:read` | Sí | Sí, según alcance | Sí | Agregado |
| `incident:update` | Sí | Propia o autorizada | Según caso | No por defecto |
| `incident:changeSeverity` | Sí | Responsable/autorizado | Sí | No por defecto |
| `incident:transition` | Sí | Responsable/autorizado | Sí | No por defecto |
| `incident:assign` | Sí | No por defecto | Sí | No por defecto |
| `incident:close` | Sí | Responsable/autorizado | Sí | No por defecto |
| `incident:reopen` | Sí | No por defecto | Sí | No por defecto |
| `catalog:manage` | Sí | No | Sí, revisión | No |
| `audit:read` | Sí | Restringido | Sí | Restringido |
| `complianceReview:read` | Según autorización | No por defecto | Sí | Restringido |

### Reglas de autorización

- La autorización se aplica en backend; ocultar un botón no es suficiente.
- El actor no puede asignar una incidencia fuera de su alcance sin permiso explícito.
- Dirección recibe agregados por defecto, no descripciones completas.
- Cumplimiento puede acceder a incidencias escaladas y a la trazabilidad necesaria.
- La administración de catálogos queda restringida a usuarios autorizados de Tecnología y Cumplimiento.

## 4. Política de datos y no-PHI

### Permitido

- Sistema afectado.
- Clínica y jurisdicción.
- Síntoma operativo.
- Hora de inicio del fallo.
- Impacto agregado en el servicio.
- Acciones técnicas realizadas.
- Referencia interna no clínica.

### No permitido

- Nombre, dirección, teléfono o correo del paciente.
- Identificadores de paciente, historia clínica o reclamación clínica.
- Diagnósticos, notas clínicas o resultados médicos.
- Información médica no necesaria para restaurar el servicio.
- Capturas que contengan datos de pacientes.

### Reglas de implementación

- Título y descripción tendrán límites de longitud configurables.
- El formulario mostrará una advertencia de no incluir PHI.
- El backend validará la estructura, pero no se considerará un detector perfecto de PHI.
- Si se detecta o reporta posible PHI, se restringirá el acceso y se escalará a Cumplimiento según el procedimiento aprobado.
- Logs, errores y métricas no incluirán el contenido completo de título o descripción.
- La retención se definirá con Cumplimiento antes del piloto.

## 5. Auditoría y retención

### Eventos mínimos

- Creación.
- Edición.
- Cambio de severidad.
- Cambio de estado.
- Cambio de área responsable.
- Asociación o modificación de `ComplianceReview`.
- Cierre y reapertura.
- Cambio de configuración de catálogo.
- Administración de permisos relacionada con la incidencia.

### Campos de cada evento

- Identificador del evento.
- Incidencia, cuando aplique.
- Tipo de evento.
- Actor.
- Marca temporal UTC generada por servidor.
- Campo afectado, cuando aplique.
- Valor anterior y nuevo, minimizados y protegidos.
- Motivo, cuando aplique.
- Identificador de correlación técnico, sin payload sensible.

### Reglas

- El historial de estado y responsable es inmutable desde la aplicación.
- El evento y el cambio descrito se confirman en una única transacción.
- La auditoría debe poder consultarse por usuarios autorizados.
- La retención exacta queda pendiente de aprobación de Cumplimiento.
- No se purgan eventos necesarios para obligaciones legales o investigaciones activas.

## 6. PostgreSQL, migraciones y recuperación

### Decisión inicial

- PostgreSQL gestionado será la persistencia inicial.
- La API se conectará mediante secretos gestionados fuera del repositorio.
- El esquema evolucionará mediante migraciones versionadas.
- Los seeds de catálogo serán reproducibles e idempotentes.
- Las operaciones de cambio de estado, asignación e historial serán transaccionales.

### Entornos mínimos

- Desarrollo.
- Pruebas.
- Staging.
- Producción.

Cada entorno debe tener credenciales, datos y permisos separados.

### Requisitos de recuperación

- Backups automáticos gestionados.
- Retención definida por Tecnología y Cumplimiento.
- Cifrado en tránsito y en reposo conforme a la infraestructura aprobada.
- Prueba de restauración en entorno no productivo antes del piloto.
- Registro de resultado de la restauración.
- Procedimiento para rollback de migraciones cuando sea viable.

### Pendientes técnicos

- Herramienta concreta de migraciones.
- Proveedor y configuración de PostgreSQL gestionado.
- RPO y RTO.
- Retención de backups.
- Usuarios y roles de base de datos.
- Política de acceso de producción.

## 7. Criterios de validación de la fase

La fase inicial queda validada internamente cuando:

- Los catálogos tienen `key`, etiqueta, activación y vigencia definidos.
- Las transiciones e `isOpen` están documentados.
- Los permisos están documentados.
- La política de no-PHI está documentada.
- La auditoría y sus eventos están definidos.
- PostgreSQL, migraciones y recuperación tienen una decisión inicial.
- No existen contradicciones con `CONTEXT.md` ni con `OperationalIncident-specs.md`.

La fase queda **completamente cerrada** sólo cuando, además, exista aprobación registrada de Tecnología y Cumplimiento para los puntos que les corresponden.

## 8. Aprobaciones y controles de salida

| Responsable | Alcance | Estado | Evidencia |
|---|---|---|---|
| Tecnología | Catálogos técnicos, PostgreSQL, migraciones, permisos técnicos | Pendiente | — |
| Cumplimiento y Gobierno del Dato | No-PHI, auditoría, retención, acceso y `ComplianceReview` | Pendiente | — |
| Áreas funcionales | Canales, tipos, severidades, estados y flujo operativo | Pendiente | — |

Estas aprobaciones quedan diferidas. La Fase 1 puede comenzar, pero no se podrá habilitar producción ni cerrar el control de salida mientras alguno de estos estados permanezca pendiente.

## 9. Condiciones para continuar

- Usar los valores actuales sólo como configuración provisional de desarrollo, pruebas y staging.
- Mantener migraciones reversibles y seeds reproducibles.
- No fijar los valores provisionales como contrato definitivo de negocio.
- Registrar cualquier cambio de catálogo, estado o permiso.
- Revisar y resolver todas las aprobaciones pendientes antes del piloto o producción.
