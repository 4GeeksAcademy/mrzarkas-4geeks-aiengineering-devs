# OperationalIncident — Management: implementación

**Estado:** M1–M6 implementados de forma provisional; M0 pendiente de aprobación externa
**Referencia:** [`OperationalIncident-management.md`](./OperationalIncident-management.md)

## 1. Estructura propuesta

```text
app/
  management/
    router.py
    schemas.py
    service.py
    repository.py
    audit.py
    permissions.py
  reference_data/
  compliance/
```

`management` orquesta administración; no duplica modelos de catálogos,
maestros o Cumplimiento. Las reglas contextuales reutilizan
`app/auth/policies.py`.

## 2. Persistencia

Añadir a maestros y valores administrables:

```text
created_at, created_by, updated_at, updated_by
```

Crear `management_audit_event`:

```text
id, resource_type, resource_id, action,
actor_id, occurred_at, before_data, after_data,
reason, correlation_id
```

No guardar payloads clínicos ni descripciones completas de incidencias.

## 3. Servicio de dominio

Cada mutación seguirá el mismo flujo transaccional:

1. Autorizar capability y política de recurso.
2. Validar esquema, vigencia, claves y compatibilidad.
3. Aplicar cambio sin borrar históricos.
4. Crear evento de auditoría en la misma transacción.
5. Confirmar y devolver contrato de lectura.

El servicio rechazará cambiar `key` o eliminar físicamente registros usados.

## 4. Endpoints y capacidades

| Endpoint | Capability |
|---|---|
| `GET /management/catalogs` | `catalog:read` |
| mutaciones de catálogo | `catalog:manage` |
| `GET /management/reference-data/*` | `referenceData:read` |
| mutaciones de maestros | `referenceData:manage` |
| lectura ComplianceReview | `complianceReview:read` |
| mutaciones ComplianceReview | `complianceReview:manage` |
| auditoría de Management | `audit:read` |

Durante la implementación inicial, `admin` recibirá las capacidades de
escritura. Las demás asignaciones siguen pendientes de M0.

Implementado en M2: `catalog:read`, `referenceData:read`,
`referenceData:manage` y `complianceReview:manage`; las mutaciones de
`ComplianceReview` quedan para `admin` y Cumplimiento. La lectura de una
revisión está limitada igualmente a esos roles. No se ha introducido un claim
de jurisdicción en el JWT sin decisión de M0.

## 5. Contratos

Separar `Create`, `Update`, `ActivationRequest`, `Read`, `ListItem` y
`ListResponse`. Usar UUID para relaciones y `camelCase` al publicar contratos
TypeScript. Los `Update` excluyen `id` y `key`.

M3 publica `GET /management/catalogs`,
`GET /management/catalogs/{catalogName}/values` y las mutaciones de valor
propuestas. La API actual mantiene el estilo `snake_case` ya usado por los
contratos del servicio; la adaptación a tipos TypeScript es parte de M6.
Cada cambio incrementa la versión del catálogo y se escribe en
`management_audit_event` dentro de la misma transacción.

M4 publica `GET`, `POST`, `PATCH` y activación para los recursos bajo
`/management/reference-data/{resource}`, donde `resource` es `jurisdictions`,
`clinics`, `affected-systems` o `responsible-areas`; la cobertura de un sistema
se mantiene en `/management/affected-systems/{id}/jurisdictions`. No se permite
cambiar una clínica o retirar una cobertura si eso invalidaría una incidencia
histórica.

M5 publica `PATCH /compliance-reviews/{id}/status`. Lo pueden ejecutar
`admin` y Cumplimiento; cerrar o cancelar exige motivo. La creación, cada
cambio y toda asociación o desasociación con una incidencia quedan registrados
en `management_audit_event` dentro de la transacción correspondiente.

M6 publica la especificación viva en `/openapi.json` y `/docs`, tipos de
consumidor en `packages/shared/types/management.ts`, y
`GET /management/audit-events` protegido por `audit:read`. El backoffice
estático en `uis/backoffice/management/` muestra carga, vacío y error; no
persiste el JWT y delega toda autorización en la API.

## 6. Pruebas mínimas

- Rol autorizado y no autorizado por endpoint.
- `key` inmutable y sin borrado físico.
- Valor inactivo rechazado en nuevas incidencias.
- Auditoría creada en la misma transacción.
- Compatibilidad clínica/jurisdicción y sistema/jurisdicción.
- ComplianceReview de jurisdicción incorrecta rechazada.
- Fixtures sintéticos únicamente.
- Migración limpia, rollback viable y restauración.

## 7. Despliegue

1. Migración de auditoría y campos de autores.
2. Endpoints de sólo lectura.
3. Mutaciones `admin` con pruebas.
4. UI administrativa restringida.
5. Validación de capacidades por responsables.
6. Promoción controlada de datos aprobados.
