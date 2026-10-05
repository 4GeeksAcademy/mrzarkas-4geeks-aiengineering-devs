# OperationalIncident — Management de configuración y datos de referencia

**Estado:** M1–M6 implementados de forma provisional; validación funcional y M0 pendientes
**Fecha:** 2026-09-28
**Ámbito:** administración de catálogos, maestros contextuales y `ComplianceReview`.
**Tareas:** [`OperationalIncident-management-tasks.md`](./OperationalIncident-management-tasks.md)
**Implementación:** [`OperationalIncident-management-implementation.md`](./OperationalIncident-management-implementation.md)

## 1. Propósito

El Management permite mantener la configuración operativa sin modificar código
ni destruir trazabilidad histórica. No es un gestor clínico: no admite PHI,
historias clínicas ni documentos de pacientes.

Durante desarrollo y pruebas se usarán exclusivamente fixtures sintéticos. La
carga de datos reales requiere autorización explícita antes de piloto.

## 2. Recursos administrables

| Recurso | Acciones |
|---|---|
| Catálogos de incidencia | listar, crear valor, editar etiqueta/descripción, activar/desactivar, cambiar vigencia y orden |
| Jurisdicciones | listar; cambios restringidos y auditados |
| Clínicas | listar, alta, edición, activar/desactivar; cada clínica pertenece a una jurisdicción |
| Sistemas afectados | listar, alta, edición, activar/desactivar, asignar cobertura por jurisdicción |
| Áreas responsables | listar, alta, edición, activar/desactivar |
| ComplianceReview | crear, consultar, cambiar estado; asociación validada a una incidencia |

No se permitirá la eliminación física de un valor usado históricamente.

## 3. Autorización

La autorización se aplica en backend mediante capacidades. Hasta que se valide
la matriz funcional, sólo `admin` puede modificar configuración.

La propuesta completa de M0, con los cuatro roles principales y las áreas
operativas con alcance propio, está en
[`proposals.md`](../proposals.md#propuesta-m0-matriz-funcional-de-roles-y-capacidades).
Es una propuesta pendiente: la tabla siguiente describe la implementación
provisional actual, no una aprobación de producción.

| Capacidad | admin | Tecnología | Cumplimiento | Dirección | Área responsable |
|---|---:|---:|---:|---:|---:|
| `catalog:read` | Sí | Sí | Sí | No | Sí, para formularios |
| `catalog:manage` | Sí | Pendiente | Pendiente | No | No |
| `referenceData:read` | Sí | Sí | Sí | No | Sí, según formulario |
| `referenceData:manage` | Sí | Pendiente | Pendiente | No | No |
| `complianceReview:read` | Sí | Según caso | Sí | No | No |
| `complianceReview:manage` | Sí | No | Sí | No | No |

Dirección recibe métricas y listados resumidos; no obtiene endpoints de
administración ni detalle de revisiones.

## 4. Ciclo de vida e integridad

- `key` e `id` son estables y no cambian.
- `label`, `description`, orden y vigencia pueden cambiarse con auditoría.
- Un valor `isActive=false` no se acepta en altas ni reasignaciones nuevas.
- Los registros históricos siguen resolviendo su identificador y etiqueta.
- Un cambio semántico (dividir, fusionar o reasignar el significado de un
  valor) exige migración, mapeo de históricos y revisión de impacto.
- Una clínica debe pertenecer a una jurisdicción.
- Un sistema sólo puede asociarse a incidencias de jurisdicciones que cubre.
- Una revisión de Cumplimiento debe pertenecer a la misma jurisdicción que la
  incidencia asociada.

## 5. Auditoría

Toda operación de Management genera un evento inmutable con:

- tipo de recurso e identificador;
- operación (`created`, `updated`, `activated`, `deactivated`, `coverageChanged`, `statusChanged`);
- actor autenticado y UTC del servidor;
- valores anterior y nuevo minimizados;
- motivo obligatorio para desactivación, cambio semántico o cierre;
- identificador técnico de correlación.

Los eventos no incluyen PHI ni payloads completos de incidencias. El acceso a
auditoría se restringe a `audit:read`.

## 6. Contrato API propuesto

```text
GET    /management/catalogs
POST   /management/catalogs/{catalogName}/values
PATCH  /management/catalogs/{catalogName}/values/{valueId}
POST   /management/catalogs/{catalogName}/values/{valueId}/activation

GET    /management/reference-data/{resource}
POST   /management/reference-data/{resource}
PATCH  /management/reference-data/{resource}/{id}
POST   /management/reference-data/{resource}/{id}/activation
PUT    /management/affected-systems/{id}/jurisdictions

POST   /compliance-reviews
GET    /compliance-reviews/{id}
PATCH  /compliance-reviews/{id}/status

GET    /management/audit-events?resourceType=&resourceId=
```

Todas las listas son paginadas. Las mutaciones usan UUID, nunca etiquetas
arbitrarias. Las respuestas de error no exponen contenido sensible.

## 7. Validación de entrada

- `key`: formato técnico, única e inmutable.
- etiquetas y descripciones: límites de longitud y sin PHI.
- fechas: `effectiveFrom <= effectiveTo`.
- desactivación: no rompe referencias históricas.
- cambios de cobertura: no invalidan incidencias existentes sin plan de
  migración.
- cambios de `ComplianceReview`: jurisdicción compatible y actor autorizado.

## 8. Datos sintéticos y promoción

Los fixtures `dev-*` se mantienen en desarrollo y pruebas. No se promueven a
staging o producción. La promoción de datos aprobados requiere:

1. fuente propietaria identificada;
2. revisión de Tecnología y Cumplimiento;
3. importación versionada y reversible;
4. validación de referencias existentes;
5. evidencia de auditoría y rollback.

## 9. Criterios de aceptación

- Un `admin` puede administrar recursos y deja auditoría verificable.
- Un rol no autorizado recibe `403`.
- Un valor inactivo se rechaza para nuevas incidencias.
- No existe borrado físico de valores con uso histórico.
- Las asociaciones clínica/jurisdicción, sistema/jurisdicción y
  incidencia/revisión se validan.
- Las operaciones de Management y sus pruebas no usan datos reales.
- La UI consume listas y permisos desde API, sin etiquetas hardcodeadas.
