# SDD — HealthCore Inventory Manager UI · tasks

## Lectura y clasificación

Fecha de discovery: 2026-11-02. Rama `feature/inventory-manager`; árbol limpio antes del trabajo. La fase inicial autorizó investigación y tres documentos. La petición posterior «ejecuta memory-bank/specs/inventory-manager-ui» autoriza la implementación frontend y pruebas del alcance sintético descrito; no autoriza contratos nuevos, SSO, cambios backend, commit, PR ni despliegue.

- **EXISTING**: comprobado en código/contrato/pruebas presentes; no equivale a pruebas ejecutadas hoy ni aprobación operativa.
- **APPROVED**: decisiones de backend D-01–D-08 y revisión ficticia `HC-INV-APPROVAL-2026-11-02` ya documentadas, limitadas al escenario sintético; no aprobación nueva de UI.
- **PROPOSED**: decisiones nuevas pendientes de revisión.
- **BACKEND GAP**: capacidad no soportada por contratos actuales.
- **BLOCKED**: ejecución que requiere autorización o contrato previo. El diseño puede estar completo con implementación bloqueada.

Fuentes: `CONTEXT.md`, `AGENTS.md`, Memory Bank obligatorio e índice/conventions, Rules 01/07/09 siempre activas y 02/05/08 consideradas por contenido; `backend/app/inventory/{router,schemas,service,policies,access_audit,retention}.py`, `backend/app/inventory/README.md`, `backend/app/auth/{dependencies,roles,router}.py`; `uis/backoffice/{README.md,package.json,next.config.ts,tsconfig.json,contracts/openapi.json}`, `src/features/inventory/`, `src/components/`, `src/styles/tokens.css`, hooks y lib API/auth; `frontend/README.md`, `frontend/app/page.module.css`; SDD previos `memory-bank/specs/inventory-manager/{spec,plan,tasks}.md` y `memory-bank/specs/migrationBackoffice/nextjs-migration/spec.md`. No se editan fuentes discrepantes ni otros documentos protegidos. El usuario ha autorizado expresamente trasladar estos tres artefactos a `memory-bank/specs/inventory-manager-ui/`.

## Alcance de las tareas

Son tareas **PROPOSED** de finalización/caracterización sobre capacidades **EXISTING**, no checklist que declare pendiente todo lo ya construido. Estado inicial requerido: **TODO** para todas; bloqueo se registra en un campo independiente. El diseño inicial no ejecutó tareas. El estado actual de ejecución consta en cada ficha y en el cierre siguiente. APPROVED sólo invariantes backend D-01–D-08, roles y retención del escenario ficticio. BACKEND GAP-01–05 en spec§17; cambios de API/auth/auditoría/storage/infra/dependencias requieren autorización expresa adicional. La autorización de implementación sintética fue recibida con la petición de ejecutar este SDD; decisiones menores pueden revisarse con propuesta documentada.

## MVP y roadmap

MVP sintético: tareas001–009,011–014,016–017 y verificación018 para vistas MVP,019. Dashboard010 y agrupación015 son P1; completar018 con esas vistas para alcance global. Orden recomendado consultas→operaciones→reorden/auditoría→calidad; no crear base Next nueva ni rehacer funciones caracterizadas. Exportar/imprimir/lookup nominal/idempotencia fuerte/SSO no forman MVP y necesitan alcance/contrato separado. Las dependencias de018 siguientes describen cierre global; para corte MVP se documenta exclusión explícita P1 y no se declara todo alcance cerrado.

## Fase 0 — Preparación

