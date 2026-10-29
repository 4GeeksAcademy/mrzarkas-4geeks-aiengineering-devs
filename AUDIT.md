# Auditoría inicial de HealthCore Digital

Fecha: 29 de octubre de 2026. Rama: `features/measurement`.
Se audita el website existente en `frontend/` y el backoffice de incidencias,
incluido su resumen autenticado. `frontend/` es la referencia alternativa
autorizada en `AGENTS.md`; no se traslada a `uis/website`.

## Condiciones y evidencia

Website: http://localhost:3000/, build de Next.js 16.4.3 mediante el Dockerfile
(`pnpm build`), servidor standalone `node server.js`, Node v24.21.0,
`NODE_ENV=production`, build inicial `b2RxLvmJMB8ZBo1oXemlB`. Se ejecutó
`podman compose build frontend`: build correcto, capas iniciales reutilizadas
y misma imagen que el contenedor activo. No se ejecutó `next dev`.

Backoffice: Nginx 1.27, HTML/CSS/JS nativos servidos desde el árbol original,
sin HMR ni bundle de desarrollo. No hay build de JavaScript para esta aplicación.
Entrada `http://localhost:8080/#/incidents`; dashboard
`http://localhost:8080/#/summary` con JWT efímero de Dirección y métricas reales
de la base sintética (cuatro severidades con cero incidencias abiertas).

Lighthouse 12.8.2 y Chrome local; configuración y navegador exactos en cada JSON.
Tres navegaciones independientes por perfil, con caché fría y presets constantes.
El script `scripts/frontend-audit.mjs` conserva los cuatro scores, informe HTML,
captura del informe y de la página, y traza del primer ensayo. La serie numerada
es la base comparativa; los informes CLI sin número son exploratorios.
Instrucciones completas en [audit/README.md](audit/README.md).

No hay CrUX ni RUM para localhost. No se conoce INP/FID de campo y TBT no los
sustituye. Las métricas son de laboratorio y no describen usuarios de Internet.

## Puntuaciones iniciales

Valores de la serie de tres ejecuciones; los perfiles repetidos mantienen
estas puntuaciones. Los informes íntegros y capturas están en `audit/before/`.

| Página | Modo | Performance | Accessibility | Best Practices | SEO |
| --- | --- | ---: | ---: | ---: | ---: |
| Home | Escritorio | 100 | 100 | 96 | 100 |
| Home | Móvil | 99 | 100 | 96 | 100 |
| Entrada de incidencias | Escritorio | 100 | 95 | 100 | 90 |
| Resumen autenticado | Escritorio | 100 | 95 | 100 | 90 |

| Perfil | TTFB mediana, ms | LCP mediana, ms | CLS mediana | TBT mediana, ms |
| --- | ---: | ---: | ---: | ---: |
| Home escritorio | 14,85 | 463,59 | 0 | 0 |
| Home móvil | 9,70 | 1952,88 | 0 | 9,5 |
| Resumen escritorio | 2,42 | 323,18 | 0,03419 | 0 |

Home escritorio: LCP 446,24–474,20 ms; móvil: 1951,82–2041,68 ms.
Resumen: LCP 323,16–332,00 ms, CLS 0,02417–0,03419. La conexión automatizada
oculta el formulario y carga las tarjetas durante la navegación; no equivale
a una sesión ya conectada. Performance inicial saludable en ambas aplicaciones.

## Problemas y causa raíz

1. **Prioridad de la imagen LCP.** El trace y `lcp-discovery-insight` móvil
   muestran `priorityHinted: false`, aunque la imagen es descubrible, tiene
   preload y no usa lazy loading. El navegador no recibe la prioridad alta
   explícita recomendada para el contenido principal. Corrección dirigida:
   `fetchPriority="high"` en el `Image`, conservando dimensiones y preload.
   LCP ya está por debajo de 2,5 s; no se promete una mejora fuera del ruido.
