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
