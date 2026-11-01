# HealthCore Telemetry Design — 0.1

Fecha: 2026-11-01. Rama: `features/telemetryDesignPlan`. Hito exclusivamente documental. Todos los eventos son **PROPOSED como instrumentación**; el estado de cada componente se indica aparte. No hay decisiones de infraestructura ni tratamiento personal aprobadas. Prototipo sintético pre-MVP, sin autorización de piloto o producción.

# Traceability Matrix

Ubicación de evidencia backend: `backend/app/`, paquete de la API central trasladada desde `services/central-api/`; entrada `backend/app/main.py`. Todas las filas de API apuntan a módulos de la ubicación vigente. La ruta antigua solo se conserva como antecedente documental.

| Fuente/clase | EARS | Evento | JSON Schema | Tarea | Validación |
|---|---|---|---|---|---|
| MANDATORY_EXERCISE; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-001 | `inbound_order_completed` | `#/definitions/inbound_order_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_EXERCISE; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-002 | `outbound_order_completed` | `#/definitions/outbound_order_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_EXERCISE; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-003 | `inventory_validation_failed` | `#/definitions/inventory_validation_failed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_EXERCISE; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-004 | `stock_direct_update_rejected` | `#/definitions/stock_direct_update_rejected` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_EXERCISE; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-005 | `inventory_threshold_activated` | `#/definitions/inventory_threshold_activated` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-006 | `inventory_viewed` | `#/definitions/inventory_viewed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-007 | `product_selected` | `#/definitions/product_selected` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-008 | `order_started` | `#/definitions/order_started` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-009 | `order_abandoned` | `#/definitions/order_abandoned` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-010 | `inventory_adjustment_completed` | `#/definitions/inventory_adjustment_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-011 | `inventory_threshold_cleared` | `#/definitions/inventory_threshold_cleared` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; memory-bank/specs/inventory-manager/spec.md (RF-002–RF-007; INV-AC-006–019); prompt §§3,5.2 | TEL-FR-012 | `inventory_reconciliation_failed` | `#/definitions/inventory_reconciliation_failed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token | TEL-FR-013 | `authentication_failed` | `#/definitions/authentication_failed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/auth/dependencies.py:get_current_actor; backend/app/auth/security.py:decode_access_token | TEL-FR-014 | `authentication_succeeded` | `#/definitions/authentication_succeeded` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; uis/backoffice/operational-incidents/app.js; frontend/app/internal/incident-history/workspace.js | TEL-FR-015 | `session_started` | `#/definitions/session_started` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; frontend/app/internal/incident-history/workspace.js; README del backoffice | TEL-FR-016 | `session_ended` | `#/definitions/session_ended` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/auth/dependencies.py; backend/app/auth/policies.py | TEL-FR-017 | `authorization_denied` | `#/definitions/authorization_denied` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; uis/backoffice/operational-incidents/app.js; uis/backoffice/management/index.html; frontend/app/page.js | TEL-FR-018 | `navigation_viewed` | `#/definitions/navigation_viewed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; frontend/app/layout.js; audit/README.md (evidencia de auditoría, no RUM) | TEL-FR-019 | `frontend_timing_measured` | `#/definitions/frontend_timing_measured` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/main.py; routers montados | TEL-FR-020 | `api_request_completed` | `#/definitions/api_request_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/main.py; frontend/app/internal/incident-history/lazy-error-boundary.js | TEL-FR-021 | `application_error_observed` | `#/definitions/application_error_observed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/catalogs/cache.py:CatalogCache | TEL-FR-022 | `catalog_cache_observed` | `#/definitions/catalog_cache_observed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_BRIEFING; CONTEXT.md Tecnología; backend/app/main.py:health,status | TEL-FR-023 | `service_health_checked` | `#/definitions/service_health_checked` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_BRIEFING; CONTEXT.md Tecnología y Dirección | TEL-FR-024 | `alert_triggered` | `#/definitions/alert_triggered` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; CONTEXT.md Experiencia del Paciente y Acceso; no integración en código | TEL-FR-025 | `notification_delivery_completed` | `#/definitions/notification_delivery_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; CONTEXT.md Tecnología; data/pipelines/README.md | TEL-FR-026 | `job_run_completed` | `#/definitions/job_run_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/reference_data/validation.py; backend/app/management/router.py | TEL-FR-027 | `data_integrity_checked` | `#/definitions/data_integrity_checked` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/incidents/router.py; backend/app/incidents/history.py | TEL-FR-028 | `incident_created` | `#/definitions/incident_created` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/incidents/router.py; backend/app/incidents/history.py | TEL-FR-029 | `incident_transitioned` | `#/definitions/incident_transitioned` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/incidents/router.py; backend/app/incidents/history.py | TEL-FR-030 | `incident_assigned` | `#/definitions/incident_assigned` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; backend/app/management/router.py; backend/app/management/service.py | TEL-FR-031 | `management_mutation_completed` | `#/definitions/management_mutation_completed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_BRIEFING; CONTEXT.md Cumplimiento; backend/app/incidents/router.py:incident_audit; backend/app/management/router.py:list_management_audit_events | TEL-FR-032 | `audit_accessed` | `#/definitions/audit_accessed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; Diseño conceptual de este hito | TEL-FR-033 | `telemetry_contract_rejected` | `#/definitions/telemetry_contract_rejected` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; Diseño conceptual de este hito | TEL-FR-034 | `telemetry_delivery_failed` | `#/definitions/telemetry_delivery_failed` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_BRIEFING; CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados | TEL-FR-035 | `appointment_period_aggregated` | `#/definitions/appointment_period_aggregated` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_BRIEFING; CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados | TEL-FR-036 | `billing_period_aggregated` | `#/definitions/billing_period_aggregated` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| MANDATORY_BRIEFING; CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados | TEL-FR-037 | `experience_period_aggregated` | `#/definitions/experience_period_aggregated` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados | TEL-FR-038 | `workforce_period_aggregated` | `#/definitions/workforce_period_aggregated` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| IDENTIFIED_OPPORTUNITY; CONTEXT.md Experiencia del Paciente, Facturación, Operaciones, Personas y Dirección; sin módulos integrados | TEL-FR-039 | `clinical_workload_aggregated` | `#/definitions/clinical_workload_aggregated` | TASK-TEL-006,012,013 | V01–V05; V06 trigger/métrica |
| Prompt §§4–7; AGENTS.md | TEL-DATA-001 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-DATA-002 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-DATA-003 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-SEC-001 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-SEC-002 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-SEC-003 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-SEC-004 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-NFR-001 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-NFR-002 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-NFR-003 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-NFR-004 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |
| Prompt §§4–7; AGENTS.md | TEL-NFR-005 | Todos / control transversal | envelope y definiciones | TASK-TEL-005,008,013,014 | V03,V05,V06 |

Cobertura de briefing parcial por fuentes ausentes: agregados propuestos cubren KPIs pero no prometen integración ni tiempo real aprobado. No existe requisito obligatorio sin fila; controles sin evento propio aplican a todos.
