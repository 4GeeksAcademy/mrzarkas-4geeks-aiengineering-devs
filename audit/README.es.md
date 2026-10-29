# Evidencia de auditoría frontend

Entorno local con datos sintéticos, 29 de octubre de 2026. Se mide la compilación
de producción de Next.js y el backoffice servido por Nginx; no se usa `dev`.
Esto no autoriza un despliegue para usuarios reales.

La [guía reproducible](README.md) contiene los comandos y describe cada archivo.
Instalar Lighthouse 12.8.2 temporalmente, indicar su directorio `node_modules`
mediante `AUDIT_TOOLS_DIR` y ejecutar `scripts/frontend-audit.mjs` para website
en escritorio/móvil, entrada del backoffice y resumen autenticado en escritorio.
Cada perfil usa tres navegaciones con Chrome nuevo y caché fría. La configuración
exacta y versión del navegador quedan en los JSON.

El resumen usa un JWT efímero de desarrollo de Dirección, con acceso de solo
lectura a métricas. No se guardan credenciales ni se modifican datos operativos.
Los informes y capturas iniciales se conservan en `before/`; las mediciones
posteriores en `after/` y las verificaciones incrementales en `steps/`.

Se comparan medianas y rangos. No hay CrUX/RUM en localhost; INP/FID de campo no
están disponibles. TBT no equivale a INP. TTFB es una medición del servidor local.
El recorrido autenticado incluye conectar el formulario y cargar las tarjetas;
solo se compara con ese mismo recorrido tras los cambios.
