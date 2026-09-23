# Convenciones del repositorio

- Monorepo organizado por responsabilidad: `uis/`, `services/`, `data/`, `agents/`, `skills/`, `mcps/`, `workflows/`, `packages/`, `shared/`, `docs/`, `infra/`, `scripts/` e `internal/`.
- Código funcional fuera de la raíz; cada componente debe incluir su propio `README`.
- Documentación bilingüe: `README.md` y `README.es.md`.
- Datos: `raw/` (fuente), `pipelines/` (ETL), `process/` (procesados), `eval/` (evaluación).
- Backend inicialmente centralizado en una API FastAPI; evitar microservicios prematuros.
- Un agente o skill por carpeta; usar `_template/` como base.
- `packages/` contiene código reutilizable; `shared/`, recursos comunes simples.
- `workflows/` contiene automatizaciones y orquestación.
- `infra/` contiene despliegue; `docker-compose.yml` debe permanecer en la raíz.
- Tipos TypeScript compartidos en `packages/shared/`, con nombres en inglés y `camelCase`.
- Desarrollo reproducible mediante Dev Container; Python con `uv` y JS/TS con `pnpm`.
- `CONTEXT.md` es la fuente central del contexto de negocio.
- Métricas y fórmulas deben documentarse explícitamente, incluyendo tratamiento de nulos y comparación temporal.
