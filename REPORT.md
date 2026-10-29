# Resultado de la auditoría frontend

Fecha: 29 de octubre de 2026. Aplicaciones: `frontend/` (website) y
`uis/backoffice/operational-incidents/` (entrada y resumen autenticado).
Se conserva la arquitectura y el comportamiento de las herramientas.

## Correcciones aplicadas

| Commit | Cambio | Verificación incremental |
| --- | --- | --- |
| `1f44787` | Baseline de producción, capturas, AUDIT y skill performance | Tres mediciones por perfil antes de modificar frontends |
| `0bff8c3` | Prioridad alta explícita de la imagen LCP, manteniendo Next/image, preload y dimensiones | `audit/steps/01-lcp-priority/`: priorityHinted false→true; Performance móvil permanece 99; no mejora de tiempo demostrada |
| `8bf1cba` | Icono SVG local con metadatos nativos de Next.js | `audit/steps/02-favicon/`: desaparece el 404 de favicon y Best Practices 96→100 |
| `5e7618d` | Texto del aviso sintético con el color oscuro de marca | `audit/steps/03-badge-contrast/`: color-contrast pasa y Accessibility 95→100 |
| `6f5f516` | `createSelectField` extraído e integrado en tres constructores DOM | `audit/steps/04-select-field/`: Lighthouse estable y prueba de filtros/campos sin enviar datos |
| `82e5d39` | `SectionHeading` extraído y usado en herramientas y presentación institucional | `audit/steps/05-section-heading/`: build y Lighthouse correctos, ids y niveles h2 preservados |

Cada problema está en un commit propio y se volvió a medir la misma URL antes
de continuar. Las capturas y JSON/HTML incrementales permanecen en `audit/steps/`.
Las mediciones finales se hicieron tras todas las correcciones y refactorizaciones.

## Puntuaciones antes y después

Tres ejecuciones independientes por perfil con Lighthouse 12.8.2, caché fría,
Chrome local y configuración idéntica. Los tres resultados de cada categoría
coinciden con la tabla. Se conservan íntegros en `audit/before/` y `audit/after/`.

| Página y modo | Performance | Accessibility | Best Practices | SEO |
| --- | ---: | ---: | ---: | ---: |
| Home escritorio | 100→100 | 100→100 | **96→100** | 100→100 |
| Home móvil | 99→99 | 100→100 | **96→100** | 100→100 |
| Entrada backoffice escritorio | 100→100 | **95→100** | 100→100 | 90→90 |
| Resumen autenticado escritorio | 100→100 | **95→100** | 100→100 | 90→90 |

Hay mejora verificable de al menos una puntuación por frontend. Performance
ya era saludable y no se cambió contenido ni se desactivaron auditorías para
buscar un 100 artificial. El backoffice conserva su carácter interno.

## KPI: medianas y límites de interpretación

| Perfil | TTFB, ms antes→después | LCP, ms antes→después | CLS antes→después | TBT, ms antes→después |
| --- | ---: | ---: | ---: | ---: |
| Home escritorio | 14,85→46,22 | 463,59→477,44 | 0→0 | 0→0 |
| Home móvil | 9,70→29,81 | 1952,88→2042,13 | 0→0 | 9,5→18 |
| Entrada backoffice | 3,15→1,74 | 322,95→364,92 | 0,01002→0,01002 | 0→0 |
| Resumen escritorio | 2,42→2,08 | 323,18→370,70 | 0,03419→0,01949 | 0→0 |

Rangos de LCP antes→después:

- Home escritorio: 446,24–474,20 → 473,26–491,17 ms.
- Home móvil: 1951,82–2041,68 → 2028,67–2046,38 ms.
- Resumen: 323,16–332,00 → 365,36–409,78 ms.
- Entrada backoffice: 322,80–323,42 → 362,57–365,04 ms.