2. **Error real de recurso en el website.** `errors-in-console` identifica
   `http://localhost:3000/favicon.ico` con 404. La aplicación no define icono,
   por lo que Chrome solicita el predeterminado. Proporcionar icono de marca
   local elimina la petición fallida, sin ignorar ni silenciar la auditoría.
3. **Contraste insuficiente del backoffice.** `color-contrast` identifica
   `.environment-badge`: texto `#42766a` sobre `#e7f0ed`, 4,48:1 para texto
   de 12 px; requiere 4,5:1. Oscurecer ese texto preserva la identidad visual
   y permite leer el aviso también a usuarios con visión reducida.
4. **Movimientos durante la conexión del resumen.** `layout-shifts` señala
   `#app` y el footer. `showConnectionState` oculta el formulario y
   `renderMetrics` reemplaza el estado de carga por tarjetas de otra altura.
   CLS menor de 0,1; se documenta, sin reservar grandes espacios ni cambiar
   el flujo de autenticación solo para mejorar artificialmente el score.
5. **TTFB acoplado al status.** La home hace `await fetch('/status')` sin caché
   antes de renderizar; en una caída puede esperar hasta 5 s. El TTFB medido
   es saludable. Es una hipótesis de degradación en fallo, no un problema
   demostrado del entorno actual. No se modifica la conexión ni su contrato.
6. **Recursos de Nginx sin compresión/cache duradera.** Lighthouse observa
   unos 40 KB de JS y 12 KB de CSS sin compresión. El payload y KPI son pequeños;
   es una mejora de servidor sugerida, no causa de un KPI deficiente medido.
7. **SEO de herramienta interna.** Falta descripción HTML; score 90.
   Se conserva el carácter interno del backoffice, sin inventar necesidades
   de indexación pública. Los avisos de JS heredado vienen del bundle de Next;
   no se cambia de framework por una auditoría secundaria.

No se encontró un error de hidratación. La foto de origen pesa 1.153.316 bytes,
pero Next/image entrega WebP de aproximadamente 14 KB en móvil: no es una
descarga de 1,1 MB. Sus dimensiones intrínsecas y las fuentes de sistema ya
evitan las causas habituales de CLS y bloqueo por fuentes externas.

## Análisis de refactorización

### Caso 1: constructores select de incidencias

En `uis/backoffice/operational-incidents/app.js`, `requiredSelectField`,
`selectField` y `fixedSelectField` repiten crear label, span y select,
asignar id y añadir opciones. Duplicar la estructura facilita divergencias
de accesibilidad y dificulta mantener atributos consistentes.

Extraer `createSelectField(labelText, id)` en un módulo local reutilizable
que devuelva `{ label, select }`. Mantener los wrappers existentes, sus tipos
de retorno, placeholders, `required`, selección y `name`; los consumidores
no cambian y las reglas de permisos permanecen en la aplicación.

### Caso 2: encabezados institucionales del website

En `frontend/app/page.js`, las secciones de herramientas y «Acerca de
HealthCore» repiten eyebrow y h2, con descripción opcional. Extraer
`SectionHeading({ id, eyebrow, title, description, className })`, reutilizado
en ambas. Preservar ids de `aria-labelledby`, nivel h2 y clases existentes.
El icono institucional y el contenido de cada sección permanecen fuera.

Ambas son extracciones locales; no se introduce una biblioteca compartida
entre React y DOM nativo ni se reestructura ningún frontend.

## Skill y prioridades

Se instaló y leyó [performance](skills/performance/SKILL.md) del repositorio
de Addy Osmani. La revisión del agente por indicador, clasificación de acciones
y limitaciones están en [audit/skill-review.md](audit/skill-review.md).
Primero se verifica la prioridad LCP; después favicon y contraste; finalmente
las extracciones con comprobaciones de comportamiento. Cada problema se mide
y documenta por separado.
