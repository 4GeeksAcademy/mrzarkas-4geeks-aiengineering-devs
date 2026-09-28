# OperationalIncident — Maestros externos y referencias contextuales

**Estado:** Decisión de arquitectura inicial; valores reales y aprobación funcional pendientes
**Fecha:** 2026-09-28
**Referencias:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md), [`OperationalIncident-phase1-data-model.md`](./OperationalIncident-phase1-data-model.md)

## 1. Decisión

`OperationalIncident` no será propietario de los datos maestros. La API
central incorporará un dominio compartido de datos de referencia, separado
del módulo `incidents`, que será la fuente de validación para:

| Maestro | Propietario funcional | Uso en incidencias |
|---|---|---|
| `Jurisdiction` | Cumplimiento y Gobierno del Dato | Determina `US` o `UK` y reglas de acceso/retención aplicables |
| `Clinic` | Operaciones Clínicas | Clínica afectada; pertenece a una jurisdicción |
| `AffectedSystem` | Tecnología | Sistema afectado y jurisdicciones donde opera |
| `ResponsibleArea` | Tecnología con responsables de área | Área actual responsable de la resolución |
| `Reporter` | Identidad y acceso | Actor autenticado que registra la incidencia |
| `ComplianceReview` | Cumplimiento y Gobierno del Dato | Revisión restringida asociada cuando corresponda |

Los cuatro primeros se almacenarán como datos de referencia compartidos en
la API central, no como catálogos internos de `OperationalIncident`. Cuando
sus tablas residan en la misma base de datos, las incidencias usarán claves
foráneas. La API seguirá devolviendo UUID estables y etiquetas configurables.

## 2. Contratos mínimos

Todos los maestros contextuales deben exponer: `id` UUID estable, `key`
técnica única, `label`, `isActive`, vigencia, auditoría y fecha de
actualización. Los valores inactivos no se usarán en incidencias nuevas y no
se eliminarán si tienen historial.

Relaciones obligatorias:

- Cada `Clinic` tiene una `Jurisdiction`.
- Cada `AffectedSystem` declara las jurisdicciones en las que puede operar.
- La `clinic_id` de una incidencia debe ser compatible con su
  `jurisdiction_id`.
- El `affected_system_id` debe estar habilitado en la jurisdicción de la
  incidencia.
- El `responsible_area_id` debe estar activo al crear o reasignar.

## 3. Reporter e identidad

`Reporter` no se duplicará como tabla local de empleados. En el flujo normal,
`reporter_id` será el `Actor.id` extraído del JWT; el cliente no podrá
suplantar a otro reportante enviando un UUID arbitrario. Un registro en nombre
de otra persona requerirá una capacidad explícita futura y auditoría del
actor y del reportante declarado.

## 4. ComplianceReview

`ComplianceReview` será un módulo propietario de Cumplimiento, separado de
incidencias. Su referencia será opcional y validada antes de asociarse. La
API de incidencias sólo podrá exponer su identificador o un resumen autorizado;
no copiará detalles de una revisión ni datos sensibles dentro de la incidencia.

## 5. Datos iniciales y límites

No se cargarán en producción clínicas, personas o sistemas ficticios. Antes
de la implementación se debe recibir y aprobar:

1. El registro de las 12 clínicas, con `key`, jurisdicción y estado activo.
2. El inventario de sistemas afectados y su cobertura por jurisdicción.
3. Las cinco áreas responsables y sus responsables funcionales.
4. La fuente de identidad que asigna UUID a los reportantes.
5. El procedimiento de alta y ciclo de vida de `ComplianceReview`.

Mientras esos datos no estén disponibles, sólo se permiten fixtures sintéticos
en desarrollo y pruebas; no se validarán UUID arbitrarios en staging o
producción.

## 6. Orden de implementación

1. Crear el módulo compartido de datos de referencia y migraciones.
2. Cargar fixtures sintéticos de desarrollo y contratos de lectura.
3. Añadir claves foráneas y validación de compatibilidad en incidencias.
4. Derivar `reporter_id` de la identidad autenticada.
5. Implementar el módulo y la asociación validada de `ComplianceReview`.
6. Sustituir fixtures por datos aprobados antes de piloto.
