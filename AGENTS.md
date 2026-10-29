# Instrucciones para agentes de HealthCore

Estas instrucciones se aplican a cualquier agente que trabaje en este monorepo. No sustituyen `CONTEXT.md`, las Rules de `.agents/rules/` ni la evidencia del codigo y la configuracion.

## Identidad del proyecto

HealthCore es una empresa de atencion sanitaria ambulatoria que opera 12 clinicas: 9 en Estados Unidos y 3 en Reino Unido. HealthCore Digital es su unidad tecnologica interna, dirigida por el CTO James Osei. La organizacion utiliza dos ecosistemas EHR distintos que no tienen una integracion unificada. Sus operaciones estan sujetas a HIPAA en EE. UU. y UK GDPR en Reino Unido, y sus sistemas pueden tratar informacion sanitaria sensible, incluida PHI.

El briefing de `CONTEXT.md` describe necesidades empresariales; no demuestra que una funcionalidad este construida. Distingue siempre entre necesidad, propuesta pendiente y capacidad implementada. Para el estado tecnico utiliza primero el codigo y la configuracion presentes, contrastados con `memory-bank/current-state.md`.

## Inicio obligatorio de cada sesion

Antes de analizar o modificar el proyecto, consulta en este orden:

1. `CONTEXT.md`.
2. Este `AGENTS.md`.
3. `memory-bank/product-context.md`.
4. `memory-bank/technology-stack.md`.
5. `memory-bank/current-state.md`.

Despues:

- Consulta el indice `memory-bank/README.md` para encontrar otros documentos relevantes.
- Consulta `.agents/rules/README.md`, las Rules siempre activas y las Rules cuyos `globs` coincidan con el trabajo. Las Rules expresan su alcance mediante frontmatter `alwaysApply` y `globs`; respeta el mecanismo de carga que realmente admita el entorno.
- Revisa documentacion de arquitectura y convenciones, y los README de la raiz, de las carpetas afectadas y de la aplicacion correspondiente.
- Comprueba rama, `git status` y cambios staged, unstaged y no rastreados. Revisa cambios preexistentes antes de actuar y no los sobrescribas.

**Ningun agente puede modificar codigo sin haber consultado el contexto obligatorio y las Rules relevantes.** No dependas de recuerdos de otras conversaciones; vuelve a leer estas fuentes al iniciar cada sesion.

### Fuentes y discrepancias documentales

Para resolver discrepancias, aplica esta precedencia: `CONTEXT.md` para negocio y restricciones; codigo/configuracion para estado tecnico; Memory Bank para contexto persistente; README de la plantilla para convenciones de carpetas; Rules para instrucciones aplicables. No corrijas silenciosamente la fuente discrepante.

Se han observado estas afirmaciones historicas que no describen el estado actual: los README de plantilla indican que `CONTEXT.md` es un placeholder, que no hay `AGENTS.md` ni aplicaciones ejecutables; `memory-bank/technology-stack.md` afirma que aun no existen API, base de datos, UI ni autenticacion. Contrastalas con el `CONTEXT.md` real, `memory-bank/current-state.md` y el codigo existente. `current-state.md` describe el sistema como prototipo pre-MVP y no autorizado para piloto o produccion; no presentes esas capacidades como aprobadas para uso real.

## Flujo obligatorio antes de cualquier commit

Si un paso falla, resuelve el bloqueo antes de continuar. No crees commits automaticamente.

1. **STEP 1 — READ:** leer `CONTEXT.md`, los documentos obligatorios del Memory Bank, Rules aplicables y documentacion pertinente.
2. **STEP 2 — INSPECT:** examinar implementacion, dependencias, restricciones, estado de Git y cambios locales.
3. **STEP 3 — PLAN:** establecer alcance, archivos afectados, criterios de aceptacion y riesgos; pedir aclaracion si no se pueden determinar.
4. **STEP 4 — IMPLEMENT:** aplicar solo los cambios necesarios y autorizados, siguiendo las convenciones del monorepo.
5. **STEP 5 — VALIDATE:** ejecutar pruebas y comprobaciones pertinentes, revisar seguridad y verificar cada criterio de aceptacion.
6. **STEP 6 — REVIEW & COMMIT:** revisar el diff final y ejecutar `validate-delivery` cuando corresponda. Solo se puede crear un commit si las validaciones obligatorias pasan, no hay bloqueos ni cambios no autorizados y el desarrollador aprobo expresamente el commit.

La existencia de una skill no concede permiso para modificar archivos, hacer commit, push, crear o fusionar PR, ni desplegar.

## Archivos y operaciones protegidos

Solicita confirmacion expresa antes de modificar:

- `CONTEXT.md` y archivos empresariales originales.
- `memory-bank/**` y `.agents/rules/**`.
- `.env`, `.env.*`, `*.env`, credenciales, tokens, claves y otros secretos.
- Configuracion de CI/CD, incluyendo workflows y pipelines.
- Infraestructura, despliegue, seguridad y configuracion de entornos.
- Autenticacion, autorizacion, auditoria, conexiones y almacenamiento.
- Migraciones de base de datos existentes.
- Archivos fuera del alcance aprobado de la tarea.

