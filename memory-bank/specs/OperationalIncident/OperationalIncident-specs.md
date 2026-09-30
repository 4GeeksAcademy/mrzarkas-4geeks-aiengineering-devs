# OperationalIncident — Specs, Tasks e Implementation

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Entidad principal:** `OperationalIncident`  
**Estado:** Preparado para implementación incremental  
**Fecha:** 2026-09-26  
**Fuente de negocio:** `CONTEXT.md` y `memory-bank/product-context.md`

> Este documento contiene la especificación funcional y es la fuente de requisitos del proyecto. Las tareas y la estrategia de implementación se mantienen separadas en [`OperationalIncident-tasks.md`](./OperationalIncident-tasks.md) y [`OperationalIncident-implementation.md`](./OperationalIncident-implementation.md). El avance verificable se registra en [`OperationalIncident-status.md`](./OperationalIncident-status.md).

---

## 1. Objetivo y alcance

HealthCore necesita un gestor para registrar y seguir **incidencias operativas**: interrupciones, degradaciones o comportamientos anómalos que afecten —o puedan afectar— a la operación de una clínica, a los sistemas que la soportan, a la facturación, a la gestión de citas, al cumplimiento o al acceso autorizado a datos.

El sistema permitirá:

- Registrar, editar, listar y consultar incidencias.
- Registrar obligatoriamente el canal de entrada, el tipo y el nivel de severidad.
- Asignar cada incidencia a un área responsable.
- Registrar y consultar cambios de estado y de responsable, con autor y marca temporal.
- Filtrar el listado por estado, severidad y área responsable.
- Mostrar el volumen de incidencias abiertas agrupadas por severidad.
- Mantener trazabilidad y minimizar los datos tratados conforme a HIPAA y UK GDPR.

### Fuera de alcance inicial

- Historia clínica, diagnósticos, notas clínicas o gestión de pacientes.
- Sustitución de los EHR, sistemas de facturación o sistemas de citas.
- Decisiones clínicas automatizadas.
- Microservicio independiente para incidencias.
- Valores de catálogo codificados de forma rígida en la UI o en la API.

---

## 2. Decisiones técnicas

### 2.1 Ubicación y arquitectura

- El backend será un módulo de la API centralizada **FastAPI**.
- El backoffice vivirá en `uis/`.
- No se introducirá un microservicio nuevo.
- Los contratos TypeScript que sean consumidos por backend y UI se añadirán a `packages/shared/`, utilizando el paquete existente `@repo/shared-types` cuando corresponda.
- Se mantendrán las herramientas del monorepo: `uv` para Python y `pnpm` para JavaScript/TypeScript.

### 2.2 Persistencia

Se utilizará una base de datos gestionada basada en **PostgreSQL**.

La validación de entrada y salida se realizará mediante modelos **Pydantic** en la API. Pydantic no sustituye las restricciones de PostgreSQL: ambas capas deben validar lo que les corresponde.

#### Responsabilidades por capa

| Capa | Responsabilidad |
|---|---|
| Pydantic | Tipos, campos requeridos, formatos, límites de texto, valores configurados y errores de API |
| Dominio/API | Transiciones de estado, permisos, asignaciones y reglas de negocio |
| PostgreSQL | Integridad referencial, unicidad, nulabilidad, índices y consistencia transaccional |
| Migraciones | Evolución versionada del esquema, catálogos y datos existentes |

La elección de PostgreSQL se considera la decisión inicial de persistencia. Si posteriormente se valida una alternativa distinta, se realizará una migración controlada; no se diseñará el módulo para depender de una base de datos embebida o de almacenamiento temporal.

### 2.3 Migraciones

Toda modificación de:

- Tablas.
- Columnas.
- Índices.
- Restricciones.
- Catálogos persistidos.
- Relaciones de auditoría.

debe implementarse mediante una migración versionada y reversible cuando sea viable.

Los nombres visibles de los catálogos no deben almacenarse directamente como clave de relación. Se almacenará un identificador estable y se resolverá la etiqueta vigente mediante configuración. Esto permite adaptar nombres sin migrar todas las incidencias históricas.

---

## 3. Modelo de dominio contextual

Los identificadores de entidad y los valores ya definidos por el contexto deben conservarse.

### Entidades y conceptos

- `OperationalIncident`: incidencia operativa.
- `Clinic`: clínica afectada.
- `Reporter`: persona que reporta.
- `AffectedSystem`: sistema afectado.
- `Jurisdiction`: jurisdicción.
- `IncidentStatus`: estado de la incidencia.
- `ComplianceReview`: revisión de Cumplimiento asociada, cuando aplique.

