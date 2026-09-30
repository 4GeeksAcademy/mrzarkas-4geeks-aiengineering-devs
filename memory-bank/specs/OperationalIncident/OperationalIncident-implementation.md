# OperationalIncident — Implementation

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Especificación:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md)  
**Tareas:** [`OperationalIncident-tasks.md`](./OperationalIncident-tasks.md)  
**Estado:** Diseño de implementación preparado; código aún no iniciado  
**Fecha:** 2026-09-26

**Decisiones de infraestructura:** API FastAPI centralizada en `services/`, Alembic integrado con SQLAlchemy, `docker-compose.yml` en la raíz y configuración de PostgreSQL mediante variables de entorno.

## 1. Objetivo técnico

Implementar `OperationalIncident` como módulo de la API centralizada FastAPI, con PostgreSQL gestionado, validación Pydantic y un backoffice en `uis/`. El diseño debe permitir ajustar etiquetas de catálogo sin reescribir incidencias históricas y debe conservar la trazabilidad de estados, responsables y cambios relevantes.

No se implementará un microservicio independiente ni se añadirá una librería, un gestor de dependencias o un patrón nuevo sin una decisión documentada que lo justifique.

## 2. Arquitectura objetivo

```text
Backoffice (uis/)
        |
        | HTTP / contrato API
        v
API centralizada FastAPI
        |
        +-- módulo OperationalIncident
        |     +-- routers
        |     +-- schemas Pydantic
        |     +-- servicios de dominio
        |     +-- autorización
        |     +-- auditoría
        |     +-- repositorios
        |
        v
PostgreSQL gestionado
  +-- catálogos y versiones
  +-- operational incidents
  +-- historiales
  +-- auditoría
```

### Responsabilidades

| Componente | Responsabilidad |
|---|---|
| Backoffice | Presentación, interacción, filtros y consumo de catálogos; no decide reglas de negocio |
| Router FastAPI | HTTP, autenticación integrada, serialización y códigos de respuesta |
| Pydantic | Contratos, tipos, formatos, límites y validación estructural |
| Servicio de dominio | Transiciones, permisos, asignaciones, auditoría y reglas operativas |
| Repositorio | Consultas y escrituras transaccionales contra PostgreSQL |
| PostgreSQL | Integridad referencial, unicidad, índices y consistencia |
| Migraciones | Evolución versionada del esquema y datos iniciales |

## 3. Estructura propuesta

La ruta exacta debe adaptarse a la API que exista cuando comience el código. Como orientación:

```text
services/
  <central-api>/
    ...
    operational_incidents/
      README.md
      router.py
      schemas.py
      models.py
      repository.py
      service.py
      permissions.py
      catalog_service.py
      audit_service.py
      tests/
      alembic/
      alembic.ini
      pyproject.toml
      README.md
      README.es.md
    docker-compose.yml
```

Para la UI:

```text
uis/
  <backoffice>/
    ...
    operational-incidents/
      ...
```

Migraciones y seeds deben ubicarse en el servicio de la API centralizada y utilizar Alembic/SQLAlchemy. No se debe crear una segunda estrategia de migraciones. `docker-compose.yml` debe permanecer en la raíz, conforme a las convenciones del repositorio.

La conexión se leerá desde variables de entorno. En desarrollo local se podrá usar un fichero `.env` ignorado por Git y se documentará un `.env.example` sin valores sensibles.

## 4. Modelo de datos PostgreSQL

### 4.1 Catálogos

Se recomienda separar el catálogo lógico de sus valores y permitir versiones o vigencias explícitas:

```text
catalog
- id
- catalog_name
- version
- is_active
- created_at
- created_by
- updated_at
- updated_by

catalog_value
- id
- catalog_id
- key
- label
- description
- is_active
- is_open                 -- aplicable a incidentStatus
- sort_order
- effective_from
- effective_to
- created_at
- created_by
- updated_at
- updated_by
```

Restricciones mínimas:

- `catalog_name` único dentro del ámbito definido por la aplicación.
- `key` único dentro de un catálogo.
- `effective_from <= effective_to` cuando exista `effective_to`.
- Un valor utilizado por una incidencia no se elimina físicamente.
- Los valores inactivos no se aceptan en nuevas altas.
- Los valores históricos se mantienen consultables.

El modelo físico puede simplificarse si el sistema existente ya proporciona versionado de configuración, pero no debe perderse la capacidad de consultar el valor aplicado históricamente.

### 4.2 Referencias a datos maestros

`clinic_id`, `reporter_id`, `affected_system_id` y `responsible_area_id` son referencias a entidades maestras de HealthCore. El módulo no será inicialmente propietario de sus datos completos. Si el maestro vive en la misma base de datos, se podrán añadir foreign keys; si vive fuera, el servicio deberá validar el identificador mediante el contrato correspondiente.

No se crearán datos ficticios de clínicas, empleados o sistemas afectados como parte del seed de catálogos.

### 4.3 Incidencia

```text
operational_incident
- id
- incident_identifier
- title
- description
- reporter_id
- clinic_id
- jurisdiction_id
- affected_system_id
- entry_channel_value_id
- incident_type_value_id
- severity_value_id
- status_value_id
- responsible_area_id
- compliance_review_id       -- nullable
- created_at
- created_by
- updated_at
- updated_by
```

Requisitos:

- `incident_identifier` único y estable.
- Las relaciones a catálogos deben referenciar identificadores estables o filas versionadas según la decisión de persistencia.
- No se deben guardar etiquetas como sustituto de la relación.
- El título y la descripción deben tener límites de longitud.
- La descripción no debe contener PHI innecesaria.
- La eliminación física debe evitarse para conservar trazabilidad; si se requiere baja, debe modelarse como estado o archivado auditado.

### 4.3 Historiales

```text
incident_status_history
- id
- incident_id
- previous_status_value_id
- new_status_value_id
- reason
- changed_at
- changed_by

incident_assignment_history
- id
- incident_id
- previous_area_id
- new_area_id
- reason
- changed_at
- changed_by

incident_audit_event
- id
- incident_id
- event_type
- field_name
- previous_value
- new_value
- occurred_at
- actor_id
- metadata
```

Los historiales deben insertarse en la misma transacción que el cambio que describen. No se deben permitir actualizaciones desde el flujo normal de la aplicación.

## 5. Contratos Pydantic y API

### 5.1 Contratos

Crear modelos separados para entrada y salida. No reutilizar el modelo de persistencia como contrato público.

Contratos previstos:

- `OperationalIncidentCreate`.
- `OperationalIncidentUpdate`.
- `OperationalIncidentRead`.
- `OperationalIncidentListItem`.
- `OperationalIncidentListFilters`.
- `IncidentStatusTransitionRequest`.
- `IncidentAssignmentRequest`.
- `IncidentHistoryEntry`.
- `CatalogValueRead`.
- `OpenIncidentsBySeverityRead`.

Los campos públicos deben conservar la semántica contextual. Para contratos TypeScript, usar nombres en inglés y `camelCase` conforme a las convenciones del repositorio.

### 5.2 Endpoints conceptuales

La ruta y versionado definitivos deben seguir la convención de la API existente:

```text
GET    /operational-incidents/catalogs
POST   /operational-incidents
GET    /operational-incidents
GET    /operational-incidents/{incidentIdentifier}
PATCH  /operational-incidents/{incidentIdentifier}
POST   /operational-incidents/{incidentIdentifier}/status-transitions
POST   /operational-incidents/{incidentIdentifier}/assignments
GET    /operational-incidents/{incidentIdentifier}/status-history
GET    /operational-incidents/{incidentIdentifier}/assignment-history
GET    /operational-incidents/metrics/open-by-severity
```

Si la API ya dispone de un patrón para subrecursos, paginación, errores o métricas, ese patrón tendrá prioridad.

### 5.3 Reglas de respuesta

- `201` para alta correcta.
- `200` para consultas y cambios correctos, según la convención existente.
- `400` para payload estructuralmente inválido.
- `401` para ausencia de autenticación.
- `403` para operación no autorizada.
- `404` para incidencia o catálogo no encontrado, sin revelar información no autorizada.
- `409` para conflicto de versión, transición inválida por concurrencia o restricción de unicidad.
- `422` cuando la convención FastAPI/Pydantic existente lo utilice para validación semántica.

