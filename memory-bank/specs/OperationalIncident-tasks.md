# OperationalIncident — Tasks

**Proyecto:** Gestor de incidencias operativas de HealthCore  
**Especificación de referencia:** [`OperationalIncident-specs.md`](./OperationalIncident-specs.md)  
**Estado:** Fase inicial cerrada condicionada; Fase 1 en progreso  
**Fecha:** 2026-09-26

## Estado de fases

| Fase | Estado | Criterio de cierre |
|---|---|---|
| Fase inicial — configuración y decisiones | **Cerrada condicionada** | Validaciones formales diferidas; deben resolverse antes de producción |
| Fase 1 — PostgreSQL y modelo | **En progreso** | Migraciones, modelo y restricciones en preparación |
| Fase 2 — API FastAPI | Pendiente | Contratos, endpoints, permisos y pruebas validados |
| Fase 3 — Backoffice | Pendiente | Flujos de UI y consumo de API validados |
| Fase 4 — Pruebas y migrabilidad | Pendiente | Suite crítica y migraciones verificadas |
| Fase 5 — Piloto y operación | Pendiente | Piloto aprobado y criterios operativos cumplidos |

> La Fase inicial se cierra de forma condicionada para permitir avanzar con decisiones provisionales. Esto no equivale a aprobación funcional o normativa: las validaciones diferidas son controles obligatorios de salida antes de producción.

## 1. Propósito

Este documento desglosa el trabajo necesario para implementar `OperationalIncident` sin repetir la especificación funcional. Las tareas deben ejecutarse respetando:

- `CONTEXT.md` como fuente de contexto de negocio.
- FastAPI como API centralizada.
- PostgreSQL gestionado como persistencia.
- Pydantic para contratos y validación de API.
- `uv` para Python y `pnpm` para JavaScript/TypeScript.
- `packages/shared/` para contratos TypeScript compartidos cuando sean necesarios.
- HIPAA y UK GDPR como restricciones de minimización, autorización y trazabilidad.

## 2. Reglas de ejecución

1. No codificar etiquetas de catálogo directamente en la UI.
2. Persistir identificadores estables (`key` o identificador equivalente), no etiquetas visibles.
3. No eliminar físicamente valores de catálogo utilizados por incidencias históricas.
4. Cualquier cambio semántico de catálogo requiere migración y revisión de impacto.
5. Los cambios de estado y de área responsable deben generar historial inmutable.
6. Las marcas temporales y autores de auditoría deben generarse en servidor.
7. No registrar PHI ni payloads completos en logs.
8. No crear un microservicio independiente para este módulo.
9. No introducir dependencias nuevas sin verificar las convenciones del monorepo y justificar la decisión.

## 3. Backlog priorizado

### P0 — Bloqueantes de diseño y seguridad

- [x] Preparar la propuesta de formato de configuración para `entryChannel`, `incidentType`, `severity` e `incidentStatus`.
- [x] Preparar los identificadores estables y etiquetas provisionales iniciales.
- [~] Validar la propuesta de catálogos con Tecnología, las áreas funcionales y Cumplimiento. Diferido a control de salida; ver [`OperationalIncident-catalogs-decision.md`](./OperationalIncident-catalogs-decision.md).
- [~] Definir qué estados tienen `isOpen = true`. Propuesta disponible; validación diferida.
- [~] Definir la matriz de transiciones permitidas. Propuesta disponible; validación diferida.
- [~] Definir la matriz de permisos para crear, editar, asignar, cambiar estado, cerrar y administrar catálogos. Propuesta disponible; validación diferida.
- [~] Definir límites de título y descripción. Propuesta disponible; validación diferida.
- [~] Definir controles y respuesta ante posible PHI. Propuesta disponible; revisión de Cumplimiento diferida.
- [~] Definir política de auditoría, retención y acceso a historiales. Propuesta disponible; aprobación diferida.
- [~] Confirmar estrategia de secretos y conexión a PostgreSQL gestionado. Transferido a Fase 1.
- [~] Confirmar estrategia de migraciones y restauración en entornos no productivos. Transferido a Fase 1.

Documento de consolidación de esta fase: [`OperationalIncident-initial-decisions.md`](./OperationalIncident-initial-decisions.md). Sus decisiones son propuestas preparadas y no se consideran aprobadas hasta que exista evidencia de validación por los responsables.

`[~]` significa **diferido con propuesta preparada**. No equivale a completado y debe resolverse antes de producción.

### P1 — Fundación de datos

