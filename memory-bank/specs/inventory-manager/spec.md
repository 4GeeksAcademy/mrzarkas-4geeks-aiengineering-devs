# HealthCore Inventory Manager — Specification

**Estado:** borrador para aprobación del CTO; no autoriza implementación.
**Versión:** 0.1
**Fecha:** 2026-10-18
**Ubicación funcional prevista:** módulo de Operaciones; el alcance físico del inventario sigue pendiente.

## 1. Propósito, contexto y alcance

Proporcionar al equipo de Operaciones una forma trazable de mantener artículos y registrar entradas, salidas y ajustes, consultar existencias calculadas y detectar artículos por debajo de su punto de reorden.

El briefing corporativo describe 12 clínicas en EE. UU. y Reino Unido, pero no indica cómo se distribuye o comparte el inventario. Por tanto, esta especificación no declara que el stock sea global, por clínica, por ubicación ni por lote: la dimensión que define una existencia debe aprobarse antes de implementar consultas y escrituras.

Alcance funcional mínimo: alta, consulta, edición y baja de artículos; registro de movimientos de entrada, salida y ajuste; cálculo de existencias; consulta de reorden; trazabilidad; y validación de referencias a artículos y, cuando corresponda, lotes. No se especifican categorías, valores de unidades, cantidades mínimas ni umbrales numéricos sin fuente aprobada.

Esta es una especificación de comportamiento y contratos. Las decisiones de almacenamiento, API HTTP y concurrencia se desarrollan en `plan.md` y no alteran los requisitos de negocio sin aprobación.

## 2. Actores y casos de uso

- **Operaciones:** administra artículos, registra movimientos y consulta existencias y reorden. Las personas/roles concretos autorizados y su alcance están pendientes de aprobación.
- **Consumidor autorizado de consulta:** solicita existencias calculadas y artículos bajo reorden; identidad y permisos sujetos a la matriz de autorización pendiente.
- **Sistema:** valida las referencias y reglas, registra movimientos y conserva la relación entre movimiento, artículo y lote cuando aplique.

Casos de uso: crear/consultar/editar/dar de baja un artículo; registrar entrada, salida o ajuste; consultar existencia disponible; consultar artículos bajo punto de reorden; consultar historial de movimientos.

## 3. Glosario y fuentes

| Término | Significado para esta especificación | Fuente / estado |
|---|---|---|
| Artículo | Elemento cuyo inventario gestiona Operaciones. Atributos y clasificación por aprobar. | Requisito explícito del prompt; no definido en `CONTEXT.md`. |
| Movimiento | Registro de entrada, salida o ajuste que afecta la existencia calculada. | Requisito explícito del prompt. |
| Existencia disponible / stock | Resultado calculado desde movimientos válidos, nunca un valor editable. | Invariante explícito del prompt. Alcance (global, clínica, ubicación, lote) pendiente. |
| Entrada | Movimiento que incrementa stock. | Requisito explícito del prompt. |
| Salida | Movimiento que reduce stock. | Requisito explícito del prompt. |
| Ajuste | Movimiento que altera stock; puede ser diferencia firmada o diferencia derivada de conteo físico. | Tipo requerido por el prompt; semántica pendiente de decisión. |
| Lote | Referencia potencial de un movimiento; debe existir si el dominio determina que es obligatorio. | Validación condicional explícita del prompt; uso, identidad y obligatoriedad pendientes. |
| Punto de reorden | Umbral configurado respecto del cual se identifica stock bajo reorden. | Requisito explícito del prompt; valor, dimensión y política de comparación requieren aprobación. |
| Unidad de medida (UOM) | Unidad en que se expresa cantidad del artículo/movimiento. | No está definida en `CONTEXT.md`; catálogo, precisión y conversiones pendientes. |
| Clínica / jurisdicción | Contexto de la red (12 clínicas; EE. UU. y Reino Unido). | `CONTEXT.md` y `memory-bank/product-context.md`; no prueban que sean dimensiones del stock. |

## 4. Requisitos funcionales y reglas de negocio

- **RF-001 — Gestión de artículos:** las personas autorizadas pueden dar de alta, consultar, editar y dar de baja artículos. Los campos obligatorios, la unicidad, la política de eliminación y el efecto de la baja en artículos con historial necesitan aprobación.
- **RF-002 — Registro de movimientos:** se pueden registrar movimientos tipados como entrada, salida o ajuste, asociados a un artículo existente y con cantidad y unidad validadas.
- **RF-003 — Stock derivado:** para cada ámbito de stock aprobado, la existencia se obtiene exclusivamente de la suma de cantidades firmadas de movimientos válidos:

  ```text
  stock(ámbito) = SUM(cantidad_firmada(movimiento válido del ámbito))
  ```

  La entrada aporta una cantidad positiva y la salida una cantidad negativa. La conversión de cantidad a signo y la semántica del ajuste deben aprobarse/documentarse; el ajuste siempre se materializa como movimiento.
