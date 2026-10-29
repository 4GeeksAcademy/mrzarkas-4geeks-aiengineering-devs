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
