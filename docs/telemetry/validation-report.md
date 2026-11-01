# Validation Report — HealthCore Telemetry Design

## Task

Aplicar prompt «HealthCore Telemetry Design» mediante siete documentos de diseño, sin instrumentación. Fecha 2026-11-01. Change reference: `features/telemetryDesignPlan`; working tree inicial limpio, sin commit, push ni PR. Revisión manual de skill `.agents/skills/validate-delivery/SKILL.md`; no se afirma activación automática.

## Files inspected

Contexto: CONTEXT.md, AGENTS.md, memory-bank/product-context.md, technology-stack.md, current-state.md, README.md y conventions.md; índice Rules y reglas 01–09 (01,07,09 siempre activas, 05 por contenido de negocio; globs restantes no modificados). README raíz, docs, skills, services, backend, frontend y ambos backoffice. Baseline: backend/app/main.py; auth/router.py, security.py, dependencies.py, policies.py, roles.py; incidents/router.py, models.py, history.py; management/router.py, service.py, audit.py; reference_data/validation.py; catalogs/cache.py; error_contracts.py; frontend/app/api/incident-history/route.js y fuentes UI enumeradas en catálogo. Especificación inventario en memory-bank/specs/inventory-manager/spec.md; plan/tareas consultados como documentación de propuesta, no evidencia de código.

Contenido nuevo revisado: specs.md (51 requisitos: 39 FR+12 controles), plan.md, telemetry-plan.md (39 eventos), event-schemas.json (envelope+39 contratos), tasks.md (14 tareas), traceability-matrix.md (39 filas evento+12 controles), y este informe. `git diff` no incluye archivos nuevos; se inspeccionaron contenidos y consistencia mediante lector/validador, y revisión documental.

## Acceptance matrix

| ID | Resultado | Método y evidencia |
|---|---|---|
| AC-01 | PASS | Lecturas de contexto obligatorio y Rules registradas en sesión; matriz baseline de specs.md. |
| AC-02 | PASS | Necesidades empresariales diferenciadas de componentes existentes; ningún evento declarado emitido; inventario no atribuido al briefing. |
| AC-03 | PASS | Siete archivos solo docs/telemetry; continuidad del servicio trasladado verificada en backend/app/main.py, backend/Dockerfile, Compose e historial 8570d01; esta entrega no mueve aplicaciones. |
| AC-04 | PASS | Convenciones, flujo Git y no-PHI conservados; no cambio de instalación/comportamiento que exija README bilingüe de componente. |
| AC-05 | PASS | Scope explícitamente autorizado por prompt; ningún archivo protegido modificado. |
| AC-06 | PASS | Revisión de todos los contenidos, allowlists cerrados y ejemplos sintéticos; sin credenciales ni datos clínicos. Scanner de terceros NOT_RUN: no herramienta requerida por repositorio. |
| AC-07 | PASS | V01–V05 ejecutadas con stdlib, V08 draft-07 completo con jsonschema 4.25.1 y V06 revisión; no tests de aplicación necesarios para documentación sin modificación de apps. Límite de validador declarado abajo. |
| AC-08 | PASS | Cobertura: 39 eventos, 5 ejercicio, 6 briefing, 28 oportunidades, 11 categorías, 17 STREAM/22 BATCH, 5 excluidos; mapa inventario>=5 puntos, envelope, privacy, tareas y trazabilidad presentes. |
| AC-09 | PASS | Estado inicial limpio; final únicamente siete archivos autorizados no rastreados; sin staged/unstaged previos. |
| AC-10 | PASS | Fuentes y secciones identificadas, comandos/resultados registrados y comprobador reproducible en anexo. |
| G0 discovery | PASS | Código y discrepancias reales en matriz; incógnitas inventario clasificadas PLANNED. |
| G1 EARS | PASS | Cada FR tiene ID, fuente, trigger, prioridad, estado, aceptación, dependencia y validación; controles cubren sintaxis EARS en cinco variantes. |
| G2 design | PASS | Todos los eventos tienen hipótesis, decisión, propiedades, frecuencia por trigger, coste UNKNOWN y urgencia; políticas comunes de privacidad y fallos. |
| G3 tasks | PASS | 14 tareas documentales secuenciales con requisito, objetivo, evidencia, riesgo y aceptación. |
| G4 validation | PASS | V01–V08, trazabilidad y scope revisados; propuestas no convierten aprobaciones futuras en requisito de instrumentación satisfecha. |