### INV-UI-TASK-001 — Caracterizar implementación y aprobar alcance

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Contrastar las diez fichas con código y registrar aprobación de D-01–D-10 o exclusiones explícitas.
- **Requisitos EARS:** REQ-INV-UI-001, REQ-INV-UI-002, REQ-INV-UI-003, REQ-INV-UI-004, REQ-INV-UI-005, REQ-INV-UI-006, REQ-INV-UI-007, REQ-INV-UI-008, REQ-INV-UI-009, REQ-INV-UI-010, REQ-INV-UI-011, REQ-INV-UI-012, REQ-INV-UI-013, REQ-INV-UI-014, REQ-INV-UI-015, REQ-INV-UI-016, REQ-INV-UI-017, REQ-INV-UI-018, REQ-INV-UI-019, REQ-INV-UI-020, REQ-INV-UI-021, REQ-INV-UI-022, REQ-INV-UI-023, REQ-INV-UI-024, REQ-INV-UI-025, REQ-INV-UI-026, REQ-INV-UI-027, REQ-INV-UI-028, REQ-INV-UI-029, REQ-INV-UI-030, REQ-INV-UI-031, REQ-INV-UI-032, REQ-INV-UI-033, REQ-INV-UI-034, REQ-INV-UI-035, REQ-INV-UI-036, REQ-INV-UI-037, REQ-INV-UI-038, REQ-INV-UI-039, REQ-INV-UI-040, REQ-INV-UI-041, REQ-INV-UI-042, REQ-INV-UI-043, REQ-INV-UI-044, REQ-INV-UI-045, REQ-INV-UI-046, REQ-INV-UI-047, REQ-INV-UI-048, REQ-INV-UI-049, REQ-INV-UI-050, REQ-INV-UI-051, REQ-INV-UI-052, REQ-INV-UI-053, REQ-INV-UI-054.
- **Áreas/archivos:** memory-bank/specs/inventory-manager-ui; lectura src/features/inventory. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** Ninguna.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Revisión y ejecución sobre contratos actuales completadas; ampliaciones independientes pendientes.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Revisión contractual y documental, sin ejecutar mutaciones.
- **Criterio de aceptación:** Matriz completa y decisiones con responsable/estado; ninguna propuesta aprobada por inferencia.
- **Evidencia esperada:** Acta de revisión sintética sin secretos.

### INV-UI-TASK-002 — Resolver plan de selectors y brechas

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Revisar GAP-01–05; aprobar fallback UUID/página parcial y limitación incierta del MVP o encargar contrato aparte.
- **Requisitos EARS:** REQ-INV-UI-004, REQ-INV-UI-017, REQ-INV-UI-031, REQ-INV-UI-042, REQ-INV-UI-043.
- **Áreas/archivos:** contratos y diseño; ningún backend sin nueva autorización. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-001.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Revisión y ejecución sobre contratos actuales completadas; ampliaciones independientes pendientes.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Escenarios de scope vacío, país histórico y respuesta perdida sobre mocks.
- **Criterio de aceptación:** Fallback limitado aprobado o tareas dependientes marcadas BLOCKED; ningún endpoint inventado.
- **Evidencia esperada:** Registro decisiones y cobertura por contrato.

## Fase 1 — Base Next.js existente

### INV-UI-TASK-003 — Verificar base Next y tipos existentes

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Verificar runtime declarado y drift snapshot/router; conservar versiones/lockfiles y basePath.
- **Requisitos EARS:** REQ-INV-UI-047, REQ-INV-UI-053.
- **Áreas/archivos:** package.json/tsconfig/contracts sólo lectura; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-001.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** types:check y typecheck en entorno sintético existente aprobado.
- **Criterio de aceptación:** Sin rebootstrap ni dependencias nuevas; divergencias bloquean integración.
- **Evidencia esperada:** Salida comandos y matriz DTO revisada.

### INV-UI-TASK-004 — Caracterizar navegación y sesión

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Probar cinco roles, desconexión y401; adaptar sólo navegación Inventory si aprobado.
- **Requisitos EARS:** REQ-INV-UI-001, REQ-INV-UI-003, REQ-INV-UI-038, REQ-INV-UI-039, REQ-INV-UI-046, REQ-INV-UI-047.
- **Áreas/archivos:** src/components/app-shell; lib/auth; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-001, INV-UI-TASK-003.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Unitarias claims y cancelación; mocks401/403; roles previos sin Inventory.
- **Criterio de aceptación:** No tokens persistidos; datos viejos no aparecen; no ampliar permisos.
- **Evidencia esperada:** Tests sintéticos y revisión storage/logs.

