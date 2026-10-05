# Operación y recuperación de Management

## Desarrollo local

1. Arrancar PostgreSQL y API: `podman compose up -d --build api`.
2. Aplicar esquema: `podman compose exec -T api uv run alembic upgrade head`.
3. Cargar exclusivamente seeds sintéticos: `podman compose exec -T api uv run seed-catalogs` y `podman compose exec -T api uv run seed-reference-data`.
4. Ejecutar comprobación: `podman compose --profile test run --rm --build test`.

La especificación se publica dinámicamente en `/openapi.json`; Swagger UI está
en `/docs`. Los tipos de consumidor están en `packages/shared/types/management.ts`.

## Rollback

Antes de una migración en un entorno compartido, realizar un backup probado.
Para revertir una revisión que no haya recibido datos que deban conservarse:

```sh
podman compose exec -T api uv run alembic downgrade -1
```

No se hace rollback destructivo sobre datos operativos sin una ventana aprobada
y restauración verificada. Las mutaciones de Management no borran registros:
se desactivan y quedan en `management_audit_event`.

## Promoción de datos

Los seeds `dev-*` y las revisiones sintéticas no se promueven. Antes de cargar
datos aprobados se requiere fuente propietaria, revisión de Tecnología y
Cumplimiento, importación versionada y reversible, validación de referencias,
evidencia de auditoría y un plan de rollback. M0 sigue siendo el control de
salida para esa promoción.
