# PLAN — Implementación futura de serialización

**Estado:** diseño aprobado; implementación parcial iniciada. `TASK-SER-006` está validada con tests enfocados; las tareas restantes mantienen sus dependencias y aprobaciones.
Auditoría por endpoint y evidencia: [serialization-audit.md](../../../docs/serialization-audit.md). Requisitos: [spec.md](./spec.md). Tareas verificables: [tasks.md](./tasks.md).

## Principios de diseño

1. Mantener la API FastAPI observada en `backend/app`; no moverla a `services/` ni crear servicios nuevos. Contrastar la discrepancia con documentación previa, sin corregirla dentro de esta tarea.
2. Preservar primero contratos existentes: códigos, nombres/casing de campos, permisos, paginación, errores y semántica. No retirar una propiedad porque no aparezca en la UI local; clientes externos no están identificados.
3. Las respuestas ORM se proyectan mediante esquemas allowlist. `from_attributes=True` sólo habilita lectura de atributos definidos en Pydantic; no constituye una autorización ni un filtro de consulta.
4. No añadir esquemas por cada endpoint si comparten un contrato real. Introducir tipos `Create`, `Update`, `ListItem`, `Detail` o `Response` únicamente donde la auditoría muestre acoplamiento o diferencia semántica.
5. No tocar contenido persistido de auditoría, retención ni autorización sin revisión y decisión expresa de Cumplimiento/Gobierno del Dato. Datos y pruebas siguen siendo sintéticos.

## Arquitectura de contratos propuesta

| Dominio | Base existente | Diseño de entrada | Diseño de salida propuesto |
| --- | --- | --- | --- |
| Auth | `TokenRequest`, `TokenResponse` en `auth/router.py` | Mantener `TokenRequest`; definir política explícita para extras sin ampliar emisión de token | Mantener `TokenResponse` exactamente como access_token/token_type. No introducir registro, login de usuario o perfil inexistentes. |
| Catálogos de lectura | `CatalogResponse`, `CatalogValueResponse` | No hay escritura pública en router `catalogs` | Mantener proyección vigente; colección explícita de `CatalogValueResponse`. |
| Incidents | `IncidentCreate`, `IncidentUpdate`, `IncidentListItem`, `IncidentListResponse`, `IncidentResponse` | Esquemas Create/Update explícitos, campos server-managed no escribibles; política documentada de extras | Crear `IncidentDetailResponse` independiente de Create, o renombrar/conservar alias sólo si la transición de contrato es compatible. Mantener `IncidentListItem` para lista. Respuestas de transición/assignment preservan hoy el contrato de detalle. |
| Compliance | `ComplianceReviewCreate`, `ComplianceReviewStatusUpdate`, `ComplianceReviewRead` | Create y Update dedicados | `ComplianceReviewResponse` independiente de entrada, con lista fija jurisdiction_id/status/id/review_identifier/created_at/created_by hasta decisión de clasificación. |
| Management catálogo | `CatalogListItem`, `ManagedCatalogValueResponse`, listas paginadas | `CatalogValueCreate/Update`, `ActivationRequest` (ya dedicados) | Añadir `ManagedCatalogValueListItem` si existe diferencia aprobada; inicialmente mantener exactamente los campos actuales de la lista. Operaciones de escritura/detail mantienen `ManagedCatalogValueResponse`. |
| Management reference data | `ReferenceValueCreate/Update`, `ReferenceValueResponse` | Modelos actuales, `extra=forbid` | Añadir `ReferenceValueListItem` como contrato nominal; no quitar created/updated metadata hasta verificar consumidores externos y aprobación. |
| Auditoría | `AuditEventResponse`, `ManagementAuditEventResponse` | No aplica | Formalizar shape de snapshots con allowlist/redacción únicamente después de decisión de Compliance. Mantener permisos `audit:read` y payload actual durante la investigación; no volver a serializar modelos genéricos sin revisión. |
| Health | Sin schema | Sin body | Añadir respuesta Pydantic `HealthResponse` para status `ok`. |
| Status | Sin schema completo | Sin body | Modelos separados para resultado conectado y no disponible; declarar 503 alternativo en OpenAPI y probar el body real emitido por `JSONResponse`, manteniendo 200/503 y payloads actuales. |