- **RF-004 — Existencia no negativa:** no se acepta una salida ni un ajuste cuyo efecto deje la existencia aplicable por debajo de cero. Las operaciones concurrentes deben conservar la misma regla.
- **RF-005 — Referencias:** el artículo referenciado debe existir. Si para el artículo/tipo de movimiento/contexto se exige lote, el lote debe existir y corresponder al artículo y al ámbito aplicable. Esa condición no se puede convertir en obligatoria hasta aprobar la política de lotes.
- **RF-006 — Reorden:** se identifican y consultan los artículos cuyo stock calculado está por debajo de su punto de reorden configurado. Faltan por aprobar existencia/ausencia del umbral, comparación en igualdad, alcance y tratamiento de lotes o unidades incompatibles.
- **RF-007 — Trazabilidad:** cada movimiento aceptado conserva historial identificable que permite conocer el artículo, tipo, cantidad/unidad, referencias aplicables y momento del movimiento. No se pierde la trazabilidad por una edición o baja de artículo.
- **RF-008 — Acceso:** sólo actores autorizados pueden ejecutar altas, ediciones, bajas y movimientos; las reglas de lectura/escritura y alcance por rol requieren aprobación de Operaciones, Tecnología y Cumplimiento.

## 5. Contratos observables de operaciones

Los contratos son lógicos y agnósticos de transporte. El plan propone rutas HTTP compatibles con la API existente, sin que las rutas sean requisito de negocio.

| Operación | Entrada lógica | Resultado | Errores observables mínimos |
|---|---|---|---|
| Crear artículo | Datos de artículo definidos tras aprobar sus campos. | Artículo creado y referencia estable. | Datos inválidos; clave duplicada si se aprueba unicidad; actor no autorizado. |
| Consultar/listar artículos | Filtros/paginación que se definan. | Artículo(s) y metadatos no sensibles permitidos. | Actor no autorizado; filtros inválidos. |
| Editar artículo | Identificador y campos editables aprobados; no incluye stock. | Artículo actualizado. | Artículo inexistente; valores inválidos; conflicto o actor no autorizado. |
| Dar de baja artículo | Identificador y motivo si la política aprobada lo requiere. | Artículo deja de estar disponible según política aprobada; historial conservado. | Artículo inexistente; conflicto por movimientos/referencias; actor no autorizado. |
| Registrar movimiento | Tipo, artículo, cantidad positiva, unidad, lote si se exige y atributos aprobados del ámbito. Para ajuste, representación por aprobar. | Movimiento aceptado con identificador y datos trazables; la existencia resultante es calculable. | Referencia inexistente o incoherente; cantidad/unidad inválida; ámbito/lote requerido ausente; stock insuficiente; actor no autorizado. |
| Consultar existencia | Artículo y dimensión(es) del ámbito aprobadas. | Existencia derivada de movimientos válidos, con unidad y ámbito explícitos. | Referencia/ámbito inválido; actor no autorizado. |
| Consultar bajo reorden | Filtros/dimensión aprobados. | Artículos con stock calculado menor que el punto de reorden aplicable. | Actor no autorizado; política o unidad incompatible que impida comparar. |
| Consultar trazabilidad | Artículo y filtros de historial aprobados. | Movimientos históricos en orden definido, con datos trazables. | Artículo inexistente; actor no autorizado. |

Los códigos HTTP concretos y el modelo de errores se fijan en el plan; de forma consistente con la API actual se prevén 401/403 para identidad/autorización, 404 para recurso inexistente, 409 para conflicto de estado/stock y 422 para validación semántica, sujetos a revisión de contrato.

## 6. Invariantes

1. La única fuente de verdad del stock es el conjunto de movimientos válidos. El stock disponible no se edita directamente ni se acepta como dato de entrada.
2. No habrá campo de formulario para editar stock, endpoint para establecer/sobrescribir stock, operación CRUD que altere existencia sin movimiento, ni campo persistido de stock como fuente independiente de verdad.
3. Una proyección o caché sólo se permitiría si se justifica técnicamente, se deriva de movimientos, es reconciliable con ellos y no se puede modificar autónomamente. No forma parte de la primera solución propuesta.
4. Entrada incrementa; salida reduce; ajuste modifica stock mediante un movimiento. La semántica exacta del signo de ajuste queda por aprobar.
5. Ninguna operación aceptada puede dejar stock negativo en el ámbito aprobado, incluso bajo concurrencia.
6. Un movimiento referencia un artículo existente y, si la regla aprobada exige lote, un lote existente y coherente.
7. Cantidades y unidades son coherentes y comparables dentro del artículo/ámbito; las conversiones, si las hubiera, requieren regla aprobada.
8. Los movimientos aceptados mantienen trazabilidad histórica; la política de corrección de un movimiento y de baja de artículo no puede borrar el historial.