No se deben devolver descripciones completas en mensajes de error o logs de validación.

## 6. Flujo de creación

1. Recibir el payload autenticado.
2. Validar estructura y límites con Pydantic.
3. Resolver valores de catálogo por identificador estable.
4. Verificar que los valores sean utilizables para nuevas incidencias.
5. Verificar permisos del actor.
6. Verificar referencias a `Clinic`, `Reporter`, `AffectedSystem`, `Jurisdiction` y área responsable.
7. Ejecutar la creación dentro de una transacción.
8. Insertar el evento de alta en `incident_audit_event`.
9. Confirmar la transacción.
10. Devolver la representación configurada de la incidencia, incluyendo etiquetas actuales sin sustituir los identificadores.

## 7. Flujo de edición

1. Cargar la incidencia con control de autorización.
2. Validar únicamente campos editables.
3. Detectar diferencias respecto al valor persistido.
4. Revalidar catálogos y referencias.
5. Aplicar los cambios en una transacción.
6. Insertar un evento de auditoría por cambio relevante.
7. Actualizar autor y marca temporal de modificación.
8. Confirmar y devolver la representación actualizada.

Los cambios de estado y responsable deben dirigirse a sus operaciones específicas para asegurar sus historiales.

## 8. Flujo de estado

El servicio de dominio debe:

1. Cargar el estado actual.
2. Cargar la regla de transición aplicable.
3. Verificar que el actor puede ejecutar la transición.
4. Verificar que el nuevo estado está activo.
5. Bloquear o controlar concurrencia sobre la incidencia.
6. Actualizar el estado.
7. Insertar `incident_status_history`.
8. Insertar `incident_audit_event`.
9. Confirmar todo en una misma transacción.

La UI puede ocultar transiciones no permitidas, pero el backend siempre debe volver a validarlas.

## 9. Flujo de asignación

1. Cargar la incidencia y el área actual.
2. Verificar que el área nueva pertenece al catálogo contextual.
3. Verificar permisos del actor.
4. Verificar que el cambio no es una asignación inválida por política.
5. Actualizar el área responsable.
6. Insertar `incident_assignment_history`.
7. Insertar auditoría.
8. Confirmar la transacción.

## 10. Catálogos y cambios futuros

### Lectura

La UI debe consultar los catálogos mediante la API. La respuesta debe contener al menos:

```json
{
  "catalogName": "severity",
  "version": 1,
  "values": [
    {
      "key": "high",
      "label": "Alta",
      "description": "...",
      "isActive": true,
      "sortOrder": 2
    }
  ]
}
```

### Cambio de etiqueta

Para modificar sólo el nombre visible:

1. Actualizar o versionar `label` y `description`.
2. Mantener `key`.
3. Auditar el cambio.
4. Verificar que filtros, informes y UI muestran la etiqueta vigente.
5. Comprobar que incidencias históricas siguen resolviendo correctamente.

### Cambio semántico

Para dividir, fusionar o redefinir un valor:

1. Crear una propuesta de migración.
2. Definir mapeo de valores antiguos a nuevos.
3. Revisar impacto en incidencias, filtros, métricas y exportaciones.
4. Crear migración versionada.
5. Ejecutar pruebas sobre una copia representativa.
6. Ejecutar la migración en el entorno objetivo.
7. Registrar el resultado y actualizar `OperationalIncident-status.md`.

## 11. Consultas y métricas

### Listado

El listado debe:

- Filtrar en base de datos por estado, severidad y área responsable.
- Aceptar combinación de filtros.
- Utilizar paginación estable.
- Ordenar por actualización y, como desempate, identificador.
- Respetar autorización antes de devolver resultados.

### Abiertas por severidad

La consulta debe unirse al valor actual de `incidentStatus` y filtrar por `isOpen = true`, agrupando por el identificador estable de severidad.

La respuesta debe incluir:

- `severity.key`.
- `severity.label` vigente.
- Conteo.
- Marca temporal del cálculo.

No se deben agrupar por `label`, ya que una modificación de etiqueta no debe dividir una métrica.

## 12. Backoffice

La UI debe implementar:

1. Cola con paginación.
2. Filtros alimentados por catálogos.
3. Formulario de alta.
4. Formulario de edición.
5. Ficha con información actual.
6. Historial de estados.
7. Historial de responsables.
8. Métrica agrupada por severidad.
9. Acciones condicionadas por permisos.

La UI no debe:

- Codificar etiquetas de severidad o estado.
- Decidir si un estado es abierto.
- Ejecutar transiciones sin confirmación del backend.
- Mostrar campos que el actor no esté autorizado a ver.
- Enviar autor o marcas temporales como datos confiables.

## 13. Seguridad, privacidad y auditoría

- Usar el mecanismo de autenticación existente cuando esté disponible.
- Aplicar autorización en backend, no sólo en UI.
- Registrar actor, acción y momento de los cambios.
- Minimizar metadatos de auditoría.
- Evitar PHI en títulos, descripciones, errores y logs.
- No incluir payloads completos en telemetría.
- Asociar posibles incidentes de datos a `ComplianceReview`.
- Revisar acceso entre US y UK con Cumplimiento.
- Cifrar conexiones y secretos según la infraestructura aprobada.
- Definir retención y eliminación lógica antes del piloto.

## 14. Estrategia de pruebas

### Unitarias

- Validación Pydantic.
- Resolución de catálogos.
- Reglas de transición.
- Reglas de permisos.
- Cálculo de estado abierto.
- Mapeo de etiquetas.

### Integración

- Migraciones desde una base limpia.
- Creación y edición contra PostgreSQL.
- Historial en la misma transacción.
- Conflictos de unicidad y concurrencia.
- Filtros y paginación.
- Métrica por severidad.
- Valores inactivos e históricos.

### End-to-end

- Alta desde backoffice.
- Edición autorizada.
- Cambio de estado.
- Reasignación.
- Consulta de historiales.
- Actualización de etiqueta sin modificar `key`.
- Restricción de acciones por rol.

### Seguridad y privacidad

- Acceso no autenticado.
- Acceso autenticado sin permiso.
- Exposición entre áreas o jurisdicciones.
- PHI en payloads, errores y logs.
- Acceso a auditoría.
- Restauración de backup en entorno no productivo.

## 15. Secuencia de entrega

### Iteración 1 — Fundación

- Crear migraciones PostgreSQL.
- Crear catálogos y seeds.
- Crear modelos Pydantic base.
- Verificar cambio de etiqueta manteniendo `key`.

### Iteración 2 — Flujo principal

- Crear API de alta, listado, detalle y edición.
- Implementar persistencia transaccional.
- Implementar auditoría básica.

### Iteración 3 — Seguimiento

- Implementar transiciones.
- Implementar asignación.
- Implementar historiales.
- Implementar permisos específicos.

### Iteración 4 — Operación

- Implementar filtros.
- Implementar agrupación por severidad.
- Implementar backoffice completo.

### Iteración 5 — Preparación de piloto

- Completar pruebas.
- Revisar seguridad y cumplimiento.
- Validar migraciones y restauración.
- Preparar documentación operativa.
- Registrar el avance en `OperationalIncident-status.md`.

## 16. Definition of done técnica

La implementación estará lista para piloto cuando:

- Las migraciones reproducen el esquema desde cero.
- PostgreSQL mantiene las restricciones previstas.
- Pydantic valida los contratos públicos.
- La API cubre alta, edición, listado, consulta, estado, asignación, historiales y métrica.
- Los catálogos se consumen dinámicamente.
- Los cambios de etiquetas no rompen históricos.
- Los cambios semánticos tienen migración documentada.
- La UI no contiene valores de catálogo rígidos.
- Los cambios de estado y responsable son auditables.
- Los filtros y la métrica por severidad están probados.
- Se han verificado permisos, minimización y ausencia de PHI en logs.
- El estado de entrega está actualizado en el documento de status.