## Fase 2 — Componentes comunes

### INV-UI-TASK-005 — Contexto clínica y lote

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Limitar IDs operator/manager a scope; regional filas autorizadas/UUID validado; lotes listados por código; invalidar payload al cambiar contexto.
- **Requisitos EARS:** REQ-INV-UI-002, REQ-INV-UI-003, REQ-INV-UI-004, REQ-INV-UI-015, REQ-INV-UI-016, REQ-INV-UI-019.
- **Áreas/archivos:** features/inventory/context-selector.tsx propuesto y detail/clinical-actions. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-002, INV-UI-TASK-004.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales. Selector nominal completo BLOCKED por GAP-01; fallback contrato actual depende de D-04.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Mocks fuera scope, lote ajeno, vacío; teclado selector.
- **Criterio de aceptación:** Contexto visible, ninguna escritura sin contexto; historia país pasado conserva acceso API.
- **Evidencia esperada:** Tests de selección/contexto y revisión visual.

### INV-UI-TASK-006 — Estados y formato fecha

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Añadir recepción local y zona/UTC; estados texto y errores asociados sin raw body.
- **Requisitos EARS:** REQ-INV-UI-018, REQ-INV-UI-034, REQ-INV-UI-036, REQ-INV-UI-037, REQ-INV-UI-039, REQ-INV-UI-040, REQ-INV-UI-044, REQ-INV-UI-045, REQ-INV-UI-048, REQ-INV-UI-052.
- **Áreas/archivos:** features/inventory; components/ui sólo si aprobado; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-003, INV-UI-TASK-004.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Mocks todos errores y null país; lector/keyboard; Intl zona inválida.
- **Criterio de aceptación:** Vacío/error/cero separados; UTC original retenido; sin fuga al cambiar sesión.
- **Evidencia esperada:** Pruebas y checklist de estados.

### INV-UI-TASK-007 — Confirmación contextual y resultado incierto

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Capturar intención segura, diálogo rico; bloquear doble envío; verificar/ack; cancelar preview al cambiar contexto.
- **Requisitos EARS:** REQ-INV-UI-002, REQ-INV-UI-021, REQ-INV-UI-041, REQ-INV-UI-042, REQ-INV-UI-043, REQ-INV-UI-049, REQ-INV-UI-051.
- **Áreas/archivos:** features/inventory/forms y preview; hooks sólo si autorizado. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-004, INV-UI-TASK-005, INV-UI-TASK-006.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales. Conciliación exacta BLOCKED por GAP-03; memoria de intención depende de D-09/Claire si tratamiento nuevo.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Doble clic/Enter, Escape, timeout/5xx/postcommit/JSON roto; navegación y desconexión.
- **Criterio de aceptación:** Un fetch por confirmación; incierto nunca éxito ni retry; límites entre pestañas/recarga documentados.
- **Evidencia esperada:** Mocks con contador POST y checklist foco.

## Fase 3 — Consultas

### INV-UI-TASK-008 — Endurecer catálogo y formulario artículo

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Conservar formularios; validar enteros/presentación y campos inmutables; baja reason confirmada; filtro local sólo si D-07 aprobado.
- **Requisitos EARS:** REQ-INV-UI-007, REQ-INV-UI-008, REQ-INV-UI-009, REQ-INV-UI-010, REQ-INV-UI-011, REQ-INV-UI-012, REQ-INV-UI-013, REQ-INV-UI-014, REQ-INV-UI-040.
- **Áreas/archivos:** features/inventory/items/detail/forms; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-003, INV-UI-TASK-006, INV-UI-TASK-007.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Duplicado409; extra422; inactivo; baja stock0/no0; sinpack factor1.
- **Criterio de aceptación:** DTO exacto; admin no consulta stock; error conserva campos seguros.
- **Evidencia esperada:** Tests payload y catálogo/edición/baja.

