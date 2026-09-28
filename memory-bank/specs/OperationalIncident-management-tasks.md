# OperationalIncident — Management: tareas atómicas

**Estado:** M1–M6 completados de forma provisional; M0 pendiente de aprobación externa
**Referencia:** [`OperationalIncident-management.md`](./OperationalIncident-management.md)

## M0 — Decisiones y seguridad

- [ ] Validar la matriz final de capacidades con Tecnología y Cumplimiento.
- [ ] Confirmar que `admin` es el único gestor inicial de configuración.
- [ ] Aprobar límites de texto y política no-PHI para descripciones administrativas.
- [ ] Definir retención y acceso a auditoría de Management.
- [ ] Confirmar el procedimiento de promoción de fixtures sintéticos a datos aprobados.

## M1 — Fundamentos de persistencia y auditoría

- [x] Añadir campos de auditoría a maestros: creación y última actualización.
- [x] Crear tabla genérica de eventos de Management.
- [x] Añadir índices por recurso, identificador y fecha de evento.
- [x] Crear migración reversible y comprobarla desde base limpia.
- [x] Crear fixtures sintéticos de `ComplianceReview` sólo para pruebas.

## M2 — Autorización y políticas

- [x] Añadir capacidades `catalog:read`, `referenceData:read`, `referenceData:manage` y `complianceReview:manage`.
- [x] Implementar políticas para operaciones de Management.
- [x] Aplicar `403` homogéneo a mutaciones no autorizadas.
- [x] Aplicar filtros de visibilidad a lecturas de `ComplianceReview`.
- [x] Probar cada rol contra cada capacidad relevante.

## M3 — Administración de catálogos

- [x] Implementar listado paginado de catálogos y valores.
- [x] Implementar alta de valor de catálogo.
- [x] Implementar edición de etiqueta, descripción, orden y vigencia.
- [x] Implementar activación y desactivación con motivo.
- [x] Impedir cambio de `key` e impedir borrado físico.
- [x] Auditar cada mutación.
- [x] Probar valores activos, inactivos, históricos y cambios semánticos.

## M4 — Administración de maestros

- [x] Implementar lectura paginada de jurisdicciones, clínicas, sistemas y áreas.
- [x] Implementar alta y edición de clínicas con jurisdicción válida.
- [x] Implementar alta y edición de sistemas.
- [x] Implementar asignación de cobertura sistema–jurisdicción.
- [x] Implementar alta y edición de áreas responsables.
- [x] Implementar activación/desactivación de cada maestro con motivo.
- [x] Auditar cada mutación y validar compatibilidades existentes.
- [x] Probar que no se invalidan incidencias históricas.

## M5 — ComplianceReview

- [x] Implementar cambio de estado autorizado.
- [x] Auditar creación, cambio de estado y asociación con incidencia.
- [x] Validar visibilidad por rol y jurisdicción.
- [x] Probar asociación válida e inválida por jurisdicción.

## M6 — API, UI y operación

- [x] Publicar contratos OpenAPI y tipos compartidos de Management.
- [x] Construir pantallas administrativas restringidas en backoffice.
- [x] Mostrar auditoría autorizada, carga, vacío y error.
- [x] Ejecutar pruebas HTTP, integración, migración y restauración.
- [x] Documentar operación, rollback y promoción de datos aprobados.

## Orden obligatorio

```text
M0 → M1 → M2 → M3/M4/M5 → M6
```

No se habilitará UI administrativa ni promoción de datos reales sin M0, M1 y
M2 completos. M2 está implementado con la matriz provisional: el alcance por
jurisdicción de `ComplianceReview` requerirá una decisión de M0 y un claim JWT
con fuente de verdad aprobada.
