# Propuestas de mejora

## Estado

Pendientes de validación.

## Propuesta: convención formal de calidad

**Descripción:**  
Definir y documentar una convención formal para formateo, linting, testing y CI/CD.

**Motivo:**  
Aunque el Dev Container incluye algunas herramientas, actualmente no existe una política común ni comprobaciones automatizadas visibles.

**Estado:**  
Pendiente de validación.

**Acción posterior:**  
Si se aprueba, documentarla e incorporarla a `conventions.md`.

## Propuesta: autenticación JWT propia como paso intermedio hacia SSO

**Descripción:**
Implementar en `central-api` un mecanismo de autenticación propio basado en
JWT firmado por la propia API (HS256, secreto en variable de entorno), con
claims de `sub` (actor), `role` y, cuando aplique, `area_id`. Un endpoint
`POST /auth/tokens` emite tokens de forma explícita para desarrollo y
pruebas, ya que todavía no existe un proveedor de identidad corporativo.

**Motivo:**
Las specs de `OperationalIncident` asumen una matriz de permisos que se
"mapea al mecanismo de autenticación que exista en el monorepo", pero ese
mecanismo no existe (ver `discrepancies.md`). Sin autenticación no es
posible aplicar la matriz de capacidades ni proteger `audit:read` ni las
transiciones de estado.

**Diseño para ser reemplazable:**
- La verificación de JWT vive en un módulo aislado
  (`app/auth/security.py` y `app/auth/dependencies.py`).
- Los endpoints de negocio dependen de una interfaz mínima (`Actor` con
  `id`, `role`, `area_id`) y de funciones `require_capability(...)`, no del
  formato concreto del token.
- Sustituir el emisor propio por SSO/OIDC del cliente implicará cambiar
  cómo se obtiene y valida el token (por ejemplo, verificar firma contra
  las claves públicas del IdP), sin tocar los routers de incidencias.

**Plan de migración futuro:**
1. Integrar el IdP del cliente (SSO, probablemente OIDC) cuando esté
   disponible.
2. Mantener el emisor propio sólo para entornos de desarrollo/test.
3. Retirar `POST /auth/tokens` de cualquier entorno expuesto públicamente.

**Estado:**
Implementado como solución vigente de desarrollo (2026-09-28). Se mantiene
indefinidamente mientras no exista una validación de Tecnología y
Cumplimiento que requiera su sustitución por el IdP real del cliente.

## Propuesta: refuerzo del sistema JWT y autorización

**Estado:**
Implementación parcial. El JWT propio se mantiene como mecanismo vigente;
la emisión libre queda limitada por configuración a `development` y `test`.
Permanecen pendientes la validación formal y las mejoras de políticas.

### Crítico — restringir la emisión de tokens

Actualmente `POST /auth/tokens` acepta `actor_id`, `role` y `area_id` en el
payload y emite un JWT válido. Cualquier consumidor que pueda alcanzar ese
endpoint puede reclamar un token con rol `admin` u otro rol de mayor
privilegio. La firma JWT protege contra la manipulación posterior del token,
pero no protege contra una emisión inicial sin comprobación de identidad.

Antes de exponer el servicio fuera del desarrollo local se debe aplicar una
de estas alternativas aprobadas:

1. Limitar el endpoint a desarrollo y pruebas mediante configuración de
   entorno; no registrarlo en entornos compartidos.
2. Proteger la emisión con una credencial de bootstrap gestionada como
   secreto y restringida a operadores autorizados.
3. Persistir usuarios, credenciales y asignaciones de rol, y emitir tokens
   sólo después de autenticar al usuario.

**Implementado (2026-09-28):** `POST /auth/tokens` devuelve `404` cuando
`APP_ENVIRONMENT` es `staging` o `production`. Todo despliegue compartido
debe fijar explícitamente uno de esos valores; de lo contrario, el valor por
defecto de desarrollo habilita la emisión para uso local.

### Alta prioridad — centralizar autorización contextual

Mantener `require_capability(...)` como dependencia FastAPI para exigir la
capacidad general del endpoint. Añadir un módulo de políticas, por ejemplo
`app/auth/policies.py`, que concentre la autorización sobre recursos:

