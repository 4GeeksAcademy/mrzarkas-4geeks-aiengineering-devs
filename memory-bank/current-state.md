# Estado actual — OperationalIncident

**Actualizado:** 28 de septiembre de 2026
**Estado:** prototipo técnico pre-MVP; no autorizado para piloto ni producción.

## Estado verificable

- El contexto de HealthCore, sus 12 clínicas, la operación EE. UU./Reino Unido y las restricciones HIPAA/UK GDPR están documentados.
- Existe una API FastAPI centralizada con catálogos configurables, incidencias, listado resumido, detalle, edición, transiciones de estado, historial de estado, auditoría y JWT propio. Dirección sólo accede a resúmenes y métricas; la emisión libre de tokens queda limitada a desarrollo y pruebas mediante `APP_ENVIRONMENT`; las reglas contextuales de autorización se centralizan en `app/auth/policies.py`.
- Existen migraciones Alembic para catálogos, `OperationalIncident`, historial de estado y auditoría, además de seed idempotente para los cuatro catálogos provisionales.
- El proyecto cuenta con un entorno local montado en Podman con PostgreSQL. Tras limpiar datos, Alembic y el seed fueron validados. Una base temporal vacía aplicó las migraciones `0001` a `0005`, ejecutó el seed y superó 18 pruebas. Un dump de la base local también se restauró en un entorno temporal, donde quedó en `0005`, aplicó migraciones idempotentes y superó 18 pruebas. Los entornos y dumps temporales se eliminaron al finalizar.
- Hay pruebas de catálogos, autenticación/autorización HTTP y workflows: el servicio `test` de Podman las ejecuta de forma reproducible contra PostgreSQL local, con 18 pruebas superadas y sin advertencias. La imagen de producción permanece libre de dependencias de pruebas.

## Pendiente para MVP

- Las incidencias validan clínica, jurisdicción, sistema y área contra maestros sintéticos estables US/UK; `reporter_id` deriva de la identidad autenticada y existen claves foráneas para las referencias contextuales. Antes de piloto deben sustituirse fixtures por datos aprobados.
- `ComplianceReview` y administración de catálogos.
- Backoffice en `uis/`.
- Validación formal de Tecnología, Cumplimiento y áreas funcionales sobre catálogos, permisos, transiciones, no-PHI, retención y SLA.
- Validación por Tecnología y Cumplimiento del JWT vigente o de una alternativa futura; no hay una sustitución comprometida. También faltan la decisión de PostgreSQL gestionado, backups y prueba de restauración.

## Próximo paso

Usar el entorno PostgreSQL local de Podman para ejecutar y registrar migraciones, seed y pruebas de integración desde una base limpia. Después, completar las brechas del API y fijar el contrato público antes de iniciar el backoffice.