- [x] Preparar el diseño relacional inicial y los criterios de salida de Fase 1. Ver [`OperationalIncident-phase1-data-model.md`](./OperationalIncident-phase1-data-model.md).
- [x] Crear la migración inicial de catálogos.
- [x] Crear el seed provisional de los cuatro catálogos configurables.
- [ ] Crear los catálogos contextuales de `Clinic`, `AffectedSystem`, `Jurisdiction` y áreas responsables.
- [x] Crear la tabla lógica de `OperationalIncident`.
- [ ] Crear el historial de estados.
- [ ] Crear el historial de asignaciones.
- [ ] Crear la auditoría de cambios.
- [ ] Añadir claves foráneas, restricciones de nulabilidad y unicidad.
- [ ] Añadir índices para estado, severidad, área responsable y fechas.
- [x] Documentar rollback y compatibilidad de migraciones.

### P1 — API FastAPI

- [ ] Crear el módulo de `OperationalIncident` dentro de la API centralizada.
- [x] Crear modelos Pydantic de entrada, salida, filtros y paginación.
- [x] Implementar lectura de catálogos activos.
- [x] Implementar alta.
- [ ] Implementar edición con auditoría.
- [x] Implementar listado paginado.
- [x] Implementar consulta detallada.
- [ ] Implementar cambio de estado con validación de transición.
- [ ] Implementar asignación y reasignación.
- [ ] Implementar consulta de historial de estados.
- [ ] Implementar consulta de historial de responsables.
- [ ] Implementar asociación con `ComplianceReview`, cuando corresponda.
- [ ] Implementar resumen de incidencias abiertas por severidad.
- [ ] Implementar autorización en cada operación.
- [ ] Definir errores seguros y no revelar contenido sensible.

### P1 — Backoffice

- [ ] Crear la cola de incidencias.
- [ ] Cargar catálogos desde la API.
- [ ] Implementar filtros combinables por `IncidentStatus`, `severity` y área responsable.
- [ ] Implementar paginación, ordenación y limpieza de filtros.
- [ ] Crear formulario de registro.
- [ ] Crear formulario de edición.
- [ ] Crear ficha de detalle.
- [ ] Mostrar historial de estados y responsables.
- [ ] Mostrar el área responsable actual.
- [ ] Crear vista de incidencias abiertas agrupadas por severidad.
- [ ] Implementar estados de carga, vacío y error.
- [ ] Ocultar acciones no autorizadas.
- [ ] Evitar mostrar o enviar información clínica.

### P1 — Pruebas

- [ ] Probar contratos Pydantic válidos e inválidos.
- [ ] Probar valores activos e inactivos de catálogo.
- [ ] Probar cambio de etiqueta conservando el identificador estable.
- [ ] Probar transiciones válidas e inválidas.
- [ ] Probar asignaciones y reasignaciones.
- [ ] Probar autor y marca temporal generados en servidor.
- [ ] Probar auditoría e inmutabilidad funcional.
- [ ] Probar filtros individualmente y combinados.
- [ ] Probar la fórmula de incidencias abiertas por severidad.
- [ ] Probar permisos y aislamiento por rol/área.
- [ ] Probar ausencia de PHI en logs, errores y telemetría.
- [ ] Probar migraciones hacia delante y rollback cuando sea viable.
- [ ] Probar restauración de una copia en un entorno no productivo.

### P2 — Piloto y operación

- [ ] Preparar datos de prueba sin pacientes reales.
- [ ] Seleccionar clínicas y áreas piloto.
- [ ] Preparar guía de operación del backoffice.
- [ ] Definir métricas de registro, asignación y resolución.
- [ ] Revisar incidencias sin responsable.
- [ ] Revisar cambios de catálogo durante el piloto.
- [ ] Recoger observaciones de Tecnología y Cumplimiento.
- [ ] Corregir bloqueos antes de extender a las 12 clínicas.

## 4. Dependencias y orden recomendado

```text
P0 diseño y seguridad
  → P1 migraciones y catálogos
  → P1 API y autorización
  → P1 backoffice
  → P1 pruebas
  → P2 piloto
```

Las tareas de interfaz pueden comenzar con etiquetas provisionales siempre que consuman el catálogo desde la API y no incorporen etiquetas hardcodeadas.

## 5. Definición de terminado

Una tarea se considera terminada cuando:

- La implementación respeta `OperationalIncident-specs.md`.
- Existe prueba automatizada o evidencia verificable adecuada al tipo de tarea.
- Se han revisado permisos y datos sensibles cuando aplique.
- La migración es reproducible desde un entorno limpio.
- La documentación del módulo está actualizada.
- No se han introducido valores de catálogo rígidos en clientes.

La entrega del MVP se considera terminada cuando todas las tareas P0 y P1 están completadas, las pruebas críticas pasan y el piloto está preparado con datos no productivos.
