# Estado actual — OperationalIncident

**Actualizado:** 28 de septiembre de 2026
**Estado:** prototipo técnico pre-MVP; no autorizado para piloto ni producción.

**Datos de desarrollo:** todo el entorno de desarrollo, pruebas y ejemplos usa exclusivamente datos sintéticos. No se cargarán clínicas, empleados, revisiones de Cumplimiento ni datos de pacientes reales durante el desarrollo.

## Estado verificable

- El contexto de HealthCore, sus 12 clínicas, la operación EE. UU./Reino Unido y las restricciones HIPAA/UK GDPR están documentados.
- Existe una API FastAPI centralizada con catálogos configurables, incidencias, listado resumido, detalle, edición, transiciones de estado, historial de estado, auditoría y JWT propio. Dirección sólo accede a resúmenes y métricas; la emisión libre de tokens queda limitada a desarrollo y pruebas mediante `APP_ENVIRONMENT`; las reglas contextuales de autorización se centralizan en `app/auth/policies.py`.
- Existen migraciones Alembic para catálogos, `OperationalIncident`, historial de estado y auditoría, además de seed idempotente para los cuatro catálogos provisionales.
- El proyecto cuenta con un entorno local montado en Podman con PostgreSQL. Tras limpiar datos, Alembic y el seed fueron validados. Una base temporal vacía aplicó las migraciones `0001` a `0005`, ejecutó el seed y superó 18 pruebas. Un dump de la base local también se restauró en un entorno temporal, donde quedó en `0005`, aplicó migraciones idempotentes y superó 18 pruebas. Los entornos y dumps temporales se eliminaron al finalizar.
- Hay pruebas de catálogos, autenticación/autorización HTTP, workflows y fixtures de Cumplimiento: el servicio `test` de Podman las ejecuta de forma reproducible contra PostgreSQL local, con 19 pruebas superadas y sin advertencias. La imagen de producción permanece libre de dependencias de pruebas.
- Management tiene completados M1–M6 de forma provisional: la migración `0009_management_audit` añade trazabilidad de creación y actualización a los maestros, un registro append-only de eventos e índices de consulta; las capacidades y políticas restringen mutaciones a `admin` salvo `ComplianceReview`, que también gestiona Cumplimiento. Catálogos y maestros sintéticos tienen listado paginado, alta, edición, activación/desactivación motivada, claves inmutables y auditoría transaccional. `ComplianceReview` permite cambio de estado autorizado y audita creación, estado y asociación. OpenAPI, tipos compartidos, consulta autorizada de auditoría, backoffice de lectura y guía de operación están disponibles. Los cambios de clínica o cobertura que invalidarían incidencias históricas se rechazan. Una instalación vacía y una restauración de dump sintético superaron migración idempotente, seeds y 27 pruebas; la suite local actual suma 27 pruebas superadas.

## Pendiente para MVP

- Las incidencias validan clínica, jurisdicción, sistema y área contra maestros sintéticos estables US/UK; `reporter_id` deriva de la identidad autenticada y existen claves foráneas para las referencias contextuales. Antes de piloto deben sustituirse fixtures por datos aprobados.
- Administración de catálogos y maestros según `specs/OperationalIncident-management.md` está técnicamente implementada. M0 sigue pendiente de aprobación externa: no se autoriza la promoción de datos reales, UI de escritura ni producción. El alcance de `ComplianceReview` por jurisdicción se valida al asociarlo a una incidencia; el JWT aún no representa alcance jurisdiccional individual.
- Backoffice en `uis/`.
- Validación formal de Tecnología, Cumplimiento y áreas funcionales sobre catálogos, permisos, transiciones, no-PHI, retención y SLA.
- Validación por Tecnología y Cumplimiento del JWT vigente o de una alternativa futura; no hay una sustitución comprometida. También faltan la decisión de PostgreSQL gestionado, backups y prueba de restauración.

## Próximo paso

Resolver M0 con Tecnología y Cumplimiento: matriz final de capacidades, política no-PHI, retención de auditoría y proceso de promoción de maestros aprobados. Después, validar el backoffice de escritura antes de piloto.
