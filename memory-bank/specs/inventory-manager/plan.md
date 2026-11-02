# HealthCore Inventory Manager — Plan técnico ejecutado

**Estado:** implementación y entorno Compose aislado validados; bloqueo de Podman resuelto.
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

Diagnóstico inicial (resuelto en el cierre operativo siguiente): almacenamiento overlay devuelve `readlink ... invalid argument`; tras reinicio la máquina informa no estar en ejecución. No se borraron máquinas ni volúmenes. Docker Compose no fue validado de nuevo. Recuperar Podman sin pérdida de datos requiere diagnóstico adicional y, si fuera necesario resetear, autorización explícita de la operación destructiva.

Revisión simulada `HC-INV-APPROVAL-2026-11-02`: roles/ámbito, auditoría y retención aprobados para escenario ficticio. Purga/disposición ejecutable, interfaz, SSO/OIDC y autorización de piloto/producción siguen fuera de esta entrega.

## Cierre operativo de Podman y Compose — 2026-11-02

Podman 5.5.2 recuperado sin eliminar máquinas, imágenes, contenedores ni volúmenes existentes. El error API `readlink .../storage/overlay: invalid argument` se debía a cuatro capas registradas con archivos `link` y `lower` vacíos. Los enlaces simbólicos originales y el registro de padres permitieron restaurar ocho archivos de metadatos. Copias originales y manifiestos: `/var/home/core/inventory-podman-repair-20261102`, dentro de la máquina. Tres directorios no registrados se conservaron sin cambios. Reinicio de socket/servicio API; comprobación final de imágenes y contenedores: exit0. No se afirma saneamiento integral de otros proyectos alojados en Podman.

Compose completo construido y arrancado desde el archivo existente, sin modificar infraestructura ni `.env` del repositorio. Proyecto aislado `healthcore-inventory-validation`, volumen nuevo propio, credenciales sintéticas en archivo temporal con modo 0600. DB, API y frontend saludables; backoffice responde HTTP200. `db-init` aplicó migraciones hasta `0011` y los seeds. No se tocó el volumen `healthcore-stack_mvp-postgres-data`.

Comandos ejecutados:

```bash
podman compose -p healthcore-inventory-validation --env-file /private/tmp/healthcore-inventory-compose.env up --build -d
podman compose -p healthcore-inventory-validation --env-file /private/tmp/healthcore-inventory-compose.env exec -T backend uv run --no-sync python -m app.inventory.demo
python3 /private/tmp/validate_inventory_compose.py
backend/.venv/bin/python /private/tmp/smoke_inventory_compose.py
podman images --format '{{.ID}}'
podman ps --format '{{.Names}} {{.Status}}'
```

Todos terminaron en exit0. Seed de inventario ejecutado dos veces: 6 y 0 aperturas. Smoke HTTP confirma catálogo, seis saldos, US/UK, tres alertas y denegación 403 auditada. Saldo US: 10/25/100; UK: 5/20/40. Web y backoffice/Management: HTTP200. Regresión en imagen test de Compose: **418 passed in 7.12s**, sin skips, usando bases nuevas `inventory_validation_tests` y `telemetry_validation` separadas de la demo. Mantiene el adaptador temporal NullPool y claves sintéticas descritos arriba. Log: `/private/tmp/inventory-compose-validation.log`.

URLs del Compose aislado: API `http://localhost:18080/docs`, web `http://localhost:13000`, backoffice `http://localhost:18081`, Management `http://localhost:18081/management/`. El demo nativo anterior en puerto 8000 se conserva separado. Los archivos temporales pueden caducar; conservar configuración segura antes de reutilizar este entorno a largo plazo. No hay despliegue ni autorización de producción.

Revisión final con validate-delivery: PASS para recuperación local conservando datos, Compose aislado y evidencia de entrega. Informe de sesión: `/private/tmp/inventory-compose-delivery-review.md`. Retención/purga ejecutable, interfaz de inventario y SSO/piloto/producción conservan sus exclusiones originales.
