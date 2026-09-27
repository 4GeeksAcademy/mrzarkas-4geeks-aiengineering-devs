# OperationalIncident — migraciones y seeds de Fase 1

**Estado:** Implementado parcialmente; ejecución contra PostgreSQL pendiente
**Referencia:** [`OperationalIncident-phase1-data-model.md`](./OperationalIncident-phase1-data-model.md)

## 1. Estado actual del repositorio

La API central está en `services/central-api/`, con SQLAlchemy async y **Alembic integrado con SQLAlchemy**. La URL de PostgreSQL se recibe mediante `DATABASE_URL`; no se guardan credenciales en el repositorio.

Por ello, este documento define el orden y el comportamiento esperado, pero no crea una dependencia ni una estructura de migraciones prematura.

## 2. Secuencia propuesta

La secuencia implementada hasta ahora es:

1. `0001_initial_schema` — baseline vacío.
2. `0002_create_catalog_tables` — crea `catalog` y `catalog_value`.

El seed se ejecuta como comando de aplicación (`seed-catalogs`), no como migración de esquema. Las siguientes revisiones siguen pendientes:

3. Crear referencias contextuales.
4. Crear `operational_incident`.
5. Crear historiales y auditoría.
6. Añadir restricciones e índices específicos del dominio.

Las migraciones se implementarán con Alembic y SQLAlchemy. Cada migración debe tener una operación de reversión o un procedimiento explícito de recuperación aprobado.

## 3. Seed provisional

El seed implementado en `app/catalogs/seed.py` usa las claves técnicas de la decisión de catálogos, no las etiquetas. Contempla:

- `entryChannel`
- `incidentType`
- `severity`
- `incidentStatus`
- No contempla áreas responsables ni jurisdicciones: siguen siendo datos maestros sin propietario confirmado.

El seed debe ser idempotente mediante la clave `(catalog_name, key)` y debe:

- crear el catálogo si no existe;
- crear o actualizar una entrada por su `key`;
- conservar el `id` estable;
- no eliminar entradas existentes;
- no reactivar entradas deshabilitadas sin una orden explícita;
- mantener una versión de catálogo trazable;
- registrar el actor técnico del seed;
- no incluir datos reales de pacientes, empleados o incidentes.

## 4. Ubicación y configuración del servicio

Según `memory-bank/conventions.md`, el backend debe ser una API FastAPI centralizada dentro de `services/`, mientras que `docker-compose.yml` debe permanecer en la raíz del repositorio. No se creará un microservicio independiente para incidencias.

La estructura prevista, pendiente de confirmar el nombre de la API central, es:

```text
services/<central-api>/
	app/
		operational_incidents/
	alembic/
	alembic.ini
	pyproject.toml
	README.md
	README.es.md
docker-compose.yml
```

El `.env` local se usará sólo para desarrollo y deberá estar excluido del control de versiones. Se añadirá un `.env.example` sin credenciales reales. La API recibirá por variables de entorno la URL o los componentes de conexión de PostgreSQL gestionado. En entornos compartidos o productivos, los secretos deberán proceder del mecanismo seguro del entorno, aunque el contrato de configuración siga siendo el mismo.

## 5. Tablas maestras y referencias externas

Por **tablas maestras** se entienden los datos de referencia que describen entidades existentes de HealthCore, no los catálogos configurables de la incidencia. Ejemplos: las 12 clínicas, las áreas responsables, los sistemas afectados y las identidades de usuarios.

La decisión para esta primera implementación es:

- **No duplicar** en el módulo `OperationalIncident` los datos maestros completos de clínicas, empleados o sistemas.
- Mantener en la incidencia identificadores estables (`clinic_id`, `reporter_id`, `affected_system_id`, `responsible_area_id`) proporcionados por la API central o por un servicio maestro futuro.
- Aplicar foreign keys locales sólo si esas tablas existen dentro de la misma base de datos y su propietario está confirmado.
- Mientras no exista el sistema maestro, definir contratos de referencia y validación de existencia en el servicio; no inventar seeds con personas o clínicas reales.
- Los seeds de Fase 1 se limitarán a catálogos propios del gestor: canales, tipos, severidades, estados y, si se confirma que es configuración local, áreas responsables provisionales.

Así se evita que el gestor se convierta en dueño de datos maestros que pertenecen a otros dominios y se mantiene abierta la integración posterior.

## 6. Dependencias pendientes

Antes de implementar:

- confirmar el gestor de dependencias y el entrypoint de Python;
- confirmar el nombre y el entrypoint de la API centralizada;
- confirmar si las entidades maestras estarán en la misma base de datos o se validarán mediante otro servicio;
- confirmar estrategia de secretos para entornos compartidos y productivos;
- confirmar proveedor de PostgreSQL gestionado, backups, retención y restauración.

## 5. Validación mínima

La implementación deberá comprobar:

- ejecución desde una base vacía;
- ejecución repetida de seeds sin duplicados;
- fallo atómico de una operación de negocio y su historial;
- índices mediante `EXPLAIN` sobre listado y volumen abierto por severidad;
- rollback o restauración en un entorno no productivo;
- ausencia de PHI en datos iniciales, logs y auditoría técnica.

Validación realizada localmente:

- `uv run python -m compileall -q app alembic` pasa.
- `uv run alembic history` reconoce `0002_create_catalog_tables` como head.
- `Base.metadata` contiene `catalog` y `catalog_value`.
- No se ha ejecutado contra PostgreSQL porque no hay `DATABASE_URL` disponible en este entorno.