## Validation commands

| Comando/check | Estado | Exit / resultado observado |
|---|---|---|
| `python3 /private/tmp/validate_telemetry.py` | PASS | 0; V01 parse JSON; V02 vocabulario draft-07 usado y referencias; V03 39 ejemplos aceptados y 924 casos rechazados; V04 unicidad, allowlist, EARS, nombres y cobertura; V05 justificaciones y propiedades cerradas. |
| `git diff --check` | PASS | 0; archivos nuevos revisados adicionalmente por lectura y comprobación whitespace. |
| `git status --short`, `git branch --show-current`, diffs staged/unstaged | PASS | Rama solicitada; inicial limpio, final solo docs/telemetry/. |
| `python3 -c 'import jsonschema'`, `/usr/bin/python3 -c 'import jsonschema'`, Python3.12 | NOT_RUN (validador externo) | ImportError (exit1); librería ausente. backend/.venv/bin/python apunta a intérprete inexistente (exit127). No se instaló dependencia. |
| `/private/tmp/healthcore-telemetry-validator/bin/python /private/tmp/complete_telemetry_validation.py` | PASS | 0; V08 Draft7Validator.check_schema y validación completa de 39 positivos/924 negativos; formatos con checker date-time explícito. |
| `python3 /private/tmp/validate_telemetry_delivery.py` (anexo extraído) | PASS | 0; mismos 39 positivos/924 negativos, leyendo catálogo Markdown sin datos temporales auxiliares. |
| V07 comprobación Git y contenido con stdlib | PASS | 0; siete rutas autorizadas exactas, rama correcta, sin cambios rastreados, whitespace y marcadores de credenciales revisados. |
| V06 revisión conceptual | PASS | Disparadores post-commit; invariante inventario pendiente; mínimo privilegio; semántica de nulos/periodos; stream/batch; riesgos y exclusiones revisados contra fuentes. |
| Builds/tests de aplicación | NOT_RUN | No aplicación modificada; evitar mutaciones de DB y builds ajenos al alcance. |

V02/V03 son comprobaciones stdlib del vocabulario utilizado. **V08 completa la validación externa draft-07**: `Draft7Validator.check_schema` valida el documento contra su metasesquema y `Draft7Validator` valida todos los ejemplos contra el contrato íntegro, con `FormatChecker` y comprobación explícita de fechas y zonas. Resultado: 39 aceptados / 924 rechazados. Las invariantes semánticas entre campos se mantienen como diseño futuro revisado, no como instrumentación implementada.

El desarrollador autorizó expresamente instalar `jsonschema` solo en un entorno temporal. Se creó `/private/tmp/healthcore-telemetry-validator` y se instaló `jsonschema==4.25.1` y sus dependencias allí. El primer intento de descarga falló por DNS restringido; el segundo, con aprobación de red y `--no-cache-dir`, terminó correctamente. No se cambiaron dependencias, lockfiles ni configuración del proyecto. Los fallos de disponibilidad anteriores son evidencia histórica, superada por V08.

## Revalidación de ubicación solicitada por el desarrollador

Se verificó `rg --files backend/app services`, lectura de `backend/app/main.py` y `backend/Dockerfile`, `rg -n 'backend|services/central-api|uvicorn|context:' docker-compose.yml README.md backend/README.md` y `git log -3 --oneline -- backend/app/main.py`. Resultado: mismo servicio central trasladado, paquete `backend/app/`, entrada `app.main:app`, context Compose `./backend`; commit de traslado `8570d01`. Se ajustaron baseline y razonamiento en specs/plan/telemetry-plan, tarea de discovery y trazabilidad. Los contratos JSON no requieren cambios: ningún contrato depende del nombre del directorio y las referencias de instrumentación ya usaban backend/app. Se volvió a ejecutar el comprobador del anexo: 39 casos válidos y 924 negativos, sin cambios en eventos o allowlists.

