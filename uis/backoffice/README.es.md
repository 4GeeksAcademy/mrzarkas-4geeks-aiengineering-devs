# HealthCore backoffice — migración progresiva a Next.js

Prototipo interno pre-MVP para desarrollo sintético aislado. Las aplicaciones nativas de `operational-incidents/` y `management/` siguen disponibles. Esta entrega no autoriza piloto ni producción.

## Instalación y ejecución

Requiere Node 24 y pnpm 10.18.3; usa Next 16.4.3, React 19.3.1 y TypeScript estricto. Ejecuta desde esta carpeta:

```sh
pnpm install --frozen-lockfile
APP_ENVIRONMENT=test BACKEND_URL=http://127.0.0.1:8000 pnpm dev
pnpm types:check
pnpm typecheck
pnpm test
pnpm build
APP_ENVIRONMENT=test BACKEND_URL=http://127.0.0.1:8000 pnpm start
```

Abre `http://127.0.0.1:3100/next`. El arranque copia assets generados al standalone; `HOSTNAME` y `PORT` permiten ajustar la escucha. Build/dev desactivan la telemetría del proveedor Next. La telemetría empresarial es independiente y opt-in (`TELEMETRY_ENABLED=false` por defecto).

## Rutas y permisos

| Ruta después de `/next` | Comportamiento |
| --- | --- |
| `/management/catalogs`, `/management/reference-data`, `/management/audit` | Consultas existentes, sólo lectura |
| `/summary`, `/incidents`, `/incidents/new`, `/incidents/[id]` | Métricas, filtros/página en URL, alta, edición, cambios auditados de estado/área e historia parcial |
| `/inventory` | Resumen parcial de la primera página; sin totales globales |
| `/inventory/items`, `/inventory/items/[id]` | NEW UI: catálogo, lotes, stock/historia clínicos y acciones autorizadas |
| `/inventory/stock`, `/inventory/reorder`, `/inventory/audit` | NEW UI: stock, reorden, auditoría y denegaciones dentro del ámbito |

Introduce un JWT sintético existente. El campo se limpia al conectar y el token/datos sólo viven en memoria; desconexión, 401 o recarga borran la sesión. Los claims decodificados controlan presentación; la API Python valida firma y permisos. El proxy usa `BACKEND_URL` fijo del servidor, allowlist OpenAPI revisada, body limitado, sin cookies y respuestas private/no-store. Rechaza entornos distintos de `development`/`test`; no expone `/auth/tokens`.

Incidencias conserva admin/technology/responsibleArea/compliance/direction. Direction sólo consulta resúmenes; responsibleArea edita título/descripcion en su área; sólo admin reasigna. Los cinco roles Inventory son independientes: inventoryAdmin escribe catálogo/lotes sin stock; operator registra in/out de sus clínicas; manager añade configuración, conteo y compensación; regional lee sus jurisdicciones; auditor consulta stock/auditoría dentro del país histórico autorizado. Ningún control concede permisos backend.

Los roles clínicos seleccionan UUID de clínicas asignadas; las consultas regionales e históricas conservan UUID validado por API. Los lotes se seleccionan por código de la lista paginada del artículo. La API actual no ofrece lookup nominal de clínicas para esos roles, GET configuración ni totales de listas. Siguiente sigue disponible en páginas cortas. El stock lo calcula la API. Las escrituras no reintentan automáticamente ni actualizan saldos optimistas; un resultado incierto exige consultar datos/historial y reconocer la verificación. No se persisten borradores ni datos de pacientes. Usa sólo texto operativo sintético.

## Convivencia local y preparación de rollback

El stack por defecto y el legado están intactos. `../../docker-compose.backoffice-next.yml` es un override opcional del Compose raíz: añade servicio privado standalone y plantilla Nginx alternativa. Revisa su combinación con variables ficticias y `--env-file /dev/null`; úsalo únicamente contra backend sintético aislado. Arrancar/desplegar un stack compartido requiere autorización separada.

Nginx conserva `/` y `/management/`, reenvía `/next` y `/next/`, y alias `/api-core/` al handler de contratos revisados. Conserva las rutas receptoras de telemetría. La web pública y su historial React permanecen en `/frontend`; el enlace del shell apunta a esa ruta local existente y cambiar de aplicación exige reconectar.