## 7. Comportamientos no deseados, validación y límites

- Rechazar un movimiento para un artículo inexistente; no crear referencias implícitamente.
- Rechazar lote inexistente o no relacionado cuando la política aprobada requiera lote.
- Rechazar cantidades no positivas en su representación de magnitud, cantidades no representables con la precisión aprobada, o unidades incompatibles. No aceptar un signo libre que contradiga el tipo de movimiento.
- Rechazar salida/ajuste con resultado negativo y manejar concurrencia de modo que dos solicitudes simultáneas no puedan aceptar en conjunto más stock del disponible.
- No permitir edición, sustitución o eliminación de movimientos sin una política explícita de corrección que preserve trazabilidad.
- No aceptar una actualización de artículo que pretenda cambiar stock.
- Si no existe un punto de reorden válido/configurado, el tratamiento (excluir, error u otro) es pendiente; no inventar un umbral.
- Si las dimensiones/unidades de dos existencias no coinciden, no sumarlas ni compararlas como si fueran equivalentes.

## 8. Criterios de aceptación EARS

Los criterios son observables y planificables para prueba. Donde una regla depende de una decisión pendiente, la prueba se concreta tras aprobarla; no implica que la propuesta esté aprobada.

| ID | Tipo | Criterio |
|---|---|---|
| INV-AC-001 | Evento | Cuando un actor autorizado da de alta un artículo con los campos y valores requeridos aprobados, el sistema debe crear y devolver una referencia estable al artículo. |
| INV-AC-002 | Evento | Cuando se consulta un artículo existente, el sistema debe devolver sus atributos autorizados sin exponer un campo editable de stock. |
| INV-AC-003 | Evento | Cuando un actor autorizado edita atributos permitidos de un artículo existente, el sistema debe persistirlos y devolver el artículo actualizado sin modificar movimientos ni stock. |
| INV-AC-004 | Evento | Cuando un actor autorizado da de baja un artículo, el sistema debe aplicar la política aprobada y conservar el historial de movimientos asociado. |
| INV-AC-005 | Comportamiento no deseado | Si una alta, edición o baja referencia un artículo inexistente o contiene datos inválidos, entonces el sistema debe rechazar la operación con un error observable y no producir una mutación parcial. |
| INV-AC-006 | Evento | Cuando se acepta una entrada de cantidad válida para un artículo existente, el sistema debe registrar un movimiento y aumentar la existencia calculada en esa cantidad, expresada en la unidad aprobada. |
| INV-AC-007 | Evento | Cuando se acepta una salida de cantidad válida para un artículo existente, el sistema debe registrar un movimiento y reducir la existencia calculada en esa cantidad, expresada en la unidad aprobada. |
| INV-AC-008 | Evento | Cuando se acepta un ajuste, el sistema debe registrar un movimiento de ajuste y calcular el cambio de stock mediante la semántica de ajuste aprobada, sin editar directamente la existencia. |
| INV-AC-009 | Ubicuo | El sistema debe calcular toda existencia consultada como suma de cantidades firmadas de movimientos válidos dentro del ámbito aprobado. |
| INV-AC-010 | Comportamiento no deseado | Si una solicitud intenta establecer stock, sobrescribir stock o cambiarlo mediante CRUD de artículo sin registrar un movimiento, entonces el sistema debe rechazarla y mantener intactas la existencia y los movimientos. |
| INV-AC-011 | Comportamiento no deseado | Si una salida o ajuste produce stock negativo en su ámbito, entonces el sistema debe rechazar el movimiento y no registrar una mutación parcial. |
| INV-AC-012 | Comportamiento no deseado | Si un movimiento referencia un artículo inexistente, entonces el sistema debe rechazarlo y no registrar movimiento ni alterar existencias. |
| INV-AC-013 | Comportamiento no deseado | Si la política aprobada exige lote para el movimiento y el lote falta, no existe, no corresponde al artículo o no corresponde al ámbito aplicable, entonces el sistema debe rechazar el movimiento sin mutación parcial. |
| INV-AC-014 | Comportamiento no deseado | Si la cantidad, unidad, precisión o referencia de un movimiento no cumple las reglas aprobadas, entonces el sistema debe rechazarlo y no cambiar la existencia. |
| INV-AC-015 | Comportamiento no deseado | Si operaciones concurrentes sobre la misma existencia podrían producir un resultado negativo, entonces el sistema debe aceptar como máximo las operaciones compatibles con el stock disponible y rechazar el resto. |
| INV-AC-016 | Ubicuo | El sistema debe conservar para cada movimiento aceptado los datos históricos necesarios para identificar su artículo, tipo, cantidad/unidad, referencias aplicables y momento, sin que una edición o baja posterior borre esa traza. |
| INV-AC-017 | Estado | Mientras un artículo tenga un punto de reorden configurado y una existencia calculable en unidad y ámbito comparables, el sistema debe identificarlo como bajo reorden cuando la existencia sea menor que el punto de reorden aprobado. |
| INV-AC-018 | Evento | Cuando un actor autorizado consulta existencias, el sistema debe devolver un valor calculado a partir de movimientos y señalar el ámbito y unidad a los que corresponde. |
| INV-AC-019 | Evento | Cuando un actor autorizado consulta artículos bajo reorden, el sistema debe devolver únicamente artículos cuya existencia calculada cumpla la regla de reorden aprobada. |
| INV-AC-020 | Comportamiento no deseado | Si un actor carece de autorización para una operación, entonces el sistema debe denegarla y no alterar artículos, movimientos ni existencias. |