## Risks / corrective recommendations

R01–R09 en telemetry-plan.md permanecen abiertos para futura implementación. Claire debe revisar antes de procesar datos personales, aplicar retención/auditoría o transferencias. El hito no procesa datos personales ni modifica auditoría; esa aprobación no se simula. CTO/Operaciones deben aprobar ámbito, UOM, lotes, ajustes, roles y umbrales; fuentes de negocio ausentes y tiempo real todavía no resuelto. El comprobador stdlib es limitado; V08 aporta validación externa completa. Antes de implementar quedan fixtures semánticos y las aprobaciones de dominio/gobernanza, fuera del hito documental.

## Proposed Pull Request (no creado)

Título: `docs: telemetry design plan`

Descripción propuesta:

> Define contratos futuros de telemetría para inventario y superficies existentes de HealthCore, con 39 eventos (5 ejercicio, 6 briefing, 28 oportunidades), 11 categorías y entrega 17 STREAM/22 BATCH. Incluye SDD/EARS, catálogo accionable, esquemas cerrados, trazabilidad y privacidad US/UK. Propone outbox para hechos transaccionales y entrega acotada para UX, sin implementar ni seleccionar infraestructura.
>
> Validación: 39 ejemplos válidos y 924 negativos, referencias/nombres/allowlists/cobertura y scope documental verificados; validación completa draft-07 con jsonschema 4.25.1 en entorno temporal autorizado. Riesgos: inventario y fuentes empresariales aún pendientes, retención/seudonimización sujetas a Claire y KPIs diarios aún insuficientes para tiempo real. Sin cambios de aplicaciones, dependencias ni archivos protegidos.

## Cierre documental

La revisión final verificó siete entregables, 39 contratos y la continuidad de la API en `backend/app`. Se corrigió la referencia TASK-TEL-002 a TEL-FR-032 (`audit_accessed`). No se encontró en el material aportado otro enunciado académico con métricas adicionales; la cobertura se evalúa contra el prompt recibido y CONTEXT.md, diferenciando procedencia. El estado del ejercicio corresponde a diseño terminado; los riesgos de implementación permanecen explícitos.

## Final status

**PASS** para entrega del diseño documental, con alcance de validación definido y propuestas explícitas. No equivale a aprobación de instrumentación, cumplimiento, piloto ni producción. No hay validación obligatoria documental pendiente: V08 completa draft-07. El desarrollador autorizó expresamente crear commits mediante «genera los commits» el 2026-11-01. La revisión previa al commit terminó en PASS. Push y creación de PR no autorizados ni ejecutados.

## Anexo: comprobador reproducible (solo stdlib)

Guardar el siguiente código temporalmente fuera del repositorio y ejecutarlo desde su raíz con `python3`. No instala paquetes ni modifica aplicaciones. Lee contratos, reconstruye muestras desde catálogo y verifica el vocabulario usado.

```python
import json,re,math,copy,datetime
from pathlib import Path
D=Path('docs/telemetry'); s=json.loads((D/'event-schemas.json').read_text()); rows=[]
text=(D/'telemetry-plan.md').read_text()
for block in text.split('### `')[1:]:
 name=block.split('`',1)[0]
 if name not in s['definitions']: continue
 props=json.loads(re.search(r'Tipos específicos: `(.+?)`',block).group(1))
 source=re.search(r'Clase: (\w+)',block).group(1)
 cat=re.search(r'Categoría: (\w+)',block).group(1)
 req=re.search(r'Requisito: (TEL-FR-\d+)',block).group(1)
 rows.append(dict(name=name,props=props,source=source,cat=cat,req=req,hyp='Capturamos' in block,decision='lo que nos permite' in block,metric='Métrica:' in block,point='Origen/punto futuro:' in block))