### INV-UI-TASK-009 — Detalle, lotes y stock

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Listar lotes; saldo total/lote; equivalencias API; mensaje no configuración; refresh de contexto.
- **Requisitos EARS:** REQ-INV-UI-008, REQ-INV-UI-015, REQ-INV-UI-016, REQ-INV-UI-017, REQ-INV-UI-018, REQ-INV-UI-030, REQ-INV-UI-051.
- **Áreas/archivos:** features/inventory/detail/stock; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-005, INV-UI-TASK-006, INV-UI-TASK-008.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Stock0/409/404/lote ajeno; below_reorder clínico con lote0; sesión distinta.
- **Criterio de aceptación:** Cero confirmado separado; no saldo editable; lotes sin caducidad/CRUD extra.
- **Evidencia esperada:** Tests de consulta y matriz APIs.

### INV-UI-TASK-010 — Dashboard parcial

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Crear resumen por página sólo con permiso; admin catálogo; etiquetas parcial/hora; tarjetas error independiente.
- **Requisitos EARS:** REQ-INV-UI-005, REQ-INV-UI-006, REQ-INV-UI-018, REQ-INV-UI-029, REQ-INV-UI-030.
- **Áreas/archivos:** features/inventory/dashboard.tsx y app/inventory/page.tsx propuestos. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-008, INV-UI-TASK-009.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Mocks listas vacías, fallo parcial y cantidades con unidades distintas.
- **Criterio de aceptación:** No sumas heterogéneas, globales ni métricas inventadas.
- **Evidencia esperada:** Captura sin token/datos reales y tests fórmula.

## Fase 4 — Operaciones

### INV-UI-TASK-011 — Preview y confirmación entradas/salidas

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Preview3×10; base factor1; confirmar contexto/cantidad/saldo orientativo; enviar DTO actual y invalidar.
- **Requisitos EARS:** REQ-INV-UI-019, REQ-INV-UI-020, REQ-INV-UI-021, REQ-INV-UI-022, REQ-INV-UI-041, REQ-INV-UI-042, REQ-INV-UI-051.
- **Áreas/archivos:** features/inventory/clinical-actions/operation-preview; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-007, INV-UI-TASK-009.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Cantidades0/negativa/fracción, sinpack, lote obligatorio, salida409, respuesta perdida.
- **Criterio de aceptación:** No POST inválido/doble; éxito sólo DTO; backend saldo final.
- **Evidencia esperada:** Tests simulados y E2E in/out.

### INV-UI-TASK-012 — Conteo físico con diferencia real

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Mostrar saldo lote/total y diferencia prevista; confirmar adjust base; mostrar previous/delta/resulting API.
- **Requisitos EARS:** REQ-INV-UI-023, REQ-INV-UI-024, REQ-INV-UI-041, REQ-INV-UI-042, REQ-INV-UI-049, REQ-INV-UI-051.
- **Áreas/archivos:** features/inventory/clinical-actions/operation-preview; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-011.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Conteo0/fracción/motivo blanco; saldo concurrente diferente al preview.
- **Criterio de aceptación:** Sin quantity en adjust; respuesta real reemplaza previsión; incierto bloquea.
- **Evidencia esperada:** Tests cálculo y E2E conteo.

### INV-UI-TASK-013 — Historial y selección de compensación

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Seleccionar original cargado con clínica; motivo/confirmación; mostrar enlace correction_of; conservar snapshots.
- **Requisitos EARS:** REQ-INV-UI-008, REQ-INV-UI-022, REQ-INV-UI-025, REQ-INV-UI-026, REQ-INV-UI-027, REQ-INV-UI-034, REQ-INV-UI-042, REQ-INV-UI-051.
- **Áreas/archivos:** features/inventory/detail/clinical-actions; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-007, INV-UI-TASK-009, INV-UI-TASK-012.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Compensación previa/negativa/decompensación409; cambio país; presentación histórica.
- **Criterio de aceptación:** Sin editar/borrar; sustitución separada; ningún contexto deducido de UUID libre.
- **Evidencia esperada:** Tests y E2E correction/history.

