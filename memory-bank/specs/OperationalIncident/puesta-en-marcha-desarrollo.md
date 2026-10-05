# OperationalIncident — puesta en marcha de desarrollo

**Ámbito:** entorno local con Podman, PostgreSQL y autenticación temporal JWT.  
**No usar para:** staging, producción, datos reales ni usuarios reales.

## 1. Creación del entorno

### Requisitos

- Podman y Compose disponibles.
- Los puertos locales `8000` (API) y `5432` (PostgreSQL), o sus equivalentes,
  libres.

### Configuración local

Crear el fichero de entorno desde el ejemplo:

```sh
cp services/central-api/env.example services/central-api/.env
```

Mantener estos valores para desarrollo:

```env
APP_ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://healthcore:healthcore_dev_password@postgres:5432/healthcore
JWT_SECRET_KEY=<secreto-local-no-compartido>
```

`DATABASE_URL` usa el host `postgres` porque la API se conecta desde la red de
Compose. No subir `.env` al repositorio ni reutilizar el secreto fuera del
equipo local.

### Arranque, esquema y datos sintéticos

Desde la raíz del repositorio:

```sh
podman compose up -d --build api
podman compose exec -T api uv run alembic upgrade head
podman compose exec -T api uv run seed-catalogs
podman compose exec -T api uv run seed-reference-data
podman compose --profile test run --rm --build test
```

Comprobar disponibilidad:

```sh
curl http://localhost:8000/health
```

La respuesta esperada es `{"status":"ok"}`. La especificación OpenAPI está
en `http://localhost:8000/docs` y `http://localhost:8000/openapi.json`.

Los seeds son idempotentes y sólo cargan fixtures sintéticos US/UK. Nunca
cargar clínicas, empleados, pacientes o revisiones reales en este entorno.

## 2. Creación de TOKEN con ACTOR

### Qué representa un ACTOR

Un `ACTOR` es la identidad técnica que aparece como `sub` del JWT y como autor
en los eventos de auditoría. Para desarrollo puede ser un UUID sintético; no
corresponde a una persona real ni crea usuarios persistentes.

Roles disponibles:

- `admin`: acceso total técnico y administrativo.
- `technology`: operación técnica de incidencias.
- `compliance`: revisiones de Cumplimiento y auditoría autorizada.
- `direction`: listados resumidos y métricas.
- `responsibleArea`: acceso limitado a su propia `area_id`.

### Token de `admin`

Definir un ACTOR sintético y solicitar un token:

```sh
export ACTOR_ID=00000000-0000-0000-0000-00000000a001

curl -sS -X POST http://localhost:8000/auth/tokens \
  -H 'Content-Type: application/json' \
  -d "{\"actor_id\":\"${ACTOR_ID}\",\"role\":\"admin\"}"
```

La respuesta contiene `access_token`. Copiarlo temporalmente como variable de
sesión:

```sh
export TOKEN='<access_token devuelto por la API>'
curl -H "Authorization: Bearer ${TOKEN}" http://localhost:8000/management/catalogs
```

### Token de área responsable

Un actor con `responsibleArea` necesita además la UUID del maestro de área.
El fixture sintético de Tecnología usa
`00000000-0000-0000-0000-000000000201`:

```sh
export ACTOR_ID=00000000-0000-0000-0000-00000000a201
export AREA_ID=00000000-0000-0000-0000-000000000201

curl -sS -X POST http://localhost:8000/auth/tokens \
  -H 'Content-Type: application/json' \
  -d "{\"actor_id\":\"${ACTOR_ID}\",\"role\":\"responsibleArea\",\"area_id\":\"${AREA_ID}\"}"
```

El token caduca según `JWT_EXPIRES_MINUTES` (60 minutos por defecto). Generar
uno nuevo cuando caduque; no guardarlo en ficheros versionados, tickets o
capturas.

## 3. Seguridad: JWT sólo para desarrollo

`POST /auth/tokens` permite reclamar un `actor_id`, rol y `area_id` de forma
libre. Por ello es un mecanismo de autenticación **exclusivo de desarrollo y
pruebas**, no un sistema de identidad apto para entornos compartidos.

- Sólo está habilitado con `APP_ENVIRONMENT=development` o `test`.
- En `staging` y `production` responde `404`.
- La firma HS256 protege la integridad del token, pero no autentica a quien
  solicita inicialmente un token de desarrollo.
- La API aplica las capacidades y el alcance por área; el token no concede
  acceso fuera de las reglas del backend.

La sustitución futura está propuesta en
[`proposals.md`](../../proposals.md#propuesta-autenticación-jwt-propia-como-paso-intermedio-hacia-sso):
un proveedor corporativo SSO/OIDC emitirá o validará la identidad, y el emisor
local de tokens se retirará de cualquier entorno expuesto. Esa propuesta sigue
pendiente de validación por Tecnología y Cumplimiento.

## 4. Apagado y diagnóstico básico

```sh
podman compose ps
podman compose logs api
podman compose down
```

No ejecutar `down -v` salvo que se quiera eliminar explícitamente el volumen
local de PostgreSQL. Para rollback y restauración, consultar
[`management-operation.md`](../../../docs/management-operation.md).