# Standalone validator for the entire vocabulary used by this schema, no packages installed.
allowed={'$schema','title','description','definitions','oneOf','anyOf','allOf','$ref','type','required','properties','additionalProperties','pattern','format','enum','const','minimum','maximum'}
def check(x):
 assert isinstance(x,dict) and not set(x)-allowed
 if '$ref' in x: assert x['$ref'].startswith('#/definitions/') and x['$ref'].split('/')[-1] in s['definitions']
 if 'type' in x: assert x['type'] in ['object','string','number','integer','null']
 for k in ['oneOf','anyOf','allOf']:
  if k in x:
   assert isinstance(x[k],list) and x[k]
   for v in x[k]: check(v)
 for k in ['definitions','properties']:
  if k in x:
   assert isinstance(x[k],dict)
   for v in x[k].values(): check(v)
 if 'required' in x: assert isinstance(x['required'],list) and len(x['required'])==len(set(x['required'])) and all(isinstance(v,str) for v in x['required'])
 if 'additionalProperties' in x: assert isinstance(x['additionalProperties'],bool)
 if 'enum' in x: assert x['enum'] and len(x['enum'])==len(set(x['enum']))
 if 'pattern' in x: re.compile(x['pattern'])
 if 'format' in x: assert x['format']=='date-time'
 for k in ['minimum','maximum']:
  if k in x: assert isinstance(x[k],(int,float)) and not isinstance(x[k],bool)

def valid(sc,v):
 if '$ref' in sc: return valid(s['definitions'][sc['$ref'].split('/')[-1]],v)
 if 'allOf' in sc and not all(valid(x,v) for x in sc['allOf']):return False
 if 'anyOf' in sc and not any(valid(x,v) for x in sc['anyOf']):return False
 if 'oneOf' in sc and sum(valid(x,v) for x in sc['oneOf'])!=1:return False
 t=sc.get('type')
 if t=='object' and not isinstance(v,dict):return False
 if t=='string' and not isinstance(v,str):return False
 if t=='null' and v is not None:return False
 if t in ['integer','number'] and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or t=='integer' and int(v)!=v):return False
 if 'const' in sc and v!=sc['const']:return False
 if 'enum' in sc and v not in sc['enum']:return False
 if isinstance(v,dict):
  if not set(sc.get('required',[]))<=set(v):return False
  p=sc.get('properties',{})
  if sc.get('additionalProperties') is False and set(v)-set(p):return False
  if not all(valid(p[k],vv) for k,vv in v.items() if k in p):return False
 if isinstance(v,str):
  if 'pattern' in sc and not re.search(sc['pattern'],v):return False
  if sc.get('format')=='date-time':
   try:
    dt=datetime.datetime.fromisoformat(v.replace('Z','+00:00'))
    if dt.tzinfo is None:return False
   except ValueError:return False
 if isinstance(v,(int,float)):
  if 'minimum' in sc and v<sc['minimum']:return False
  if 'maximum' in sc and v>sc['maximum']:return False
 return True
check(s)
names=[r['name'] for r in rows];assert len(names)==len(set(names));assert set(names)==set(s['definitions'])-{'envelope'}
assert len(s['oneOf'])==len(names)
env=['eventId','timestamp','sessionId','userId','event_type','schemaVersion','requestId','properties']
assert s['definitions']['envelope']['required']==env
accepted=negative=0
for r in rows:
 sc=s['definitions'][r['name']]['allOf'][1]['properties']['properties']
 assert sc['additionalProperties'] is False and set(sc['required'])==set(sc['properties'])
 assert set(sc['properties'])=={'jurisdiction','environment'}|set(r['props'])
 assert r['name'] in (D/'telemetry-plan.md').read_text() and r['name'] in (D/'traceability-matrix.md').read_text()
 def sample(sc):
  if 'enum' in sc:return sc['enum'][0]
  if sc.get('format')=='date-time':return '2026-11-01T10:00:00Z'
  if sc.get('type')=='string':return 'ps_'+'0'*64
  return max(1,sc.get('minimum',0))
 v={'eventId':'00000000-0000-4000-8000-000000000001','timestamp':'2026-11-01T10:00:00Z','sessionId':None,'userId':None,'event_type':r['name'],'schemaVersion':'1.0.0','requestId':None,'properties':{k:sample(val) for k,val in sc['properties'].items()}}
 assert valid(s,v),r['name'];accepted+=1
 bad=[]
 a=copy.deepcopy(v);a['extra']='synthetic';bad.append(a)
 a=copy.deepcopy(v);a['properties']['extra']='synthetic';bad.append(a)
 for k in env:
  a=copy.deepcopy(v);del a[k];bad.append(a)
 for k in sc['required']:
  a=copy.deepcopy(v);del a['properties'][k];bad.append(a)
 for k in sc['properties']:
  a=copy.deepcopy(v);a['properties'][k]=[];bad.append(a)
 for ts in ['2026-11-01T10:00:00','2026-99-99T10:00:00Z']:
  a=copy.deepcopy(v);a['timestamp']=ts;bad.append(a)
 a=copy.deepcopy(v);a['schemaVersion']='2.0.0';bad.append(a)
 a=copy.deepcopy(v);a['event_type']='invalid_event';bad.append(a)
 for a in bad:assert not valid(s,a),r['name'];negative+=1