**No se ha demostrado una mejora de velocidad.** Las medianas de LCP suben
aproximadamente 3,0% en escritorio, 4,6% en móvil y 14,7% en el resumen, aunque
todas siguen por debajo de 2,5 s y la puntuación de Performance se mantiene.
La extracción DOM añade una petición pequeña a `select-field.js`; su cadena
de dependencia puede contribuir al incremento del resumen. La comparación
local también incluye variación de servidor y navegador: no se atribuye toda
la diferencia a una sola causa ni se considera una mejora por estar en verde.

La prioridad LCP corrige un diagnóstico de descubrimiento/prioridad confirmado,
pero no reduce el LCP medido aquí. El descenso de CLS del resumen no se atribuye
al cambio de contraste ni a la refactorización: el rango final 0,00449–0,03419
incluye el inicial 0,02417–0,03419 y depende del recorrido automatizado de conexión.
TTFB final móvil varía entre 12,04 y 179,52 ms; no se presenta como mejora.

No hay CrUX/RUM ni medición de INP/FID de usuarios reales en localhost.
TBT no equivale a INP. Estos resultados son de laboratorio, con datos sintéticos,
y no certifican el rendimiento o cumplimiento de una producción pública.

## Validación funcional y reproducibilidad

El website se recompiló después de cada cambio relevante con
`podman compose build frontend` y se sirvió con
`podman compose up -d --no-deps frontend`. Build final
`lRXGWsDXnakXg3llTSUFr`, Next.js 16.4.3, Node v24.21.0,
`NODE_ENV=production`, proceso `node server.js`. No se usó `next dev`.
El backoffice sirve código nativo por Nginx; no tiene build de desarrollo.
Versiones y condiciones en [audit/environment.json](audit/environment.json).

Las comprobaciones reales de navegador pasaron tras ambas extracciones:

- Home a 1350 y 393 px: sin desbordamiento, imagen cargada, icono, dos destinos
  correctos y enlace de salto accesible con Tab.
- Filtro de severidad aplicado: la selección se mantiene tras actualizar ruta.
  El selector de ordenación conserva «descendente» como valor predeterminado.
- Siete select obligatorios del alta conservan label, name y required. Elegir
  jurisdicción carga las clínicas; el formulario **no se envió**.
- Desconexión vacía el token y restaura el formulario; Management responde.
- Sin excepciones JavaScript no controladas en las páginas verificadas.

Salida reproducible en `audit/steps/05-section-heading/browser-checks.json`.
Sintaxis de los módulos DOM y de ambos scripts correcta; `git diff --check`
sin errores. No existen scripts de lint/test en el paquete Next.js: no se
afirma que se hayan ejecutado. No se cambiaron backend, API, autorización,
secretos, migraciones, configuración de servidor ni datos operativos.

El JWT efímero de desarrollo se usa solo en memoria; los argumentos de la
traza se redactan antes de escribirla. Los artefactos se revisaron para evitar
credenciales. Los datos de las tarjetas son sintéticos y se obtienen de la API.

## Valoración del impacto

El mayor impacto observable para el website es eliminar una petición fallida
real, con +4 puntos de Best Practices. Para el backoffice es hacer legible el
aviso de entorno: +5 puntos de Accessibility. Son correcciones de causas
verificadas, no ocultación de avisos ni eliminación de funcionalidades.

Las extracciones mejoran mantenimiento y consistencia semántica; no se les
atribuye una ganancia de rendimiento. La prioridad de imagen deja una petición
LCP correctamente priorizada, con impacto de velocidad no demostrado en este
entorno. Para un futuro ciclo, conviene medir tráfico real y valorar la petición
adicional del módulo DOM, compresión/cache de Nginx y el timeout del status,
antes de añadir más complejidad.

La skill [performance](skills/performance/SKILL.md), instalada con el instalador
oficial, guio la interpretación secuencial TTFB→LCP→CLS→INP→Performance. Evidencia,
clasificación de acciones y decisiones en [audit/skill-review.md](audit/skill-review.md).