## Fase 5 — Reorden y auditoría

### INV-UI-TASK-014 — Umbrales y alertas

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Mostrar umbral de stock; configurar manager; alerta estricta y página corta con siguiente.
- **Requisitos EARS:** REQ-INV-UI-017, REQ-INV-UI-028, REQ-INV-UI-029, REQ-INV-UI-030, REQ-INV-UI-008, REQ-INV-UI-051.
- **Áreas/archivos:** features/inventory/stock/clinical-actions; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-009, INV-UI-TASK-011.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales. GET configuration independiente BACKEND GAP-02; usar stock aprobado en D-04.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** 19/20/21 conthreshold20, cero, sin configuración, pages cortas concurrentes.
- **Criterio de aceptación:** Igualdad no alerta; alerta no pedido; config no apertura.
- **Evidencia esperada:** Tests/E2E límites reorden.

### INV-UI-TASK-015 — Agrupación regional de página

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Agrupar clinic_id de página; prioridad déficit por fila si aprobado; título desde catálogo acotado; marcar parcial.
- **Requisitos EARS:** REQ-INV-UI-004, REQ-INV-UI-008, REQ-INV-UI-009, REQ-INV-UI-029, REQ-INV-UI-030, REQ-INV-UI-031, REQ-INV-UI-032.
- **Áreas/archivos:** features/inventory/stock; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-002, INV-UI-TASK-009, INV-UI-TASK-014.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales. Selector nominal completo BLOCKED por GAP-01; fallback contrato actual depende de D-04.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** US/UK scopes, vacío, clínica migrada para historia, empate y páginas divididas.
- **Criterio de aceptación:** No país inventado/total global; no escrituras supervisor; filtros sólo página.
- **Evidencia esperada:** Mocks y revisión regional.

### INV-UI-TASK-016 — Auditoría y denegaciones

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Mostrar DTO sólo redactado; fechas/país histórico; accepted/denied distintos; no antes/después reconstruido.
- **Requisitos EARS:** REQ-INV-UI-033, REQ-INV-UI-034, REQ-INV-UI-035, REQ-INV-UI-045, REQ-INV-UI-046.
- **Áreas/archivos:** features/inventory/audit; tests. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-006, INV-UI-TASK-009.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales. Revisión de tratamiento de auditoría D-09 antes de cambios; aprobación ficticia backend no ampliada.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** País histórico cambiado, null país propia/ajena,503 y redacciones.
- **Criterio de aceptación:** Auditor sólo ámbito backend; sin exportar/borrar; retención informativa.
- **Evidencia esperada:** Tests/API mocks y revisión Claire si nuevo tratamiento.

## Fase 6 — Calidad y entrega

### INV-UI-TASK-017 — Calidad técnica y regresión

- **Estado inicial:** TODO.
- **Estado actual:** DONE.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Ejecutar tipos/unitarias/build y E2E con fixture aislada; conservar incidentes/Management; decidir lint separado.
- **Requisitos EARS:** REQ-INV-UI-001, REQ-INV-UI-003, REQ-INV-UI-008, REQ-INV-UI-038, REQ-INV-UI-039, REQ-INV-UI-041, REQ-INV-UI-042, REQ-INV-UI-047, REQ-INV-UI-051, REQ-INV-UI-053, REQ-INV-UI-054.
- **Áreas/archivos:** uis/backoffice/tests y tooling existente. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-008, INV-UI-TASK-009, INV-UI-TASK-011, INV-UI-TASK-012, INV-UI-TASK-013, INV-UI-TASK-014, INV-UI-TASK-016.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Comandos plan§20; datos sintéticos; scripts legacy tests si cambios comunes.
- **Criterio de aceptación:** Checks obligatorios pasan sin skips injustificados; lint no fingido; sin cambios protected.
- **Evidencia esperada:** Salidas exactas exitstatus/entorno sin tokens.

