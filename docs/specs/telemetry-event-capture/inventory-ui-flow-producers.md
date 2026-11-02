# Siguiente lote — product_selected y order_started

Fecha2026-11-02. Estado DESIGN_READY; sin implementación/pruebas del incremento.
Solicitud: continuar después de inventory_viewed. Es un cambio de contrato público
de API (ruta nueva), contexto firmado y UI; requiere aprobación concreta.

## Gestos y cobertura

- product_selected: clic explícito normal en enlace de artículo desde stock.tsx,
  cuyo enlace ya incorpora clínica de la fila. No emitir por render, prefetch,
  navegación programática ni lectura global del catálogo sin clínica. Enlace y
  navegación siguen funcionando si telemetría falla. Selección de perfiles con
  stock:read permanece sujeta a alcance clínico/jurisdiccional de backend.
- order_started: primera interacción real en campos de entrada/salida del
  formulario ClinicalActions, con artículo/clínica/lote válidos y stock disponible;
  no por render/foco programático. kind actual determina inbound/outbound.
  Una vez por flujo y dirección; cambios de artículo/clínica/lote o dirección
  inician flujo nuevo. No por conteo, compensación, configuración o envío automático.
- Un detalle abierto directamente puede emitir order_started sin product_selected:
  no inventar un clic previo. Una selección puede existir sin inicio posterior.
- Persistencia/idempotencia de negocio y correlación con movimientos confirmados
  quedan fuera: flowId no equivale a operationId del movimiento.

## Diseño propuesto

La API ya tiene cola efímera interna20/10; el navegador no posee HMAC y los dos
eventos requieren flowId `ps_` SHA256. Para no permitir UUID de recurso/flowId
arbitrarios en POST /telemetry/events, proponer un ingreso dedicado de gestos UI.
Los eventos describen gestos declarados por la UI autenticada, no hechos de stock;
la validación servidor no demuestra que el usuario humano realizó el clic.

1. Nueva ruta **POST /telemetry/inventory-flow** en
   `backend/app/telemetry/inventory_flow_router.py`, registrada en main.py.
   Request cerrado: action enum product_selected/order_started, clinicId UUID,
   itemId UUID, direction nullable inbound/outbound (obligatoria para inicio),
   flowToken opcional. Response cerrada: accepted bool, flowId seudónimo y
   flowToken breve firmada, expiresAt. Sin cambios de envelope ni contrato1.2.0.
2. Bearer autenticado; selección exige stock:read y alcance de clínica. Inicio
   exige movement:write, clínica/artículo activos y configuración existente.
   Backend resuelve país US/UK activo y valida recurso en sesión independiente;
   no toma país/identidad de browser. Rechazos no alteran permisos, inventario o
   auditoría existentes; ruta sólo de telemetría, sin movimiento ni nueva auditoría.
3. UUID de flujo generado exclusivamente en servidor; flowId derivado de clave
   regional de recurso con propósito separado inventory_flow. flowToken firmado
   regional, audiencia distinta del contexto/event ingress vigente, TTL máximo
   300s limitado también por caducidad Bearer. Vincular sujeto HMAC, clinicBinding,
   itemBinding, flujo, dirección cuando esté iniciada, environment y versión de
   clave. Revalidar todo en cada gesto; no confiar en token sin firma, expirado,
   de otra región/actor/clínica/artículo. No exponer UUID ni claves en respuesta.
4. Nuevo productor `telemetry/inventory_flow_producer.py`: dos tipos por sink
   interno únicamente. Envelope sesión/request=null, userId HMAC regional;
   properties selection jurisdiction/environment/flowId, inicio añade direction.
   Nueva allowlist SERVER_EVENTS, sin ampliar admisión de POST /telemetry/events.
   Reutilizar límites16/100ms y cola20/10, diagnóstico/cierre existentes.
5. Si telemetría está disabled/config inválida: respuesta segura503 o accepted=false,
   sin credencial activa. Saturación descarta capture de mejor esfuerzo; no afecta
   navegación/formulario. No prometer exactly-once: repetición maliciosa del gesto
   o fallo de red puede duplicar o perder eventos, sin dedup persistente.
6. Hook/módulo independiente de flujo en
   `uis/backoffice/src/lib/telemetry/inventory-flow.ts` integrado en Provider:
   mapas/credenciales sólo en memoria, máximo16 flujos y expiración breve,
   AbortSignal/session generation, un vuelo por flujo y timeout5s, sin retries
   automáticos ni almacenamiento/logs. El Provider mantiene su servicio común de
   incidencias/Management como está; este canal permite inventory UI sin tratarlo
   como aplicación incidents. Obtener enabled del config.json existente; no .env.
7. stock.tsx y clinical-actions.tsx invocan API de flujo por gestos acotados, sin
   bloquear navegación/envío ni emitir datos de campos. Reutilizar token de selección
   para inicio sólo si coincide el mismo artículo/clínica y sigue vigente. Cambio de
   dirección/ámbito invalida flujo. No compartir credenciales entre sesiones.

Archivos previstos: main.py, telemetry/server.py, nuevos inventory_flow_router.py,
inventory_flow_producer.py, inventory_flow_identity.py (firma/resolución), nuevo
test_telemetry_inventory_flow.py; Provider, nuevo módulo de flujo, stock.tsx,
clinical-actions.tsx y pruebas UI/Node pertinentes; README bilingües backend/
inventario/backoffice y expediente. Podría reutilizar helpers de identidad existentes
sin modificar la admisión/caducidad del contexto público actual. Sin nuevas claves,
contratos JSON, modelos/migraciones, auth policies, .env, dependencias, infraestructura,
Memory Bank/Rules, commit o despliegue. No introducir una segunda implementación
de batching en navegador: son gestos puntuales autenticados; batching en cola servidor.

