# Inventario por clínica

Prototipo con datos sintéticos dentro de la API central existente (`backend/`).
Las decisiones de inventario fueron aprobadas en la sesión del 2026-11-02. Las
especificaciones antiguas siguen como borrador y apuntan a `services/central-api/`;
Memory Bank queda fuera del alcance autorizado y no se ha reescrito.
No incluye UI, compras, transferencias entre clínicas, caducidades, integración
EHR, registro real de inventario ni activación en producción.

## Comportamiento aprobado

- Existencias por artículo y clínica; los saldos de lotes son independientes.
  Las regiones son países, reutilizando Clinic → Jurisdiction.
- Artículo con título, código único y unidad base obligatorios. Código, unidad
  base y uso de lotes son inmutables; título y presentación son editables.
- Antes de registrar movimientos, configurar un punto de reorden entero positivo
  para cada artículo/clínica. Una combinación no configurada no tiene inventario
  habilitado y devuelve 409. Configurar crea una posición de saldo cero, nunca un
  saldo inicial independiente.
- Cantidades enteras en unidades base. Presentación opcional con nombre y
  equivalencia entera positiva: tres blísteres sintéticos de diez equivalen a
  treinta unidades. Cada movimiento conserva la equivalencia y unidad utilizadas.
- El saldo inicial se registra como entrada (`in`); una salida (`out`) resta la
  cantidad convertida. Un ajuste (`adjust`) requiere conteo físico no negativo
  `counted_quantity` en unidades base y motivo. Si hay lotes, se cuenta el lote elegido.
- Stock = `SUM(delta)`. No existe columna de stock, entrada de saldo en artículo,
  endpoint para fijarlo, caché de saldo ni proyección autoritativa independiente.
- Corrección mediante una compensación vinculada al original, con motivo. No se
  compensa una compensación ni el mismo original dos veces. El movimiento correcto
  de sustitución se registra como operación separada.
- Se rechaza saldo negativo por artículo/clínica/lote. Las escrituras bloquean la
  fila estable del artículo antes de consultar e insertar. Se requiere el aislamiento
  PostgreSQL predeterminado READ COMMITTED; no cambiarlo a REPEATABLE READ sin
  rediseñar bloqueo y snapshots. Esto también serializa escrituras del mismo
  artículo en clínicas distintas. No depende de bloquear movimientos existentes,
  por lo que protege también el historial vacío.
- Baja lógica sólo con saldo total cero, conservando historial. Artículos inactivos
  rechazan escrituras; sus consultas históricas siguen disponibles para clínicas
  activas autorizadas. No hay API de eliminación física ni de reactivación.
- Bajo reorden significa saldo total de clínica `< reorder_point`, incluido cero;
  la igualdad no lo activa. Consultar un lote mantiene el indicador de reorden de
  toda la clínica.
- Listados con `offset` (0) y `limit` (50, máximo 100). Historial cronológico con
  UUID como desempate. Reorden filtra antes de paginar y vuelve a comprobar los
  resultados; escrituras concurrentes pueden acortar una página. Las consultas
  regionales son acotadas, pero no representan un snapshot histórico único.

## Identidad y permisos

Autenticación Bearer existente. Los nuevos roles sólo tienen permisos de inventario:

| Rol | Acceso |
| --- | --- |
| `inventoryAdmin` | Consultar/administrar catálogo y lotes; baja con saldo cero. Sin movimientos ni lectura de stock clínico. |
| `inventoryOperator` | Consultar clínicas asignadas, registrar entradas/salidas y consultar historial. |
| `inventoryManager` | Lo anterior, más conteos, compensaciones y configuración de reorden. |
| `inventoryRegional` | Consultar stock, reorden e historial de países asignados. Sin escritura. |
| `inventoryAuditor` | Lectura regional y auditoría de mutaciones. Sin escritura. |

Los roles anteriores no reciben permisos de inventario. El endpoint de desarrollo
`POST /auth/tokens` admite arrays UUID opcionales `clinic_ids` y `jurisdiction_ids`,
incluidos en el JWT firmado. Operadores/responsables utilizan alcance por clínica;
región/auditoría, alcance por país. Sin alcance no se autorizan datos clínicos.
Los identificadores del cuerpo de una operación nunca conceden acceso. La emisión
sigue deshabilitada en staging/producción y no se crean actores reales.