## Estrategia FastAPI/Pydantic

- Declarar `response_model` para respuestas JSON normales, incluidas health/status. Para status 503, documentar modelo alternativo mediante `responses` y probar respuesta real porque `JSONResponse` no pasa por la validación del `response_model` principal.
- Mantener `response_model=list[T]` o contenedor tipado para colecciones, como ya ocurre en métricas e historiales. Preservar `items`/`total` y límites actuales de paginación.
- Usar `ConfigDict(from_attributes=True)` sólo en modelos que leen entidades ORM. No definir propiedades de relaciones en el schema por conveniencia; decidir explícitamente ID, flatten o objeto anidado por contrato.
- Evaluar `extra` en todos los modelos de entrada. La alternativa menos disruptiva es hacer explícito y probar el comportamiento actual `ignore`; cambiar a `forbid` requiere comprobar los clientes y aceptar el posible 422 nuevo. Campos conocidos no autorizados por el rol siguen rechazados por las políticas actuales.
- Conservar envelope de errores FastAPI y status actuales; declarar/documentar códigos alternativos relevantes sin cambiar autorización ni semántica.
- Mantener responses de escritura como allowlist; un `refresh()` ORM no autoriza que nuevos campos ORM aparezcan automáticamente.

## Relaciones, consultas y rendimiento

- Los modelos revisados no declaran relaciones ORM navegables; hoy prevalecen IDs de referencia. No hay evidencia de respuesta anidada ni N+1.
- `GET /incidents` limita la consulta con offset/limit (1–100) y responde `IncidentListItem`, pero hace `select(OperationalIncident)`. Medir si una proyección SQL explícita reduce columnas y latencia antes de proponerla.
- Management aplica paginación en catálogos, valores, referencias y auditoría. El límite es 100; no modificar paginación.
- Para EP-017 y EP-021, establecer primero la compatibilidad de propiedades. Usar proyección de lista diferente sólo con campos ratificados; si coincide con el contrato actual, el cambio puede ser sólo nominal y no producir reducción de payload.
- Medición comparable si se autoriza optimización: tamaño JSON bytes, SQL statements/columnas cargadas, consultas por request, carga de relaciones y latencia p50/p95 con misma fixture sintética, permisos, paginación y entorno. No anunciar porcentajes sin resultados guardados.

## Clasificación de campos

Esta clasificación orienta revisión; no sustituye autorización ni aprobación de Cumplimiento.

| Clase | Ejemplos observados | Regla de salida/escritura |
| --- | --- | --- |
| Público técnico | `GET /health` status y catálogo activo según permisos | Sólo valores deliberadamente publicables; los catálogos actuales requieren capability. |
| Autenticado | IDs, título/descripción de incidencia, estado, fechas y referencias | Sólo actor con capability/contexto existente; no ampliar acceso por serializar. Descripción debe ser operativa y no contener PHI. |
| Restringido por rol | ComplianceReview, Management, auditoría | Mantener `require_capability`, policies de área y autorización actual. El schema no reemplaza permisos. |
| Interno | actor IDs, created_by/updated_by, correlation_id | Confirmar necesidad y clasificación con propietario/consumidores antes de retirar; no confundir UUID con secreto. |
| Secreto/credencial | clave JWT, credenciales de DB, hashes/passwords; access token como bearer credential legítimo en EP-001 | Nunca exponer secretos internos. EP-001 sólo devuelve el token emitido que define el contrato de desarrollo; no registrar ni reenviar request en la respuesta. |
| Editable | Campos aceptados por Create/Update/Activation/status request | Deben figurar expresamente en input schema y respetar validación/política; extra ignorado o rechazado, pero explícito y probado. |
| Gestionado por servidor | id, actor, timestamps, status inicial, identifier, audit correlation | Excluir de escritura de clientes salvo campo explícitamente aprobado; establecer en servicio/contexto autenticado. |
| Snapshot de auditoría | `before_data`, `after_data`, `reason` | Tratamiento pendiente de Compliance. No asumir que diccionario JSON arbitrario es seguro ni alterar registros históricos hasta aprobación. |

