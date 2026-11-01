# Lote5: contrato1.2.0 para ámbito técnico general

El desarrollador indicó «continua como recomiendas» después de la recomendación explícita de ampliar el contrato para los eventos técnicos sin clínica. Se aplica esa ampliación; no se interpretó como autorización para cambiar autenticación, auditoría, infraestructura o desplegar.

## Regla definitiva

jurisdiction es obligatoria. US/UK procede exclusivamente de una clínica/contexto validado en servidor. null significa ausencia genuina de clínica en un hecho técnico general. No usar null para esconder clínica inválida/inactiva, timeout, configuración incompleta o region desconocida; no usar IP, frontend, JWT inválido ni región de instalación como sustitutos.

| Tipo añadido | Ámbito general permitido; condiciones para futuro productor |
| --- | --- |
| authentication_succeeded | Verificación autenticada sin clínica. userId HMAC general; no equiparar cada verificación JWT con login SSO. Unidad/deduplicación del hecho queda para lote de productor. |
| authentication_failed | Credencial ausente/inválida: null y userId=null. Nunca leer identidad/región de JWT no verificado ni exportar credenciales. |
| authorization_denied | Actor ya verificado pero sin contexto clínico validado: null con HMAC general. Denegación con clínica autoritativa puede mantener US/UK; no saltar permisos para obtenerla. |
| api_request_completed | Ruta verdaderamente general: null; solicitudes clínicas conservan resolución regional y rechazo sin fallback. Este lote no añade hooks generales. |
| catalog_cache_observed | Métrica de caché compartida global: null, userId=null si no corresponde a actor. No duplicar en US/UK. Ventana del contador pendiente del productor. |
| service_health_checked | Estado del servicio compartido: null, userId=null. Fuente/frecuencia pendiente, sin crear sondeo externo. |
| data_integrity_checked | Chequeo global real: null, userId=null. No presentar una validación puntual como chequeo agregado inexistente. |
| telemetry_contract_rejected | Rechazo sin contexto verificado: null/userId=null. Nunca confiar en payload rechazado; canal diagnóstico acotado separado, sin recursión, pendiente. |
| telemetry_delivery_failed | Fallo general: null; fallo de lote regional conserva ámbito ya validado. Sin tokens/payload/URLs libres ni envío por la cola fallida; canal pendiente. |

Los cinco tipos browser previamente admitidos conservan null permitido. Total:14 tipos nullable;25 tipos exigen US/UK. audit_accessed y management_mutation_completed no se amplían: superficies globales aún requieren decisión propia, no se convierten en hechos técnicos generales por inferencia. Ningún tipo de inventario o agregado clínico pasa a null.

## Implementación

Fuente docs/telemetry/event-schemas.json y copias backend/app/telemetry/event-contract.json y uis/backoffice/operational-incidents/telemetry/event-contract.json idénticas. Se conservan39 tipos y demás campos/allowlists; schemaVersion pasa a1.2.0. Backend genera modelos y ContextResponse con VERSION vigente.

Se separan NULLABLE_EVENTS (14 modelos) y GENERAL_EVENTS (política browser fija de5). El frontend también conserva política explícita de5 productores, separada de nulabilidad del catálogo. Permitir null no autoriza al navegador a afirmar eventos de seguridad/servidor. Sink de servidor y hooks de productores no se amplían.

No aceptación silenciosa de1.1.0: frontend/API deben actualizarse coordinadamente; una versión antigua falla validación. Las pruebas antiguas sólo documentan evidencia histórica de1.1.0. No se reconstruye entorno local ni cambia .env/Compose. El token contextual no se modifica y no contiene schemaVersion; el cuerpo nuevo sí exige1.2.0. No se añade gracia ni migración automática de colas antiguas.

## Criterios de aceptación

1. Copias idénticas,39 tipos, versión1.2.0 y exactamente14 tipos nullable.
2. Nueve tipos añadidos aceptan null sin perder campos requeridos/rechazo de extras/fechas/NaN;25 tipos clínicos siguen rechazándolo.
3. Browser/API admiten sólo los cinco tipos previos; nueve tipos generales servidor siguen rechazados403 en ingreso browser y por validación del servicio frontend.
4. Contexto publica1.2.0; payload1.1.0 se rechaza, sin normalización silenciosa.
5. Productores regionales existentes y colas20/10 conservan comportamiento; no cambio de claves/auth/auditoría/infraestructura/datos reales.
6. Pruebas frontend/backend/paridad e integración PostgreSQL sintética pasan, diff revisado y validate-delivery.

## Estado de cobertura

No añade productores: once tipos con productor al menos parcial y28 sin productor. Desbloquea sus modelos generales, no su implementación. Próximo lote debe concretar autenticación/autorización o diagnósticos y obtener aprobación de sus archivos protegidos antes de instrumentarlos. Retención/residencia/transferencias reales y producción siguen pendientes de Cumplimiento.

## Evidencia de validación

198 pruebas backend PASS;5 integraciones omitidas sin DB por guard.68 pruebas frontend PASS.93 pruebas PostgreSQL16 aislado en tmpfs PASS, incluidas las5 integraciones regionales, auditoría, mutaciones y HTTP. Modelos39 verifican requeridos/extras/fechas/null; nuevas9 pruebas exigen403 en browser pese a modelo válido; test de versión antigua exige422. Copias idénticas verificadas por bytes:39 tipos,14 nullable, schemaVersion1.2.0. git diff --check PASS; staged vacío y entorno temporal detenido. No se suman recuentos solapados. Imagen de pruebas05ad0292ddcc; comandos detallados en informe temporal de revisión.