### Jurisdicciones

Los valores definidos son:

```text
US
UK
```

La representación de una incidencia que afecte a ambas jurisdicciones deberá resolverse antes de habilitar ese caso. No se inventará un tercer valor sin una decisión de dominio.

### Áreas responsables

El catálogo contextual de áreas es:

```text
Operaciones Clínicas
Experiencia del Paciente y Acceso
Ciclo de Ingresos y Facturación
Cumplimiento y Gobierno del Dato
Tecnología
```

Estos nombres deben conservarse como etiquetas canónicas inicialmente. Se podrán añadir alias o traducciones de presentación sin modificar el identificador estable del área.

### Sistemas afectados

El catálogo contextual de `AffectedSystem` incluye:

- EHR de EE. UU.
- EHR de Reino Unido.
- Facturación de EE. UU.
- Hoja de cálculo de facturación de Reino Unido.
- Programación telefónica de EE. UU.
- Agenda manual de Reino Unido.

Los valores de producción deben tener identificadores estables y etiquetas configurables, manteniendo estas etiquetas canónicas mientras no exista una decisión aprobada que las modifique.

---

## 4. Sistema de configuración de catálogos

### 4.1 Objetivo

No se bloqueará el desarrollo a la espera de aprobar los nombres visibles de canal, tipo, severidad y estado. Se implementará un sistema de configuración que permita comenzar con valores provisionales y adaptar posteriormente sus etiquetas sin cambiar el contrato de la entidad ni reescribir las incidencias.

La configuración será administrable y versionada, no una colección de literales dispersos en el código.

### 4.2 Principio de identificador estable

Cada valor tendrá:

- `catalogName`: catálogo al que pertenece.
- `key`: identificador técnico estable, en inglés y `camelCase` cuando se exponga en contratos TypeScript.
- `label`: nombre visible configurable.
- `description`: explicación operativa configurable.
- `isActive`: indica si puede utilizarse en nuevas incidencias.
- `sortOrder`: orden de presentación.
- `version`: versión de la configuración.
- `effectiveFrom`: fecha desde la que aplica.
- `effectiveTo`: fecha de fin opcional.

Los valores históricos no se eliminarán físicamente si ya han sido utilizados. Se desactivarán para nuevas incidencias, pero seguirán siendo consultables en las existentes.

### 4.3 Catálogos configurables

Los catálogos que pueden comenzar con etiquetas provisionales son:

```text
entryChannel
incidentType
severity
incidentStatus
```

El sistema debe permitir cambiar el `label` y la `description` manteniendo el mismo `key`. Por ejemplo, el valor técnico `high` podría cambiar de etiqueta visible sin modificar las filas de `OperationalIncident` que lo utilizan.

> Los `key` siguientes son una propuesta de arranque técnico y no sustituyen la validación funcional de los valores finales.

#### `entryChannel` — propuesta inicial

```text
clinicPhone
email
backofficeForm
technicalMonitoring
internalEscalation
other
```

#### `incidentType` — propuesta inicial

```text
systemAvailability
performanceDegradation
functionalError
integration
accessOrAuthentication
dataOrSynchronization
complianceOrAudit
billingOrClaim
appointmentOrScheduling
```

#### `severity` — propuesta inicial

```text
critical
high
medium
low
```

#### `incidentStatus` — propuesta inicial

```text
new
underAnalysis
assigned
inResolution
resolved
closed
onHold
reopened
cancelled
```

Las etiquetas iniciales de presentación se podrán escribir en español y alinearse con el vocabulario de HealthCore. La interfaz no debe asumir que el `key` equivale al texto mostrado.

### 4.4 Catálogos contextuales

`Jurisdiction`, `Clinic`, `AffectedSystem` y las áreas responsables no deben duplicarse dentro de los cuatro catálogos anteriores. Se tratarán como catálogos de dominio propios, con el mismo patrón de identificador estable y etiqueta configurable, conservando los valores definidos por el contexto.

### 4.5 Administración de configuración

La primera versión debe permitir cargar y versionar la configuración mediante:

1. Migraciones/seed iniciales en PostgreSQL.
2. Un mecanismo interno de administración o configuración autorizado.
3. Auditoría de cada cambio.

No se permitirá que la UI cliente envíe una etiqueta arbitraria y la persista como si fuera un catálogo. La API devolverá los valores activos y validará contra sus identificadores.

### 4.6 Cambios futuros de nombres

Para cambiar un nombre:

1. Se conserva el `key`.
2. Se crea una nueva versión o se actualiza la versión vigente según la política aprobada.
3. Se cambia `label`, `description` o `sortOrder`.
4. Se registra el autor y la marca temporal.
5. Se comprueba el impacto en informes, filtros y exportaciones.
6. Se mantienen las incidencias históricas consultables.

Sólo se requiere una migración de datos si cambia la semántica del valor o si se decide retirar el identificador, no para un cambio de etiqueta.

### 4.7 Cuándo sí hacer una migración de dominio

Será necesaria una migración cuando:

- Un valor se divide en varios significados.
- Dos valores se fusionan y debe conservarse el histórico.
- Cambia la semántica de severidad o estado.
- Se modifica la relación de una incidencia con un área o sistema.
- Se cambia el tipo o la estructura del identificador.

Estas migraciones deben incluir un mapeo explícito, revisión de informes y pruebas de compatibilidad.

---

## 5. Especificación funcional

### 5.1 Registro

Un usuario autorizado podrá crear una `OperationalIncident` con, como mínimo:

- Identificador de `OperationalIncident`.
- Título operativo.
- Descripción operativa.
- `Reporter`.
- `Clinic`.
- `Jurisdiction`.
- `AffectedSystem`.
- `entryChannel` configurado.
- `incidentType` configurado.
- `severity` configurado.
- `IncidentStatus` configurado.
- Área responsable.
- Fecha de creación generada por el servidor.

La obligatoriedad de área y estado debe quedar definida en la configuración de negocio. La primera versión recomendada exige ambos para evitar incidencias sin seguimiento.

### 5.2 Edición

Se podrán editar los campos autorizados. Cada cambio registrará:

- Autor.
- Marca temporal.
- Campo afectado.
- Valor anterior.
- Valor nuevo.
- Motivo cuando la política lo requiera.

Los cambios de estado y de responsable se registrarán además en sus historiales específicos.

### 5.3 Listado y consulta

El listado debe mostrar al menos:

- Identificador.
- Título.
- `Clinic`.
- `Jurisdiction`.
- `AffectedSystem`.
- Canal de entrada.
- Tipo.
- Severidad.
- `IncidentStatus`.
- Área responsable.
- Fecha de creación.
- Última actualización.

La ficha debe mostrar los datos actuales, `Reporter`, `ComplianceReview` cuando exista, historial de estado, historial de responsable y auditoría autorizada.

### 5.4 Asignación

Cada incidencia tendrá un área responsable del catálogo contextual. Un cambio de responsable registrará:

- Área anterior.
- Área nueva.
- Autor.
- Marca temporal.
- Motivo.

La asignación actual será visible tanto en el listado como en la ficha.

### 5.5 Estados

Las transiciones se definirán mediante configuración o una tabla de reglas, no mediante condicionales aislados en la UI. El backend será la autoridad para aceptar o rechazar una transición.

La propuesta inicial de flujo es:

```text
new → underAnalysis → assigned → inResolution → resolved → closed
```

`onHold`, `reopened` y `cancelled` sólo se habilitarán si las reglas de negocio los aprueban.

### 5.6 Filtros

El listado debe permitir combinar filtros por:

- `IncidentStatus`.
- `severity`.
- Área responsable.

Los valores de filtro deben resolverse contra los catálogos activos e históricos permitidos. La respuesta será paginada y respetará autorización.

### 5.7 Vista de abiertas por severidad

Una incidencia será abierta si su estado no pertenece al conjunto configurable de estados finales. La vista mostrará:

- Total de incidencias abiertas.
- Conteo por `severity`.
- Marca temporal de cálculo.
- Filtros aplicados, si existen.

La fórmula será:

```text
openIncidentCount(severity) =
  count(OperationalIncident)
  where IncidentStatus.isOpen = true
  and OperationalIncident.severity.key = severity.key
```

La propiedad `isOpen` debe formar parte de la configuración del estado para evitar codificar que sólo determinados nombres implican apertura.

---

## 6. Modelo de persistencia propuesto

El modelo lógico mínimo para PostgreSQL incluye:

### `operational_incident`

- Identificador de `OperationalIncident`.
- Título.
- Descripción operativa.
- Referencia a `Reporter`.
- Referencia a `Clinic`.
- Referencia a `Jurisdiction`.
- Referencia a `AffectedSystem`.
- Referencia al valor de `entryChannel`.
- Referencia al valor de `incidentType`.
- Referencia al valor de `severity`.
- Referencia al valor de `incidentStatus` actual.
- Referencia al área responsable.
- Fechas de creación y actualización.

### `catalog`

- Identificador del catálogo.
- Nombre técnico.
- Versión.
- Estado.
- Autor y marcas temporales.

