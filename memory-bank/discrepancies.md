# Discrepancias entre documentación y estado real del repositorio

## Estado

Vivo. Añadir una entrada cada vez que se detecte que la documentación (specs,
CONTEXT.md, memory-bank) describe algo como decidido o disponible que en
realidad no está implementado en el código.

## Autenticación y autorización (detectado 2026-09-28)

`memory-bank/specs/OperationalIncident-initial-decisions.md` y
`OperationalIncident-specs.md` dan por hecho que existe "el mecanismo de
autenticación que exista en el monorepo" y describen una matriz de permisos
(`incident:create`, `incident:transition`, `audit:read`, etc.) como si sólo
faltara mapearla a un sistema ya existente.

En la realidad, antes de 2026-09-28 no existía ningún mecanismo de
autenticación ni autorización en el monorepo: ni JWT, ni OAuth/OIDC, ni
sesiones, ni roles, ni usuarios. Todos los endpoints de `central-api` eran
de acceso libre y el "actor" se recibía como un UUID arbitrario en el propio
payload de la petición, sin ninguna verificación de identidad.

**Resolución:** se implementa un sistema de autenticación propio basado en
JWT (ver `proposals.md`) como solución temporal, diseñado para poder
sustituirse por el IdP corporativo cuando exista, sin rediseñar los
endpoints de negocio.

## Rol `admin`

Ninguno de los documentos de `memory-bank/specs/` ni `product-context.md`
define un rol `admin`. Los roles documentados son implícitos por área
(Tecnología, Operaciones Clínicas, Experiencia del Paciente y Acceso, Ciclo
de Ingresos y Facturación, Cumplimiento y Gobierno del Dato) más un rol
agregado de "Dirección". Se añade `admin` como rol técnico nuevo, no
aprobado funcionalmente, para administración de catálogos, permisos y
soporte. Debe revisarse con el equipo de producto antes de producción.

## Entidades contextuales sin implementar

`Clinic`, `Reporter`, `AffectedSystem`, `Jurisdiction` y `ComplianceReview`
están descritas en las specs como referencias a datos maestros externos,
pero no existe ninguna API central ni tabla maestra real en el monorepo.
Actualmente `central-api` acepta cualquier UUID sin validarlo contra un
maestro. Esto ya estaba documentado como decisión provisional de Fase 1,
pero se deja constancia aquí porque sigue sin resolverse.