### INV-UI-TASK-018 — Verificación visual y accesibilidad

- **Estado inicial:** TODO.
- **Estado actual:** PARTIAL.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Revisar vistas/estados a320/393/768/1350; axe y teclado/lector/zoom200/400%; tokens actuales.
- **Requisitos EARS:** REQ-INV-UI-036, REQ-INV-UI-037, REQ-INV-UI-040, REQ-INV-UI-048, REQ-INV-UI-049, REQ-INV-UI-050, REQ-INV-UI-052, REQ-INV-UI-054.
- **Áreas/archivos:** tests/e2e y evidencia temporal controlada. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-010, INV-UI-TASK-015, INV-UI-TASK-017.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Automatizadas y manuales spec§14; sin screenshots credenciales.
- **Criterio de aceptación:** WCAG objetivo validado por criterio, foco/tabla/reflow y sin scroll de página.
- **Evidencia esperada:** Checklist manual y resultados axe/viewport.

### INV-UI-TASK-019 — Revisión documental y entrega

- **Estado inicial:** TODO.
- **Estado actual:** BLOCKED.
- **Clasificación:** PROPOSED trabajo sobre EXISTING; APPROVED únicamente invariantes backend aplicables.
- **Descripción:** Trazar54 requisitos,10 vistas,16 endpoints; actualizar evidencias autorizadas; ejecutar validate-delivery read-only.
- **Requisitos EARS:** REQ-INV-UI-046, REQ-INV-UI-053, REQ-INV-UI-054.
- **Áreas/archivos:** SDD y README locales sólo con autorización de actualización. Las rutas son áreas previstas, no autorización para archivos protegidos.
- **Dependencias:** INV-UI-TASK-018.
- **Prerrequisitos/aprobaciones:** alcance sintético y decisiones D aplicables revisados; no credenciales/datos reales; permiso específico para cualquier archivo u operación protegida.
- **Bloqueos:** Autorización de implementación sintética recibida; sólo frontend y contratos actuales.
- **Pasos:** 1) revisar código y contratos afectados; 2) realizar el cambio acotado descrito o caracterizar si ya satisface criterio; 3) probar escenarios indicados; 4) revisar diff y registrar evidencia, sin commit automático.
- **Pruebas:** Diff exhaustivo, pruebas/revisión seguridad y criterios individuales.
- **Criterio de aceptación:** PASS sin bloqueos; ninguna aprobación nueva inventada; sin commit/PR/despliegue automático.
- **Evidencia esperada:** Informe de revisión y matriz trazabilidad final.

## Trabajo separado bloqueado por contrato o aprobación

No añadirlo ocultamente a las tareas anteriores. No rutas/endpoints nuevos autorizados.

| Unidad futura | Estado | Dependencia / aprobación | Aceptación antes de desbloquear |
|---|---|---|---|
| Lookup nominal y clínico histórico | TODO; BLOCKED; BACKEND GAP-01 | Contrato DTO/scope aprobado por Tecnología y Claire | Clínicas y país consultables por roles Inventory sin fuga y con historia separada de stock actual |
| Configuración GET/códigos409 | TODO; BLOCKED; BACKEND GAP-02 | Contrato autorizado y semántica de errores | Distinguir no configurado de conflicto sin parsear mensaje inestable |
| Idempotencia/operation_id | TODO; BLOCKED; BACKEND GAP-03 | Diseño transaccional/backend/seguridad y aprobación expresa | Reenvío misma intención no duplica; consulta correlacionada permite confirmar resultado; tests de postcommit timeout |
| Totales/búsqueda/exportación servidor | TODO; BLOCKED; BACKEND GAP-04 | Alcance fuera MVP, presupuesto y contratos | No representar página como global; semántica concurrente documentada |
| Presentaciones plurales/lote CRUD | TODO; BLOCKED; BACKEND GAP-05 | Nueva regla negocio y contrato | No alterar snapshots históricos ni saldo; alcance de unidades aprobado |
| SSO/sesión entre aplicaciones | TODO; BLOCKED | Seguridad/infra/auth protegidos; revisión Tecnología/Claire | Sin JWT en URL/storage; logout/expiry/scope definidos y probados |
| Lint adicional | TODO; BLOCKED si se exige | Aprobación de dependencia y configuración | Script real y compatible; no declarar pnpm lint ejecutable hoy |