La identidad continúa siendo autoemitida para desarrollo, sin un sistema de asignación
de accesos de producción. La aprobación simulada de Claire Whitfield
HC-INV-APPROVAL-2026-11-02 (02/11/2026) cubre roles, alcance por clínica/país,
auditoría y retención de 24 meses. Aprueba el escenario ficticio del proyecto,
no producción real ni cumplimiento legal.

## Rutas

Todas bajo `/inventory`; OpenAPI documenta DTOs y errores exactos.

| Operación | Ruta |
| --- | --- |
| Crear/listar artículos | `POST/GET /items` |
| Consultar/editar artículo | `GET/PATCH /items/{item_id}` |
| Baja con motivo | `POST /items/{item_id}/deactivation` |
| Configurar reorden obligatorio | `POST /items/{item_id}/clinics/{clinic_id}/configuration` |
| Crear/listar lotes | `POST/GET /items/{item_id}/lots` |
| Registrar movimiento | `POST /movements` |
| Compensar original con motivo | `POST /movements/{movement_id}/correction` |
| Consultar stock de clínica y lote opcional | `GET /items/{item_id}/stock?clinic_id=...` |
| Consultar historial | `GET /items/{item_id}/movements?clinic_id=...` |
| Consultar stock regional/clínico autorizado | `GET /stock` |
| Consultar necesidades de reorden autorizadas | `GET /reorder` |
| Consultar denegaciones autorizadas | `GET /access-denials` |
| Consultar auditoría de mutaciones | `GET /items/{item_id}/audit?clinic_id=...` |

Errores: 401 identidad ausente/inválida; 403 permisos/alcance; 404 referencia
inexistente; 409 estado, saldo o unicidad; 422 entradas inválidas; 503 si no se puede
persistir la evidencia obligatoria de una denegación. Campos desconocidos,
incluido stock, se rechazan. Las mutaciones confirman la transacción antes de responder
y revierten completamente ante fallos. Actor y fecha UTC proceden del servidor.
Triggers PostgreSQL impiden UPDATE/DELETE de movimientos y auditoría. Las consultas
ocultan snapshots y motivos históricos; los registros persistidos permanecen intactos.
Los textos deben excluir PHI, secretos e identificadores reales de pacientes.
El módulo no activa productores de telemetría de negocio.

## Migración y pruebas

Revisiones: `0010_inventory` crea tablas/triggers; `0011_inventory_audit_policy`
añade país histórico, resultados aceptados y registro inmutable de denegaciones.
Los registros antiguos sin país conservan valores nulos; no se deduce su país
original de la clínica actual. No se modifican
migraciones anteriores, configuración de entorno ni bases operativas locales.
Downgrade destruye historial: requiere autorización expresa y backup; sólo se
valida en una base sintética desechable.

Desde `backend/`, con conexión a PostgreSQL explícitamente aislada:

```sh
uv run --no-sync alembic upgrade head
uv run --no-sync pytest tests/test_inventory.py tests/test_inventory_audit_policy.py tests/test_auth.py -q
```

`INVENTORY_TEST_DATABASE_URL` debe apuntar a una base desechable cuyo nombre empiece
por `inventory_validation`; las pruebas rechazan otros nombres. `DATABASE_URL`
controla Alembic y las pruebas normales de la API. No apuntar a bases compartidas,
de producción o con datos reales. Las pruebas HTTP de inventario revierten una
transacción externa; las de concurrencia confirman registros sintéticos únicamente
en la base desechable explícita. Verifican salidas competidoras, historial vacío,
rechazos atómicos y protección append-only.

Para regresión, ejecutar la suite documentada del backend con catálogos y maestros
sintéticos. Algunas pruebas antiguas de telemetría requieren una base llamada
`telemetry_validation`, configuración sintética en modo US y un pool de pruebas
que no reutilice conexiones entre sus distintos event loops de asyncio. Son ajustes
del ejecutor de pruebas, no cambios del despliegue.

Validación del 2026-11-02: Python 3.12 con dependencias bloqueadas del backend;
21 pruebas de inventario/política superadas en PostgreSQL vacío y después 415 pruebas
superadas sin omisiones en la regresión sintética completa. Pasaron instalación
desde cero, actualización desde 0009, actualización repetida, downgrade/re-upgrade
desechable y comparación entre esquema/modelos de inventario. La regresión usó
un adaptador temporal NullPool que conserva codecs para las pruebas antiguas con
varios event loops; el pool de producción no se modificó. La comparación general
de Alembic identificó discrepancias previas de Compliance, índices y claves foráneas
ajenas a inventario, que no se corrigieron silenciosamente. Se utilizó Python y
PostgreSQL temporal ante el error de almacenamiento de Podman y el virtualenv roto;
no se migró ninguna base operativa.