- `can_read_incident(actor, incident)`.
- `can_update_incident(actor, incident)`.
- `can_assign_incident(actor, incident, target_area_id)`.
- Filtros de visibilidad de incidencias según actor, área y jurisdicción.

Esto evita que cada router tenga que recordar `ensure_area_scope(...)` y
permite reutilizar exactamente las mismas reglas en detalle, listado,
historiales y métricas.

**Implementado parcialmente (2026-09-28):** `app/auth/policies.py`
centraliza el alcance por área, el filtro de listados y la autorización de
transiciones. Falta extender las políticas cuando existan jurisdicciones,
maestros y `ComplianceReview` reales.

### Alta prioridad — alinear la matriz de roles

Validar y convertir en fuente de verdad única la matriz de roles y
capacidades. Hoy existen diferencias entre las decisiones iniciales y el
código: Tecnología no puede asignar ni administrar catálogos. El rol técnico
`admin` se mantiene por decisión de proyecto, con revisión de acceso previa a
producción.

**Implementado parcialmente (2026-09-28):** el listado de incidencias se
limita a datos resumidos y Dirección no puede consultar el detalle. Se
mantiene pendiente validar las capacidades de Tecnología y Cumplimiento.

### Prioridad media — pruebas y alcance de catálogo

- Añadir pruebas HTTP para token ausente o inválido, capacidades denegadas,
  acceso a área propia y ajena, acceso de Dirección y consulta de auditoría.
- Decidir explícitamente si `GET /catalogs/{catalog_name}` debe requerir
  autenticación.
- Mantener middleware sólo para autenticación transversal (extraer y validar
  JWT); las decisiones de capacidad y recurso deben permanecer en
  dependencias y políticas de dominio.

**Implementado parcialmente (2026-09-28):** se cubren por HTTP token ausente,
token inválido, emisor deshabilitado en producción, capability denegada,
aislamiento de área y auditoría. Falta definir y cubrir el alcance de
Dirección. Las pruebas usan `httpx.AsyncClient` con `ASGITransport`, sin
depender de `TestClient`.

## Propuesta M0: matriz funcional de roles y capacidades

**Estado:** Criterio funcional acordado para el proyecto; pendiente de
validación formal por Tecnología y Cumplimiento. No autoriza datos reales,
escritura en backoffice ni producción.

**Objetivo:** consolidar una única fuente de verdad para permisos de
OperationalIncident y Management, aplicando mínimo privilegio y conservando
`admin` como rol técnico con acceso total y auditado.

### Estructura de roles

Hay cuatro áreas principales y un grupo de áreas operativas:

| Grupo | Rol JWT | Alcance |
|---|---|---|
| Administración técnica | `admin` | Acceso total; soporte y operación excepcional, siempre auditados. |
| Tecnología | `technology` | Operación técnica de incidencias y, tras aprobación específica, sistemas/coberturas. |
| Cumplimiento | `compliance` | Revisiones de Cumplimiento, auditoría y controles de conformidad. |
| Dirección | `direction` | Sólo indicadores y listados resumidos, sin detalle sensible ni mutaciones. |
| Áreas operativas | `responsibleArea` + `area_id` | Una misma capacidad base, restringida a la área responsable asignada. |

Las áreas operativas (por ejemplo, Operaciones Clínicas, Acceso de Pacientes o
Revenue Cycle) **no son roles JWT distintos**. Son registros maestros y se
aplican mediante `area_id`; así se evita multiplicar roles por departamento.

### Matriz propuesta