### `catalog_value`

- Identificador estable del valor.
- Referencia al catálogo.
- `key` técnico.
- `label` visible.
- Descripción.
- `isActive`.
- `isOpen`, cuando aplique a `incidentStatus`.
- Orden.
- Vigencia.
- Autor y marcas temporales.

### `incident_status_history`

- `OperationalIncident`.
- Estado anterior.
- Estado nuevo.
- Autor.
- Marca temporal.
- Motivo.

### `incident_assignment_history`

- `OperationalIncident`.
- Área anterior.
- Área nueva.
- Autor.
- Marca temporal.
- Motivo.

### `incident_audit_event`

- `OperationalIncident`.
- Tipo de evento.
- Campo afectado.
- Valor anterior, con tratamiento seguro.
- Valor nuevo, con tratamiento seguro.
- Autor.
- Marca temporal.
- Metadatos mínimos necesarios.

Los nombres físicos definitivos deben adaptarse a las convenciones del módulo FastAPI cuando se cree. Las relaciones deben usar claves estables y restricciones de integridad.

---

## 7. Validación Pydantic

Los modelos Pydantic deberán:

- Rechazar campos obligatorios ausentes.
- Validar tipos y formatos.
- Aplicar límites de longitud al título y descripción.
- Validar identificadores de catálogo contra los valores admitidos por el servicio.
- Rechazar valores inactivos para nuevos registros.
- Permitir consultar valores históricos en incidencias existentes.
- Validar que una transición solicitada sea estructuralmente correcta.
- Evitar recibir marcas temporales de auditoría desde el cliente.
- Evitar campos no declarados cuando la configuración del proyecto lo permita.
- No registrar en errores el contenido completo de la descripción.

La validación Pydantic debe complementarse con comprobaciones transaccionales en PostgreSQL para evitar condiciones de carrera.

---

## 8. Tareas

### Fase 0 — Configuración y decisiones

- [ ] Definir el formato de configuración de catálogos.
- [ ] Definir identificadores estables y etiquetas iniciales.
- [ ] Cargar los valores provisionales mediante migración/seed.
- [ ] Definir permisos para modificar catálogos.
- [ ] Definir reglas de transición.
- [ ] Definir qué estados tienen `isOpen = true`.
- [ ] Definir límites de texto y política de no-PHI.
- [ ] Validar con Tecnología y Cumplimiento la estrategia de cambios posteriores.

### Fase 1 — PostgreSQL y modelo

- [ ] Confirmar instancia gestionada PostgreSQL.
- [ ] Definir credenciales y secretos fuera del repositorio.
- [ ] Definir migraciones versionadas.
- [ ] Crear tablas de catálogo y valores.
- [ ] Crear tablas de `OperationalIncident`.
- [ ] Crear historiales de estado y asignación.
- [ ] Crear auditoría.
- [ ] Añadir índices para estado, severidad, área y fechas.
- [ ] Añadir restricciones de integridad.
- [ ] Definir estrategia de backup y retención.

### Fase 2 — API FastAPI

- [ ] Crear el módulo de `OperationalIncident`.
- [ ] Crear modelos Pydantic de entrada y salida.
- [ ] Crear lectura de configuración.
- [ ] Implementar alta.
- [ ] Implementar edición.
- [ ] Implementar listado paginado.
- [ ] Implementar consulta detallada.
- [ ] Implementar cambio de estado.
- [ ] Implementar asignación.
- [ ] Implementar consulta de historiales.
- [ ] Implementar resumen por severidad.
- [ ] Implementar autorización.
- [ ] Implementar auditoría.

### Fase 3 — Backoffice

- [ ] Crear cola de incidencias.
- [ ] Crear filtros configurables.
- [ ] Crear formulario de alta.
- [ ] Crear formulario de edición.
- [ ] Crear ficha de detalle.
- [ ] Mostrar historial de estados y responsables.
- [ ] Mostrar resumen de incidencias abiertas por severidad.
- [ ] No asumir etiquetas fijas en los componentes.
- [ ] Manejar estados de carga, vacío y error.

### Fase 4 — Pruebas y migrabilidad

- [ ] Probar creación con valores configurados.
- [ ] Probar rechazo de valores inactivos.
- [ ] Probar cambio de etiqueta conservando el `key`.
- [ ] Probar versionado de configuración.
- [ ] Probar migración de un valor dividido o fusionado.
- [ ] Probar transiciones válidas e inválidas.
- [ ] Probar auditoría de cambios.
- [ ] Probar filtros combinados.
- [ ] Probar agregación por severidad.
- [ ] Probar permisos y aislamiento de datos.
- [ ] Probar que logs y errores no contienen PHI.
- [ ] Probar restauración y migración en un entorno no productivo.