Tambien requieren autorizacion expresa: eliminar archivos o directorios; cambiar contratos publicos de API; ejecutar operaciones destructivas o que alteren datos; introducir dependencias; crear commits; realizar push; crear o fusionar Pull Requests; desplegar servicios.

No ejecutes estas operaciones por inferencia ni por el hecho de que aparezcan en un plan. Para esta entrega, `memory-bank/**` y `.agents/rules/**` estan fuera de alcance y no deben modificarse.

## Seguridad y cumplimiento de HealthCore

- Trata toda informacion sanitaria personal como sensible. No expongas PHI ni identificadores de pacientes.
- No introduzcas datos reales de pacientes en prompts, fixtures, logs, ejemplos o pruebas sin autorizacion y controles adecuados. Usa datos sinteticos.
- Aplica minimo privilegio. No desactives autenticacion, autorizacion, auditoria ni controles de seguridad existentes.
- Manten separacion entre jurisdicciones cuando lo requieran los requisitos. HIPAA y UK GDPR no son equivalentes.
- No transfieras informacion sanitaria entre EE. UU. y Reino Unido sin una base legal y tecnica validada.
- No incorpores integraciones externas que procesen datos de pacientes sin aprobacion.
- Toda tarea que afecte privacidad, tratamiento de PHI, auditoria, retencion o transferencias internacionales requiere revision de Cumplimiento y Gobierno del Dato, liderada por Claire Whitfield.

Estas reglas de trabajo no certifican ni demuestran cumplimiento normativo. No declares cumplimiento solo por seguirlas.

## Limites de aplicaciones del monorepo

| Ruta | Responsabilidad y estado observado |
| --- | --- |
| `/uis` | Aplicaciones frontend. |
| `/uis/website` | Ubicacion prevista para la web corporativa publica; no existe actualmente en el arbol inspeccionado. |
| `/frontend` | Ubicacion alternativa existente del website: landing de HealthCore Digital en Next.js. Usar como referencia principal del sitio web mientras `/uis/website` no exista. Entrada en `app/page.js`; scripts `pnpm build` y `pnpm start`; URL local configurada `http://localhost:3000`. |
| `/uis/backoffice` | Aplicacion interna existente, con areas separadas de incidencias operativas y Management. |
| `/services` | APIs y servicios backend; existe `services/central-api/`. |

Reglas:

- No crear un segundo arbol de aplicaciones ni ubicar APIs fuera de `/services`.
- Reconocer `/frontend` como alternativa existente a `/uis/website`; consultar sus README y conservar su ubicacion durante la auditoria, sin duplicar ni trasladar la aplicacion.
- No mezclar componentes internos con la web publica sin justificacion aprobada.
- La web corporativa, si se autoriza en una tarea futura, debe reflejar la marca y el negocio de HealthCore. El backoffice debe seguir separado del sitio publico.
- La entrada de cada frontend vive en `/` dentro del directorio de esa aplicacion, no en la raiz del monorepo.
- Lee los README locales antes de crear archivos y conserva las convenciones tecnicas existentes.
- Este hito no autoriza crear o modificar aplicaciones.

## Rules y skills de agentes

- Identifica las Rules existentes en `.agents/rules/` y respeta su alcance, `alwaysApply` y `globs`.
- El indice marca como siempre activas `01-project-conventions.md`, `07-git-workflow.md` y `09-sensitive-data.md`; aplica las demas segun sus patrones. No dupliques su contenido aqui, no las desactives ni las edites sin autorizacion.
- Consulta `skills/README.md` y las skills disponibles antes de una tarea para la que exista una habilidad especifica. El repositorio mantiene skills reutilizables bajo `/skills/`; el arbol actual contiene `skills/_template/SKILL.md` como plantilla vacia.
- La skill `validate-delivery` esta documentada en `.agents/skills/validate-delivery/SKILL.md` como revision previa a la entrega. Abrela por su ruta cuando corresponda. No asumas activacion automatica: en el entorno inspeccionado no se expuso un mecanismo de descubrimiento o invocacion de skills, por lo que esa integracion no esta verificada.

## Definition of Done

Una tarea solo esta terminada cuando:

1. Satisface sus criterios de aceptacion con evidencia.
2. Respeta el contexto empresarial de HealthCore.
3. Respeta la arquitectura existente.
4. No infringe las Rules aplicables.
5. Supera las validaciones obligatorias.
6. No incorpora secretos ni informacion sanitaria indebida.
7. El diff ha sido revisado y contiene solo cambios autorizados.
8. Se documentan las limitaciones y riesgos pendientes.
9. La revision de entrega termina en un resultado valido; `BLOCKED` no equivale a terminado ni a `PASS`.