Estas unidades son registros de brecha, no tareas de implementación de backend autorizadas ni sustituto de un SDD independiente.

## Matriz pantalla → tarea

| Pantalla | Tareas principales | Dependencias transversales |
|---|---|---|
| INV-UI-01 | 010 | 001–007,017–019 |
| INV-UI-02 | 008 | 001–007,017–019 |
| INV-UI-03 | 008 | 001–007,017–019 |
| INV-UI-04 | 009 | 001–008,017–019 |
| INV-UI-05 | 011 | 001–009,017–019 |
| INV-UI-06 | 012 | 001–009,011,017–019 |
| INV-UI-07 | 013 | 001–009,012,017–019 |
| INV-UI-08 | 014 | 001–009,011,017–019 |
| INV-UI-09 | 015 | 001–009,014,017–019 |
| INV-UI-10 | 016 | 001–009,017–019 |

## Verificación final de tareas

Cada requisito001–054 aparece en las tareas y tiene criterio en spec; cada pantalla aparece arriba y cada endpoint está en spec§10. Fase0 prepara aprobación, fase1 verifica base existente, no instala automáticamente. Todas comenzaron TODO; el estado actual indica lo ejecutado. Una tarea puede cerrarse mediante caracterización y prueba de la capacidad ya EXISTING, sin reimplementarla. Ningún TODO ni BLOCKED representa funcionalidad entregada en esta sesión.

## Cierre de ejecución — 2026-11-02

001–017 DONE: caracterización de capacidades existentes y mejoras frontend implementadas. Se aplican recomendaciones D-01–D-10 sólo dentro del alcance sintético existente: Next/backoffice, español, componentes actuales, UUID autorizado, página parcial, no-store y sin nuevas librerías de aplicación. D-09 no habilita SSO ni nuevos tratamientos: se conserva JWT sólo memoria, redacciones y retención vigentes; el aviso incierto contiene sólo contexto de operación sin motivo libre ni credenciales.

018 PARTIAL: E2E/axe y revisión visual actual disponibles; quedan revisión integral con lector de pantalla, zoom/reflow 200%/400% y contraste/foco de todos los estados. 019 BLOCKED para cierre integral por esa evidencia manual pendiente; se ha revisado diff, seguridad y trazabilidad, pero no se presenta como PASS completo. No hay aprobaciones ficticias nuevas.

GAP-01–05 siguen BACKEND GAP fuera del alcance: selector nominal/histórico completo, configuración GET/códigos, idempotencia/correlación, totales/filtros servidor y presentaciones plurales. Los fallbacks de UI están implementados; no se han creado contratos ni permisos nuevos. Evidencia y comandos: plan§21. No se modifican otros archivos Memory Bank, Rules, backend, configuración o despliegue.

## Propuesta de mejora para retomar

Por petición del desarrollador, la revisión manual integral pendiente de018 y el cierre dependiente de019 se registran en [proposals.md — accesibilidad manual de Inventory Manager UI](../../proposals.md#propuesta-completar-la-accesibilidad-manual-de-inventory-manager-ui). La implementación funcional para desarrollo sintético está terminada; esta propuesta no declara verificada la accesibilidad pendiente ni cambia PARTIAL/BLOCKED a PASS.
