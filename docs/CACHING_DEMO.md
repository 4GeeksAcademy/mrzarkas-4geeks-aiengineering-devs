# Demostración — Caching (6 minutos)

Preparar Chrome y un build de producción de la rama `feature/caching-optimisation`. La ruta es `/internal/incident-history`. Usar únicamente datos sintéticos. No grabar credenciales ni guardar contraseñas en Chrome o extensiones.

## 1. Arquitectura y problema — 45 segundos

Mostrar que `uis/backoffice` sigue en JavaScript nativo, `/frontend` es Next.js y la API existente vive en `/backend`. Abrir [CACHING_REPORT](CACHING_REPORT.md). Explicar: se difieren dos componentes internos y se reutiliza un cálculo de historial; se cachean dos catálogos, conservando autorización y frescura.

## 2. Dos descargas bajo demanda — 90 segundos

Usar el frontend ya compilado si contiene esta ruta. Si se necesita un preview aislado, los comandos siguientes crean sólo un contenedor frontend temporal; no inicializan ni escriben la base de datos:

```sh
podman compose build frontend
podman compose run --no-deps --rm -d --name healthcore-caching-demo -p127.0.0.1:3001:3000 frontend
```

Abrir `http://localhost:3001/internal/incident-history`. En Network, mostrar inicialmente la ausencia de los chunks Timeline/EventDetails, identificados en [caching-lazy-chunks.json](caching-lazy-chunks.json). Los hashes pueden cambiar al recompilar: usar el manifiesto del build correspondiente; no asumir que un hash antiguo sigue vigente.

En Console, instalar este fixture. Sólo sustituye la petición de historial de la página; los scripts de next/dynamic siguen descargándose normalmente:

```js
window.__cachingDemoFetch = window.fetch.bind(window);
window.fetch = (url, options) => url === '/api/incident-history'
  ? Promise.resolve(Response.json({
      statusHistory: [{
        id: 'synthetic-status-1',
        changed_at: '2026-01-01T10:00:00Z',
        from_status_value_id: null,
        to_status_value_id: 'synthetic-open',
        reason: '[REDACTED]'
      }],
      assignmentHistory: [{
        id: 'synthetic-area-1',
        changed_at: '2026-01-02T10:00:00Z',
        from_responsible_area_id: 'synthetic-a',
        to_responsible_area_id: 'synthetic-b',
        reason: '[REDACTED]'
      }]
    }))
  : window.__cachingDemoFetch(url, options);
```

Introducir `synthetic-only` en el campo JWT (es texto de prueba, no un JWT válido) y `00000000-0000-0000-0000-000000000001` como UUID. Consultar: aparece Timeline y se descarga su chunk. Seleccionar un evento: aparece EventDetails y se descarga el segundo chunk. Abrir/cerrar de nuevo el detalle: no hay otra descarga del módulo. Navegar por los botones con Tab y Enter; mostrar el motivo redactado.

Explicar explícitamente que el fixture valida render y carga de módulos, no autenticación. Recargar la página elimina el fixture y el token de estado. No continuar con credenciales reales.

## 3. useMemo con evidencia — 60 segundos

Mostrar `timeline.js`: `useMemo(() => chronology(statusHistory, assignmentHistory), [statusHistory, assignmentHistory])`. Mostrar `chronology.mjs`: copia, mezcla y sort; no muta los arrays. Seleccionar eventos conserva referencias; otra consulta reemplaza ambas dependencias.

Abrir [caching-react-comparison.json](caching-react-comparison.json): mismo historial de 2000 eventos, tres rondas de 20 warmup + 200 selecciones. Sin memo: 200 cálculos/ronda y p95 5,2–5,4 ms. Con memo: 0 recálculos y p95 4,2–4,5 ms. Los commits React siguen ocurriendo. La instrumentación y la variante sin memo sólo existieron en contenedores de medición; no forman parte del código de producto.

Para comprobar el cálculo real sin servidor ni datos persistentes:

```sh
node --experimental-default-type=module scripts/test_caching_frontend.mjs
node scripts/profile_react_chronology.mjs
```

Estos comandos son pruebas del cálculo/proxy y perfil Node, respectivamente; no sustituyen React Profiler.

## 4. Dos cachés y frescura — 90 segundos

Mostrar `backend/app/catalogs/cache.py` y los dos routers. Explicar TTL 60/30 s, digest de partición, JSON inmutable, límites de memoria, single-flight y consulta de generación incluso en hits. Abrir [caching-benchmark.json](caching-benchmark.json): SELECT 2→1 y 3→1, bytes iguales, p95 menor en las tres rondas; datos 28→228→28 mediante rollback.

Abrir [caching-workers.json](caching-workers.json): dos procesos previamente calientes; las tres mutaciones son visibles en el otro. Mostrar el A/B HTTP con concurrencia 10. No comparar sus latencias absolutas con el benchmark secuencial: tienen transporte y datasets distintos.

Mostrar la prueba de vigencia temporal y aislamiento en `backend/tests/test_caching.py`. Autorización se ejecuta antes del lookup; errores fuente no se convierten en 200. No cachear JWT, historial, auditoría, mutaciones ni decisiones de permisos.

No ejecutar escrituras sobre los catálogos de la aplicación durante la demo. La evidencia de mutación procede del validador que crea y elimina una base temporal aislada. Su comando reproducible y permisos requeridos están en backend/README.md.

## 5. Regresión y cierre — 45 segundos

Mostrar los resultados registrados: 150 tests, build Next, pruebas Node y OpenAPI de 28 operaciones conservado. Separar evidencia ejecutada del resultado académico: el evaluador aún no ha calificado la entrega.

Si se creó el preview temporal, cerrarlo:

```sh
podman stop healthcore-caching-demo
```

Cerrar la pestaña de prueba y rechazar cualquier sugerencia de guardar el texto sintético. No modificar el zoom global del navegador; para revisar responsive, usar DevTools a 393×852 y comprobar que Chrome está al 100 %.