Rollback significa restaurar plantilla Nginx original/omitir override conservando API/esquema. Nunca eliminar volúmenes ni revertir migraciones. Inventory no tiene UI anterior: desactivar nuevas rutas no equivale a fallback legado. Activación, retirada, autenticación real, revisión de Cumplimiento/Gobierno del Dato y presupuestos de rendimiento siguen siendo gates separados.

## Validación sintética reproducible

`scripts/validation-api.py` usa el virtualenv de pruebas backend, `pgserver`, PostgreSQL temporal nuevo, seeds sintéticos y una clave JWT aleatoria sólo en el proceso. Aplica migraciones existentes únicamente a esa BD aislada y escucha en 18190; no lee `.env`. Ctrl-C lo detiene. Si falta tooling, instálalo en un entorno Python temporal; no apuntes la suite a datos compartidos.

Compila/arranca Next contra esa API fixture en loopback y, con Chrome instalado, ejecuta:

```sh
HC_SYNTHETIC_TESTS=1 BACKOFFICE_TEST_URL=http://127.0.0.1:3100 BACKOFFICE_TEST_API=http://127.0.0.1:18190 pnpm test:e2e
node --test operational-incidents/telemetry/tests/*.test.mjs
```

La suite exige opt-in y loopback. Prueba permisos API reales, denegaciones por ámbito, compensación única, sesión en memoria, resultado incierto y accesibilidad automática a 320/393/1350 px. Trace, video y screenshots están desactivados para evitar artefactos de credenciales. Las unitarias cubren contratos/errores, cancelación, HTML escapado y bloqueo de doble envío.

`contracts/openapi.json` es el snapshot generado del backend y revisado; `pnpm types:generate` regenera tipos transportados y `types:check` comprueba drift frente al snapshot, no frente a una API viva. Refrescarlo exige contrastar el backend real. Aquí no cambia ningún endpoint ni esquema backend.

`scripts/validation-legacy.py` sirve el legado sólo lectura en loopback 8080. `HC_SYNTHETIC_TESTS=1 node scripts/measure.mjs` compara Management cold/warm, tres rondas y dos anchuras contra la misma API, emitiendo sólo métricas. Declara alcance y límites de compresión; no es benchmark completo de producción. Evidencias y gates pendientes: `../../memory-bank/specs/migrationBackoffice/nextjs-migration/`.

La API fixture escucha por defecto en 127.0.0.1. Sólo para probar desde una máquina Podman aislada, `HC_QA_API_HOST=0.0.0.0` permite llegar desde el contenedor temporal; no usar este harness en un entorno compartido.

`python scripts/validation-regression.py` (con Python QA temporal y pgserver) ejecuta las pruebas backend existentes seleccionadas de auth/incidencias/Inventory/Management en otra BD nueva y detiene PostgreSQL. No sustituye la suite E2E.

## Ejecución del SDD de Inventory UI

`/next/inventory` muestra conteos parciales de primera página. Búsqueda/estado del catálogo y agrupación/prioridad de stock actúan sólo sobre la página recibida. Las fechas de consulta indican recepción local con referencia UTC, no timestamp de snapshot del servidor. Entradas/salidas, conteos y configuración de reorden confirman contexto activo; conversión de presentaciones y diferencia de conteo son orientativas. La compensación exige seleccionar un original del historial cargado, sin UUID arbitrario.

Una escritura incierta bloquea todos los formularios Inventory de la sesión en memoria, también después de navegar. El reconocimiento explícito permite revisar una nueva intención; no demuestra que la escritura anterior fallara. Desconectar/recargar limpia memoria sin revertir escrituras. No se añade idempotencia, conciliación exacta, endpoints, almacenamiento de navegador, identidad productiva ni disposición automática de auditoría.

La validación y las comprobaciones manuales de accesibilidad pendientes constan en `../../memory-bank/specs/inventory-manager-ui/plan.md`. Las pruebas utilizan sólo el harness API sintético aislado. Las dependencias de contenedor Linux requieren Vitest/build dentro del contenedor compatible; Chrome nativo macOS ejecuta E2E contra servidores temporales loopback. No existe script lint configurado.

Los bordes de campos activos y botones secundarios de Inventario usan el token muted existente para superar 3:1 sobre blanco. Se comprobaron estructura accesible, reflow a320px y ampliación CSS200%; siguen pendientes lector de pantalla real y zoom del navegador.