## 9. Fuera de alcance

Sin apoyo documental o aprobación explícita no se incluyen compras, proveedores, facturación, transferencias entre sedes, caducidades, interfaz nueva/backoffice, integración con EHR, pronóstico automático, reservas de stock ni reglas regulatorias específicas. Esta especificación no establece ni presupone que se almacenen datos de pacientes.

## 10. Supuestos, dependencias y decisiones pendientes

### Evidencia localizada

- `CONTEXT.md`: empresa de 12 clínicas (9 EE. UU., 3 Reino Unido), estructura de Operaciones y obligaciones generales HIPAA/UK GDPR. No define un inventario ni sus reglas.
- `memory-bank/product-context.md`: describe el negocio y las restricciones de datos, sin categorías, lotes, unidades ni stock.
- `memory-bank/technology-stack.md`, `memory-bank/conventions.md`, `.agents/rules/02-repository-structure.md` y `.agents/rules/03-backend-python.md`: API FastAPI centralizada, módulos en `services/`, datos compartidos en PostgreSQL/SQLAlchemy/Alembic según código existente.
- Inspección del código: `services/central-api/app/` contiene auth, catálogos, incidencias, management y reference_data; no se encontró módulo de inventario ni modelos/endpoints relacionados. `services/central-api/alembic/versions/` contiene revisiones 0001–0009, ajenas a inventario; sus tests actuales prueban otros dominios.
- `memory-bank/technology-stack.md` tiene una afirmación histórica de que todavía no existían API/base de datos/autenticación que contradice `memory-bank/current-state.md` y el código/migraciones verificados. Para decisiones técnicas se toma el código vigente y `current-state.md`; la discrepancia no autoriza copiar funcionalidades del dominio de incidencias como reglas de inventario.

### Decisiones que debe aprobar Operaciones/CTO antes de implementar

1. **Ámbito del stock:** global, por clínica, ubicación, por lote, o combinación; definir identificadores y si se admite stock consolidado.
2. **Catálogo de artículos:** campos requeridos/editables, clave única, categorías si existen, ciclo de vida y significado de “baja”; eliminación física o lógica y reglas al existir movimientos.
3. **Unidades y cantidades:** catálogo permitido, unidad base por artículo, escala/precisión, cantidades fraccionarias, conversiones y validación de coherencia.
4. **Ajustes:** semántica de diferencia positiva/negativa frente a conteo físico final; formato de entrada y cálculo derivado si aplica.
5. **Lotes:** si existen; cuándo son obligatorios; si un lote pertenece a artículo y clínica/ubicación; política de identificación y estado. Caducidades quedan fuera salvo cambio aprobado.
6. **Reorden:** punto requerido u opcional; valor y unidad; ámbito al que aplica; comparación al igualar el umbral; política de valores no configurados y reglas para agregación por lote.
7. **Stock negativo:** el requisito exige rechazar salidas/ajustes que lo causen; aprobar precisión numérica y significado de cero/stock inicial (el saldo inicial debe registrarse como movimiento, nunca como campo).
8. **Corrección e historial:** si un movimiento puede editarse/cancelarse y qué operación trazable lo corrige. No se debe permitir borrado silencioso.
9. **Autorización y auditoría:** roles/capacidades de inventario, alcance por clínica/país, actores autorizados, necesidad de motivo y datos auditables. La matriz existente corresponde a incidencias/management y no se debe trasladar sin aprobación.
10. **Errores y lecturas:** filtros, paginación, orden, exposición de historial y política de acceso/visibilidad.
11. **Aprobación de privacidad/operación:** confirmar campos que no deben contener PHI y condiciones de desarrollo, prueba y promoción de datos sintéticos, según reglas vigentes del repositorio.

Hasta resolver estas decisiones, el spec no fija categorías, unidades, reglas concretas de lote, punto de reorden numérico, dimensión de stock, campos de artículo, matriz de roles ni semántica de ajuste.