---

## 9. Estrategia de implementación incremental

### Iteración 1 — Fundación

Implementar PostgreSQL gestionado, migraciones, tablas de catálogo, seed provisional y modelos Pydantic. En esta fase debe ser posible cambiar una etiqueta sin modificar el código de la UI.

### Iteración 2 — Flujo principal

Implementar alta, listado, consulta y edición de `OperationalIncident`, incluyendo validación de catálogos y auditoría básica.

### Iteración 3 — Seguimiento

Implementar cambios de estado, asignación a área responsable, historiales y reglas de transición.

### Iteración 4 — Consulta operativa

Implementar filtros por estado, severidad y área, además de la vista de incidencias abiertas por severidad.

### Iteración 5 — Seguridad y piloto

Completar autorización, revisión de Cumplimiento, pruebas de no-PHI, métricas técnicas y piloto limitado.

---

## 10. Criterios de aceptación

### Catálogos

- Los nombres visibles se pueden modificar mediante configuración.
- Los identificadores técnicos permanecen estables al cambiar una etiqueta.
- Los valores inactivos no se pueden utilizar en nuevas incidencias.
- Los valores históricos siguen siendo consultables.
- Los cambios de configuración quedan auditados.

### Incidencias

- Un usuario autorizado puede registrar, editar, listar y consultar una `OperationalIncident`.
- Canal, tipo y severidad son obligatorios según la configuración vigente.
- `Clinic`, `Jurisdiction`, `AffectedSystem` y área responsable usan valores contextuales válidos.
- Se puede asignar una incidencia a cualquiera de las áreas definidas en el contexto.

### Historial

- Cada cambio de estado registra estado anterior, nuevo estado, autor y marca temporal.
- Cada cambio de responsable registra área anterior, nueva área, autor y marca temporal.
- La ficha permite consultar ambos historiales.
- Los eventos históricos no se sobrescriben.

### Filtros y métricas

- El listado filtra por estado, severidad y área responsable.
- Los filtros se pueden combinar.
- La vista agregada muestra abiertas por severidad.
- La definición de abierta depende de la configuración `isOpen`, no de literales en la UI.

### PostgreSQL y API

- El esquema se crea y modifica mediante migraciones.
- Los payloads se validan mediante Pydantic.
- PostgreSQL garantiza las restricciones de integridad definidas.
- Un cambio de proveedor o modelo futuro puede abordarse mediante migración.

### Cumplimiento

- No se registra historia clínica ni PHI innecesaria.
- Los logs no incluyen payloads completos.
- Los cambios y accesos relevantes se auditan según la política aprobada.
- Una incidencia con posible impacto de HIPAA o UK GDPR puede asociarse a `ComplianceReview`.

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Las etiquetas provisionales se convierten en contrato rígido | Separar `key` estable de `label` configurable |
| Se cambia la semántica sin migrar históricos | Versionar catálogos y exigir migración para cambios semánticos |
| La UI contiene valores hardcodeados | Obtener catálogos desde la API |
| Un valor inactivo rompe consultas históricas | Desactivar para altas, conservar para lectura histórica |
| Pydantic y PostgreSQL divergen | Compartir reglas documentadas y probar ambas capas |
| Cambios concurrentes en configuración | Versionado, control de concurrencia y transacciones |
| Exposición de PHI en una descripción o log | Minimización, validación, permisos y filtrado de logs |
| Complejidad prematura | Mantener API FastAPI centralizada |
| Cambio futuro de base de datos | Encapsular persistencia y usar migraciones controladas |

---

## 12. Próximos pasos

1. Crear la decisión técnica de PostgreSQL gestionado y registrar sus requisitos operativos.
2. Acordar el formato de `catalog` y `catalog_value`.
3. Cargar los valores provisionales de los cuatro catálogos.
4. Definir los permisos para administrar configuración.
5. Confirmar el esquema de migraciones que utilizará el futuro módulo FastAPI.
6. Diseñar el contrato Pydantic de `OperationalIncident`.
7. Implementar la primera iteración sin bloquearse por el nombre visible de los catálogos.
8. Revisar los nombres y descripciones con los validadores cuando estén disponibles, cambiando etiquetas o ejecutando una migración semántica según corresponda.

> Esta propuesta adelanta el trabajo sin convertir valores provisionales en una deuda estructural: los identificadores estables protegen los datos y la configuración permite ajustar el lenguaje del dominio posteriormente.