| Capacidad o acción | Admin | Tecnología | Cumplimiento | Dirección | Área responsable |
|---|---:|---:|---:|---:|---:|
| Listar incidencias | Sí | Sí | Sí | Sólo resumen | Sólo su área |
| Ver detalle, historial y estado | Sí | Sí | Sí | No | Sólo su área |
| Crear incidencia | Sí | Sí | No | No | Sí, sólo dentro del alcance de su `area_id` |
| Editar incidencia (`incident:update`) | Sí | Sí | No | No | No; la edición propia usa la capacidad separada siguiente |
| Actualizar campos operativos propios (`incident:updateOwnArea`) | Sí, incluido en acceso total | No | No | No | Sí, sólo su área; título y descripción |
| Transicionar o reasignar | Sí | Sí | No | No | Sólo cierre/cancelación de su área |
| Métricas | Sí | Sí | Sí | Sí, agregadas | Sólo su área |
| Leer catálogos y maestros | Sí | Sí | Sí | No | Sí, para formularios |
| Gestionar catálogos | Sí | No | No | No | No |
| Gestionar clínicas, jurisdicciones y áreas | Sí | No | No | No | No |
| Gestionar sistemas y coberturas | Sí | Pendiente de aprobación específica | No | No | No |
| Leer `ComplianceReview` | Sí | No, salvo excepción aprobada | Sí | No | No |
| Crear o cambiar `ComplianceReview` | Sí | No | Sí | No | No |
| Asociar `ComplianceReview` a una incidencia | Sí | No | Sí, con capacidad específica | No | No |
| Consultar auditoría | Sí | No | Sí | No | No |

`admin` recibe todas las capacidades, incluidas las futuras; no se usa como
sustituto de los roles ordinarios. Toda mutación de `admin` debe conservar el
actor y la correlación en la auditoría.

### Criterio acordado para la revisión de capacidades

Se mantienen para los roles y acciones restantes las capacidades descritas
en esta matriz. `responsibleArea` no recibe `incident:update`, que permanece
reservada a Tecnología y `admin`. En su lugar recibe la capacidad separada
`incident:updateOwnArea`, limitada a incidencias cuyo `responsible_area_id`
coincida con el `area_id` del actor. El alcance se determina por el área
asignada, no por quién reportó o creó personalmente la incidencia.

Con `incident:updateOwnArea` sólo se permite editar título y descripción,
sujetos a validación y auditoría. No se permite modificar severidad,
`responsible_area_id` ni `compliance_review_id`; la reasignación permanece en
su flujo separado y no se concede. Los cambios de estado no forman parte de
esta capacidad y siguen limitados a las transiciones autorizadas actualmente
para el área (cierre/cancelación); cualquier ampliación requiere una decisión
expresa.

No se prevé una revisión proactiva de las demás capacidades. Se reconsiderarán
sólo si las partes interesadas solicitan una revisión. La validación formal
pendiente con Tecnología y Cumplimiento sigue siendo necesaria antes de
habilitar escritura en backoffice, promover datos reales o autorizar producción.

### Observaciones pendientes para retomar

- El modelo `IncidentUpdate` no rechaza explícitamente campos PATCH
   desconocidos; Pydantic puede ignorarlos silenciosamente y la API podría
   responder sin aplicar ningún cambio. Revisar el contrato para que entradas
   no reconocidas se rechacen explícitamente.
- La especificación exige un motivo para cancelar, pero la API actualmente
   acepta la transición a `cancelled` sin motivo. Alinear validación y pruebas
   con la regla documentada.

La capacidad `incident:updateOwnArea` y sus límites quedan confirmados como
criterio funcional del proyecto. Estos dos detalles se retomarán más adelante;
M0 sigue pendiente de validación formal por Tecnología y Cumplimiento.

### Capacidades a introducir tras la aprobación

El código actual utiliza permisos amplios para Management. Antes de delegar
escritura, se propone separar:

- `referenceData:manageSystems`
- `referenceData:manageClinics`
- `referenceData:manageJurisdictions`
- `referenceData:manageAreas`
- `incident:associateComplianceReview`

La última permite a Cumplimiento asociar o retirar una revisión compatible sin
recibir `incident:update`, que da acceso a cambios operativos más amplios.

### Condiciones de ejecución

1. Tecnología y Cumplimiento aprueban la matriz, sus propietarios y las
   excepciones temporales.
2. Se actualizan `app/auth/roles.py`, políticas y pruebas de matriz por rol.
3. Sólo se añade alcance por jurisdicción al JWT si existe una fuente de
   verdad aprobada para esas asignaciones; mientras tanto, Cumplimiento tiene
   alcance global y la compatibilidad se valida al asociar una revisión.
4. El JWT propio vigente no se sustituye por esta propuesta; su sustitución
   sigue la propuesta de autenticación existente y requiere validación aparte.
5. Se actualizan las especificaciones y el backoffice antes de habilitar
   escritura fuera de desarrollo.