for r in rows:
 assert r['hyp'] and r['decision'] and r['metric'] and r['point'] and re.fullmatch('[a-z]+(?:_[a-z]+)+',r['name'])
 assert r['req'] in (D/'specs.md').read_text()
assert sum(r['source']=='MANDATORY_EXERCISE' for r in rows)==5
assert sum(r['source']=='IDENTIFIED_OPPORTUNITY' for r in rows)>=8
assert len(set(r['cat'] for r in rows if r['source']=='IDENTIFIED_OPPORTUNITY'))>=3
print(f'PASS V01 JSON parse; V02 used draft-07 vocabulary and references; V03 {accepted} valid / {negative} rejected synthetic cases; V04 names, requirements, allowlists, coverage; V05 closed properties and justified catalogue')
print('Third-party validation is executed separately by V08; this checker uses stdlib only.')
```

## Anexo V08: validación draft-07 completa

Ejecutar en el entorno temporal autorizado que disponga de jsonschema 4.25.1, desde la raíz del repositorio. Extrae el primer anexo y sustituye su validador de instancias por Draft7Validator. No requiere nuevas dependencias del proyecto.

```python
from pathlib import Path
from importlib.metadata import version
from jsonschema import Draft7Validator, FormatChecker
report=Path('docs/telemetry/validation-report.md').read_text()
code=report.split('```python\n')[1].split('```')[0]
start=code.index('def valid(sc,v):');end=code.index('check(s)\n',start)
# All instances are checked with real Draft7Validator, including formats.
replacement='''Draft7Validator.check_schema(s)
checker=FormatChecker()
@checker.checks('date-time', raises=(ValueError, TypeError))
def iso_date_time(value):
 if not isinstance(value,str): return True
 if not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?(Z|[+-]\\d{2}:\\d{2})",value): return False
 dt=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
 return dt.tzinfo is not None
validator=Draft7Validator(s, format_checker=checker)
def valid(sc,v):
 assert sc is s
 return validator.is_valid(v)
'''
code=code[:start]+replacement+code[end:]
code=code[:code.index("print('Third-party")]
exec(compile(code,'<draft7-full-validation>','exec'))
# Check that native format validation actually rejects invalid dates.
assert not Draft7Validator({'type':'string','format':'date-time'},format_checker=checker).is_valid('2026-99-99T10:00:00Z')
print(f'PASS V08: Draft7Validator.check_schema; jsonschema {version("jsonschema")}; 39 valid and 924 invalid instances checked against complete draft-07 schema with explicit date-time checker')
```

## Anexo V07: scope final antes de commit

```python
from pathlib import Path
import subprocess
D=Path('docs/telemetry')
expected={'specs.md','plan.md','tasks.md','telemetry-plan.md','event-schemas.json','traceability-matrix.md','validation-report.md'}
assert {p.name for p in D.iterdir()}==expected
paths=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines()
assert set(paths)=={str(D/p) for p in expected}
assert not subprocess.check_output(['git','diff','--name-only'],text=True).strip()
assert not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip()
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='features/telemetryDesignPlan'
for p in D.iterdir():
 text=p.read_text()
 assert all(line==line.rstrip() for line in text.splitlines()),p
print('PASS V07: exactly seven allowed documents, correct branch, no tracked changes; whitespace checked')
```
