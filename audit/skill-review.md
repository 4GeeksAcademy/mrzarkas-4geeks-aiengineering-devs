# Uso del agente y de la skill performance

Skill instalada con `skill-installer` desde
https://github.com/addyosmani/web-quality-skills/tree/main/skills/performance
en `skills/performance/`. Se han leído `SKILL.md` y
`references/MEASUREMENT.md` y aplicado manualmente sus instrucciones en esta
sesión; no se afirma ejecución automática de otro agente. No se delegó trabajo.

## Interpretación de un indicador cada vez

1. **TTFB:** la home espera `/status` con timeout de 5 s. La medición local está
   por debajo de 800 ms; el timeout es un riesgo ante caída del backend, no una
   regresión demostrada en estas ejecuciones. No cambiar caché, conexiones ni
   arquitectura solo por esta hipótesis.
2. **LCP:** la imagen original tiene 1.153.316 bytes, pero Next/image entrega una
   variante optimizada, con dimensiones intrínsecas y preload. No confundir el
   tamaño del JPEG de origen con la transferencia real. LCP inicial saludable;
   revisar `network-requests` y el trace antes de recomendar otra optimización.
3. **CLS:** la home registra cero. El resumen presenta un desplazamiento pequeño
   de `#app` y `footer` al ocultar la conexión y sustituir la carga por tarjetas.
   Está por debajo de 0,1. No ocultar contenido ni eliminar la conexión para
   mejorar artificialmente la métrica.
4. **INP:** no disponible como dato de campo. TBT observado cero no demuestra
   INP inferior a 200 ms. No añadir telemetría a este hito.
5. **Performance:** 100 en escritorio en ambas aplicaciones, 99 en la primera
   ejecución móvil. No existe evidencia que requiera reescribir el frontend.

## Decisiones de corrección

| Hallazgo | Clasificación del agente con la skill | Acción |
| --- | --- | --- |
| Imagen LCP sin prioridad alta explícita, confirmada por el trace | Corrección dirigida de LCP | Añadir fetchPriority high y medir antes de otras correcciones |
| Favicon ausente de Next.js, HTTP 404 y error real de consola | Requerida para eliminar el error observado | Proporcionar icono local de marca |
| Aviso sintético de incidencias con contraste 4,48:1 | Requerida para texto pequeño legible, mínimo 4,5:1 | Oscurecer solo el texto del aviso |
| Constructores select duplicados | Requerida por el enunciado | Extraer una fábrica de campo reutilizada por los tres constructores |
| Encabezados de sección repetidos en la landing | Requerida por el análisis de refactorización | Extraer SectionHeading y usarlo en herramientas y presentación institucional |
| TTFB ante caída del backend | Hipótesis, no corrección requerida con estos datos | Documentar limitación; no cambiar integración |
| Compresión/cache de recursos del backoffice | Sugerencia: payload pequeño, Performance 100 | Documentar; requiere trabajo de servidor separado |
| Polyfills/JS de Next.js y CSS bloqueante de 12 KB | Sugerencia, sin KPI deficiente demostrado | Conservar stack y comportamiento |
| SEO 90 de backoffice sin descripción | Secundaria, no necesaria para herramienta interna | No fingir estrategia de indexación pública |

La skill proporciona recomendaciones generales, no emite por sí misma una
clasificación automática «requerida». La tabla identifica explícitamente el
juicio del agente basado en los informes, el contexto y los requisitos.