## País histórico y auditoría de denegaciones

Los movimientos nuevos y las mutaciones de ámbito clínico conservan UUID y clave
técnica del país resuelto por el servidor. Las escrituras bloquean la clínica antes
del artículo para impedir una reclasificación concurrente durante la transacción.
Los eventos globales de catálogo no tienen destino geográfico y mantienen país/clínica
nulos. `result=accepted` identifica cambios confirmados. `resulting_quantity` es la
suma de saldo previo y delta sólo de salida, nunca un saldo almacenado independiente.

Historial y auditoría regionales filtran por país registrado, incluso tras cambiar
el país de una clínica. El stock actual utiliza el alcance actual de la clínica.
Eventos clínicos antiguos sin país se excluyen de la lectura regional hasta una
revisión histórica independiente aprobada; no se reclasifican ni eliminan silenciosamente.

Las denegaciones 403 de inventario con actor autenticado se persisten tras revertir
la operación intentada, en una nueva transacción antes de responder 403. Se conserva
únicamente actor, operación fija del servidor, código permiso/alcance, resultado y
UUIDs/país de referencias comprobadas en base de datos. Credenciales ausentes o
inválidas (401) no generan actores ficticios de auditoría. Referencias desconocidas
quedan nulas; no se almacenan cuerpos, cabeceras, tokens ni textos libres. Si falla
la transacción obligatoria de denegación, el acceso continúa denegado y responde 503.

`GET /access-denials` requiere permiso de auditoría de inventario y filtra por país
histórico. Las denegaciones sin país sólo son visibles para un auditor autorizado
que además sea el actor registrado; un auditor regional no recibe otras denegaciones
sin ámbito. El registro es append-only y aplica la misma retención de 24 meses.

## Retención y disposición controlada

Aprobación: HC-INV-APPROVAL-2026-11-02, revisión simulada de Claire Whitfield.
Movimientos, ajustes, correcciones, auditoría y denegaciones se conservan durante
24 meses naturales desde su fecha UTC. `retention_until` es una salida calculada;
un 29 de febrero vence el 28 de febrero si el año de destino no es bisiesto.
Las consultas mantienen restricciones por rol y ámbito. No se habilitan eliminación
automática, filtros de caducidad, workers de purga, bypass de triggers ni dependencias
de almacenamiento/archivo.

Procedimiento controlado al alcanzar el plazo:

1. Abrir una revisión autorizada de retención con referencia de aprobación,
   revisor/actor, fecha UTC, país, identificadores propuestos y vencimientos
   calculados. Excluir registros que aún no hayan alcanzado 24 meses.
2. Establecer dependencias entre movimientos, compensaciones y auditoría. Comparar
   saldos y reconstrucción histórica antes de cualquier disposición. Conservar todo
   movimiento que contribuya al stock o sea necesario para reconstruirlo.
3. Obtener autorización de Cumplimiento y Tecnología para el plan exacto,
   evidencia de backup/restauración y controles de acceso de cualquier archivo
   futuro. Si no se puede demostrar preservación, no eliminar y remitir el conflicto
   a Cumplimiento para una decisión registrada. No inventar prórrogas ni cambiar
   silenciosamente el periodo aprobado.
4. Ejecutar únicamente un mecanismo de disposición autorizado y validado por separado;
   conservar actor/fecha, identificadores revisados, decisión, resultado y comprobaciones
   de saldo/trazabilidad anteriores y posteriores en un registro controlado. Este
   módulo no evita la protección append-only existente.

La purga automática y cualquier mecanismo ejecutable de archivo/disposición siguen
aplazados para diseño y validación técnica, como permite expresamente la aprobación.
El prototipo calcula retención y aplica acceso; no ejecuta acciones destructivas por
vencimiento. Antes de utilizarlo con datos que alcancen el plazo, ese procedimiento
necesita un mecanismo ejecutable aprobado. Nunca sustituir movimientos fuente por
un saldo inicial almacenado independiente.

## Inventario sintético de demostración

Con migraciones y maestros de referencia aplicados, en desarrollo/test:

```bash
uv run python -m app.inventory.demo
```

Crea tres productos SYN-INV, un lote y seis saldos iniciales mediante movimientos en las clínicas dev-us-clinic-01/dev-uk-clinic-01. Segunda ejecución no reinicia saldos ni umbrales. Si un código reservado coincide con un artículo incompatible, revierte la transacción. No utiliza datos reales ni PHI.