## Compatibilidad

- Contratos/consumidores locales: ver mapa por endpoint en la auditoría. Los UIs consumen status, catálogos, referencias, cola/detalle/incidencias y auditoría Management. Tipos TS Management existen pero no se hallaron importaciones. Compliance y varias mutaciones no tienen consumidor frontend local identificado.
- Breaking candidates: retirar actor IDs/metadata de Review/Management; estrechar `IncidentResponse` o snapshots audit; acortar `ReferenceValueResponse` de lista; rechazar extras actualmente ignorados. No se aplican sin revisar OpenAPI/consumidores y aprobación explícita.
- Crear comparación OpenAPI fijada a versión de dependencia lockeada, revisar schemas request/response, códigos de éxito/error, `required`, nullability y ejemplos sintéticos. Comparar tipos compartidos y pruebas consumer-side disponibles.
- Cambios aditivos suelen ser compatibles, pero se debe revisar si la semántica de `extra=forbid`, un campo requerido, naming o status nuevo cambia clientes. No migrar códigos HTTP ni errores por uniformidad estética.

## Plan por endpoint ⚠️/❌

Los códigos EP remiten al inventario completo de la auditoría. `T-SER-*` identifica pruebas futuras, no existentes.

| Endpoint | Archivos / esquemas | Campos y relaciones | Motivo / riesgo y tratamiento | Test / EARS |
| --- | --- | --- | --- | --- |
| EP-003 POST `/compliance-reviews` | `backend/app/compliance/router.py`, `models.py`; separar `ComplianceReviewCreate` de `ComplianceReviewResponse` | Respuesta vigente jurisdiction_id/status/id/review_identifier/created_at/created_by; jurisdicción por UUID | Esquema de salida hereda entrada y actor UUID necesita clasificación. Preservar campos y 201. | shape de 201, entrada/output separados; T-SER-COMP; FR-005/006, SEC-003 |
| EP-004 GET `/compliance-reviews/{review_id}` | router y modelo Compliance; `ComplianceReviewResponse` | mismos campos; ninguna relación anidada | Evitar contrato de detalle acoplado a Create; conservar policy y 401/403/404 | claves/roles; T-SER-COMP, T-SER-ACCESS; FR-002, SEC-003 |
| EP-005 PATCH `/compliance-reviews/{review_id}/status` | router y schemas Compliance; Update + response | status, reason de entrada; response actual no devuelve reason | Esquema de salida derivado de Create; no cambiar 200/409/422 ni validación de motivo | shape + extras; T-SER-COMP, T-SER-INPUT; FR-005/006, SEC-005 |
| EP-006 POST `/incidents` | `incidents/router.py`, `schemas.py`, modelo `incidents/models.py`; Create y DetailResponse independientes | campos de `IncidentCreate` + IDs/actor/fechas generados por servidor; referencias por UUID, review opcional | `IncidentResponse` hereda Create; asegurar reporter del actor y no del cliente. PHI incidental en texto requiere política. | POST 201 allowlist y servidor; T-SER-INC, T-SER-SECRET; FR-005/006, SEC-001/003 |
| EP-009 GET `/incidents/{incident_id}` | incidents router/schemas; `IncidentDetailResponse` | detalle actual completo, IDs escalares | Acoplamiento a input y actor IDs; mantener permisos/404 y payload publicado hasta decisión. | detalle roles/claves; T-SER-INC, T-SER-ACCESS; FR-002/004, SEC-003 |
| EP-010 PATCH `/incidents/{incident_id}` | incidents router/schemas/history; `IncidentUpdate`, detail response | title/description/severity/responsible_area/compliance review; sin relaciones anidadas | Separar respuesta; formalizar extras; description se copia a auditoría. Compliance debe decidir salida de snapshot; no truncar evidencia sin aprobar. | extras conocida/desconocida, patch response, snapshot sintético; T-SER-INPUT, T-SER-AUDIT; FR-005/006, SEC-004/005 |
| EP-011 POST `/incidents/{incident_id}/transitions` | incidents router/schemas | status_value_id/reason de entrada; devuelve detalle | Mismo DetailResponse que GET tras mutación, sin cambiar workflow/códigos. | respuesta + status/error regresión; T-SER-INC; FR-006, COMP-001 |
| EP-012 POST `/incidents/{incident_id}/assignments` | incidents router/schemas/history | responsible_area_id/reason; devuelve detalle | Mismo DetailResponse; no exponer columnas nuevas ni cambiar permisos/historial. | respuesta + history regresión; T-SER-INC; FR-006, COMP-001 |
| EP-015 GET `/incidents/{incident_id}/audit` | incidents router/schemas/history | audit IDs/actor/action/time y snapshots JSON arbitrarios | Snapshot puede contener description; requiere decisión de Compliance y mapear datos autorizados. No cambiar persistencia/retención antes de aprobación. | claves/role + caso sintético sensible; T-SER-AUDIT; SEC-003/004 |
| EP-017 GET `/management/catalogs/{catalog_name}/values` | `management/router.py`, `management/schemas.py`; añadir ListItem sólo si aporta contrato | respuesta vigente completa ManagedCatalogValueResponse; sin nested relations | Modelo de detalle/recurso en colección. Preservar campos actuales mientras clientes desconocidos; reducir después de compat review. | contract compare + 0–100 paging; T-SER-LIST, T-SER-COMPAT; FR-003, COMP-001 |
| EP-021 GET `/management/reference-data/{resource}` | management router/schemas, reference models; `ReferenceValueListItem` | lista vigente incluye audit timestamps/actors y jurisdiction_id; referencias por ID | Más amplio que columnas de UI observadas, pero no basta para quitar campos. Control de capability permanece. | shape por resource + compatibilidad; T-SER-LIST, T-SER-COMPAT; FR-003/004, SEC-003 |
| EP-026 GET `/management/audit-events` | management router/schemas/audit model/service | campos ManagementAuditEvent y before/after JSON | Actor IDs/reason/JSON arbitrario; mapear claves conforme a revisión de Compliance, sin cambiar permisos. | allowlist/audit role; T-SER-AUDIT, T-SER-ACCESS; SEC-003/004, FR-002 |
| EP-027 GET `/health` | `backend/app/main.py`; añadir `HealthResponse` | status=`ok`, sin ORM/relaciones | No response_model, riesgo de contrato no publicado. | 200 shape/OpenAPI; T-SER-HEALTH; FR-001 |
| EP-028 GET `/status` | main.py; añadir contratos success/unavailable y response alternativo 503 | status y database; sin relaciones | 503 JSONResponse bypasses model principal; documentar esquema y validar resultado sin filtrar excepción SQL. Mantener 200/503. | 200/503 body + secreto error + OpenAPI; T-SER-HEALTH; FR-001, SEC-001, TEST-001 |

Los otros 14 handlers se clasifican ✅ con evidencia y pruebas actuales/propuestas en el inventario; no requieren cambio funcional si la revisión OpenAPI y tests confirma que no cambió su contrato.

## Gates de aprobación y riesgos

- Aprobación expresa del SPEC/PLAN/TASKS antes de cualquier implementación.
- Decisión de Claire Whitfield/Compliance y Gobierno del Dato sobre actor IDs y snapshots, por el posible contenido PHI y los registros auditables.
- Dependencias instalables desde lockfile o entorno de servicio disponible, DB de pruebas claramente sintética y aprobación antes de suite que modifica registros.
- Confirmación de consumers externos/contratos documentados antes de cambios de shape o política `extra`.
- Sin commits, dependencias, migraciones o cambios fuera de los cuatro documentos hasta nueva autorización.