## Criterios de aceptación y pruebas previstas

- Gestos positivos US/UK, separación de HMAC y flujo compartido selección→inicio;
  dirección correcta, inicio directo sin selección inventada.
- Rol/scope, inactive/missing clínica/item/config, credencial manipulada/expirada,
  actor/item/clínica/región distintos y flowId browser arbitrario rechazados.
- Cambios de sesión/ámbito/dirección, carreras/respuestas tardías y unmount no
  utilizan credenciales posteriores ni duplican captura de una interacción UI.
- Disabled/503/saturación/timeout no afectan navegación ni operación; sin token
  en logs/persistencia, sin contenido de formulario ni UUID en eventos.
- POST /telemetry/events continúa rechazando ambos tipos; nueva ruta valida
  payload cerrado/autenticación. Nueva OpenAPI documentada sin alterar contratos
  de movimientos, validaciones y lecturas actuales.
- Backend/Node/UI unitarios, TypeScript/build y E2E sintético pertinente;
  integración PostgreSQL aislada y regresiones de los tres lotes anteriores.
  NOT_RUN hasta implementación autorizada. Revisión validate-delivery.

Revisión de Cumplimiento/contexto-identidad pendiente: aprobación del prototipo
no se presenta como revisión de Claire, aprobación de datos reales ni producción.


## Implementación autorizada y evidencia — 2026-11-02

El desarrollador aprobó expresamente «Sí, autorizo este lote para el prototipo
sintético». Estado técnico **IMPLEMENTED_VALIDATED_SCOPED** para los gestos
descritos; secciones DESIGN_READY/NOT_RUN anteriores son históricas.

Ruta nueva y dos esquemas OpenAPI añadidos a contracts/openapi.json de Next,
tipos generados actualizados y censo backend actualizado46→47 operaciones.
Estos cambios son necesarios para la ruta pública expresamente aprobada: el proxy
usa OpenAPI como allowlist y rechaza lo que no está publicado. No se ampliaron
otros métodos/rutas, políticas, entorno/.env ni admisión de /telemetry/events.
El helper resource_id añade únicamente propósito inventory_flow; HMAC existentes
conservan valores. Los cinco tipos browser generales y su módulo siguen intactos.

Contexto backend: firma de audiencia separada, TTL≤300s/Bearer, no extender TTL
existente; subject/clinic/item bindings HMAC, región/dirección/environment/keyVersion.
Una selección puede reutilizar su flujo para inicio; dirección distinta de una
credencial ya iniciada se rechaza. UI usa reset/nuevo flujo en cambios de dirección/
clínica/artículo/lote; mapas≤16, expiración y AbortSignal. No lote/valores de campos
en requests de telemetría. Sesión anterior se aborta al desconectar/cambiar JWT.
No correlación prometida con operationId, ni dedup malicioso global.

### Validaciones ejecutadas

Python3.12/backend/.venv. PostgreSQL16 efímero tmpfs en loopback18491,
inventory_validation_flows; DATABASE_URL e INVENTORY_TEST_DATABASE_URL dirigidas
exclusivamente allí; APP_ENVIRONMENT=test. Migraciones0001–0011 correctas.

- `.venv/bin/pytest -q tests/test_telemetry_inventory_flow.py tests/test_telemetry_inventory_view.py tests/test_telemetry_inventory_validation.py tests/test_telemetry_inventory.py tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_inventory_demo.py tests/test_telemetry_server.py tests/test_caching.py`: **165 passed**,2.12s, sin skips.
- `.venv/bin/pytest -q -m 'not integration' tests`: **520 passed,28 deselected**,2.77s.
- Node24 Alpine sobre dependencias existentes: Vitest **64 passed**,3.01s; incluye7 tests de flujo (memoria≤16, expiración, carreras, disabled, fallos sin retries, dirección/lote y flujo compartido).
- TypeScript noEmit y Next16.4.3 build: **PASS**; tipos regenerados con openapi-typescript7.13.0. Sin nuevas dependencias.
- Chrome Playwright: nuevo E2E de clic real y primer cambio de cantidad **1 passed**,2.0s; credencial compartida/accepted=true, dos cambios de cantidad sólo un inicio, cero almacenamiento browser.
- Regresión existente inventory-ui: dos pruebas PASS y detalle histórico PASS en repetición después de cargar la demo requerida; total3 escenarios distintos aprobados, no suite nueva inventada.
- Servidores sólo de pruebas: API18192 y Next13103, sobre PostgreSQL efímero; claves exclusivamente sintéticas generadas en harness /private/tmp, nunca .env real.

Recuentos backend solapados; no sumar165 y520. Integraciones ajenas no ejecutadas.
Incidencias corregidas: PyJWT require considera ausente una direction=null; se
excluyó del require manteniendo validación exacta de claims/código. Vitest nativo
no podía cargar binarios Linux de node_modules; ejecutado en Node24 Linux. Censo
OpenAPI y allowlist proxy desconocían nueva ruta; sincronizados y E2E repetido.
El harness cerraba pool en otro event loop; se corrigió preparación aislada. E2E
de detalle necesitaba demo sintética ausente; cargada únicamente en base efímera.

Cobertura actual26 tipos al menos parcial y13 sin productor: cinco de inventario
(umbrales activar/despejar, escritura directa rechazada, abandono y reconciliación)
y ocho de otros dominios. Los eventos ya instrumentados mantienen brechas descritas.
Revisión de Cumplimiento/contexto-identidad pendiente; aprobación de prototipo no
equivale a revisión de Claire ni cierre de entrega integral. Sin commit/push,
reconstrucción de contenedores compartidos ni producción.
