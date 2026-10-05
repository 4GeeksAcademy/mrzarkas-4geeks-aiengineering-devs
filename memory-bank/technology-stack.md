# Stack tecnológico

## Base disponible hoy

El repositorio es un monorepo organizado por responsabilidad: uis/, services/, data/, agents/, skills/, mcps/, workflows/, packages/, shared/, docs/, infra/, scripts/ e internal/.

- Backend: una API centralizada en **FastAPI**; no crear microservicios prematuramente.
- Python: **uv**. JavaScript/TypeScript: **pnpm**.
- Tipos compartidos: packages/shared/, paquete @repo/shared-types, con nombres en inglés y camelCase.
- Desarrollo reproducible mediante Dev Container.
- Datos: data/raw → data/pipelines → data/process; evaluación en data/eval.
- Despliegue en infra/; cuando exista, docker-compose.yml se mantiene en la raíz.

## Implicaciones para incidencias

El gestor vivirá inicialmente como módulo de la API FastAPI y su backoffice como aplicación en uis/, no como un servicio aislado. Los contratos que consuman ambos se añadirán a packages/shared/ si TypeScript los necesita.

No hay todavía base de datos, aplicación FastAPI, UI, autenticación, telemetría ni automatización implementadas. Por HIPAA/UK GDPR, los logs y payloads deben evitar PHI y conservar una auditoría de accesos y cambios.
