# HealthCore Inventory Manager — Plan técnico ejecutado

**Estado:** implementación validada, demostración local operativa; Podman bloqueado.
**Versión:** 1.0 · **Fecha:** 2026-11-02

## Arquitectura implementada

API central existente en `backend/` (traslado aprobado documentado en README), FastAPI, SQLAlchemy async, PostgreSQL y Alembic. Módulo `app/inventory/`; no nuevo servicio ni frontend. Integración en `app/main.py`, registro de modelos y extensión de scopes JWT de desarrollo. Roles de inventario no heredan capacidades de incidencias.

Persistencia `0010_inventory`: artículos, configuración clínica/artículo, lotes, movimientos append-only y auditoría. `0011_inventory_audit_policy`: snapshots geográficos/resultados y denegaciones append-only; no adivina país de eventos antiguos. No modifica migraciones históricas anteriores. Stock por suma de deltas, sin saldo editable. Escrituras bloquean clínica y artículo; mismo artículo serializa operaciones entre clínicas. Se requiere PostgreSQL READ COMMITTED. Contención por artículo es un límite conocido.

## Secuencia de entrega y responsabilidades

1. Persistencia y nuevas migraciones.
2. Contratos, políticas, servicios y rutas de inventario, integración JWT y pruebas.
3. Carga sintética repetible y documentación operativa.
4. Especificaciones y trazabilidad del Memory Bank.

Se agrupan tareas relacionadas en commits coherentes por responsabilidad; reemplaza el compromiso preliminar de un commit por tarea, porque contrato, servicio y autorización comparten dependencias. Los hashes reales se registran en `tasks.md`; no se fabrican hashes de tareas individuales.

## Validación ejecutada

- Python 3.12; `.venv` reconstruido con `uv sync --frozen`, lockfile sin cambios. Entorno roto conservado en `/private/tmp/healthcore-broken-venv-20261102`.
- Suite completa: **418 passed**, sin skips. Comando: `/private/tmp/healthcore-inventory-py312/bin/python /private/tmp/run_inventory_validation.py`; evidencia `/private/tmp/inventory-validation-final.log`.
- 21 pruebas de inventario/política sobre PostgreSQL aislado; fresh upgrade, upgrade desde `0009`, repetición, downgrade/re-upgrade desechable y preservación de eventos legacy. Metadata `inventory_*` sin diferencias.
- Suite global emplea claves sintéticas de telemetría, bases separadas `telemetry_validation`/`inventory_validation_*` y adaptador temporal NullPool para tests antiguos con múltiples event loops. No cambia el pool de producción. Los scripts temporales son evidencia de esta ejecución, no tooling permanente del repositorio.
- `alembic check` global identifica discrepancias preexistentes de Compliance/índices/FKs fuera de inventario; no se declara limpio el esquema global.
- Demostración en PostgreSQL aislado persistente: migraciones hasta `0011`, seed de maestros, carga de inventario dos veces (6 y 0 movimientos). Smoke HTTP: salud, catálogo, seis saldos, regiones US/UK, reorden y denegación 403 duradera.
- `git diff --check` y revisión de contenido: sin errores de espacios ni secretos/PHI nuevos.

## Entorno local y pendientes

API `http://localhost:8000/docs`; base de demostración aislada en `/private/tmp/healthcore-inventory-demo-db`. Launcher de esta sesión: `/private/tmp/start_inventory_demo.py`, ejecutado con el Python temporal que incluye pgserver; emplea Python del `.venv` reparado para API/migraciones/seed. pgserver es sólo tooling temporal y no dependencia del proyecto. Conservar la base al detener; se arranca el launcher nuevamente para reutilizarla. Los directorios temporales pueden ser limpiados por el sistema; no son almacenamiento de producción.

Podman no recuperado: almacenamiento overlay devuelve `readlink ... invalid argument`; tras reinicio la máquina informa no estar en ejecución. No se borraron máquinas ni volúmenes. Docker Compose no fue validado de nuevo. Recuperar Podman sin pérdida de datos requiere diagnóstico adicional y, si fuera necesario resetear, autorización explícita de la operación destructiva.

Revisión simulada `HC-INV-APPROVAL-2026-11-02`: roles/ámbito, auditoría y retención aprobados para escenario ficticio. Purga/disposición ejecutable, interfaz, SSO/OIDC y autorización de piloto/producción siguen fuera de esta entrega.
