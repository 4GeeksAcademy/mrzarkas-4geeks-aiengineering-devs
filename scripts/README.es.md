# Carpeta `scripts`

## Auditoría frontend

`frontend-audit.mjs SALIDA website|backoffice|summary desktop|mobile [1-3]`
ejecuta Lighthouse 12.8.2 sobre los servidores locales de producción. Por defecto
son tres ejecuciones independientes con caché fría. Indicar el `node_modules`
temporal mediante `AUDIT_TOOLS_DIR` o como último argumento. Configuración,
artefactos y límites en `../audit/README.md`.

`frontend-checks.mjs TOOLS_DIR [SALIDA_JSON]` verifica home en escritorio/móvil,
teclado, enlaces, filtros, selección de jurisdicción/clínica sin enviar y
desconexión. Obtiene un JWT efímero sintético de desarrollo; no escribe datos
operativos. Requiere puppeteer-core temporal de Lighthouse y Chrome local;
no añade dependencias a las aplicaciones. Salida predeterminada en `/private/tmp/`.

Esta carpeta contiene **scripts auxiliares** del monorepo: automatizaciones de desarrollo, utilidades de mantenimiento, tareas repetitivas (setup, lint, migraciones, generación de datos, etc.) y tooling interno.

- **Propósito principal**: agrupar herramientas de soporte que no pertenecen a una app/agente/pipeline específico, pero facilitan el trabajo del equipo.
- **Recomendación**: documenta cada script (qué hace, parámetros, requisitos, ejemplos de uso) y procura que sean reproducibles (y seguros) en distintos entornos.

## Baseline de caching

`python3 scripts/caching_inventory.py` lee fuentes del repositorio e imprime
inventario de operaciones y tamaños sin arrancar servicios ni consultar la base.
`node scripts/caching_calculation_profile.mjs` perfila el cálculo extraído de
cronología nativa con eventos sintéticos en memoria; no es una medición de
navegador ni React. Resultados y límites: `docs/CACHING_REPORT.md`.


`node scripts/profile_react_chronology.mjs` mide el cálculo real de la cronología
React con entradas sintéticas; no mide renders de React.
`node --experimental-default-type=module scripts/test_caching_frontend.mjs`
comprueba el cálculo y el proxy privado con red simulada.
`caching_profile_setup.cjs` instrumenta sólo `/app` dentro de un contenedor de
build frontend descartable; montar como solo lectura y ejecutar
`node /tmp/setup.cjs` seguido de `pnpm exec next build --profile`.
No está pensado para ejecutarse sobre el checkout. Las observaciones de navegador
están en `docs/caching-browser.json`; la aplicación entregada no lleva instrumentación.

Definir `CACHING_PROFILE_MODE=direct` sólo en el build descartable para comparar el mismo cálculo sin useMemo. Resultados: `docs/caching-react-comparison.json`.
