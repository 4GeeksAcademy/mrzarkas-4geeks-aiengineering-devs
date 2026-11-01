# Borrador local de Pull Request

Estado: preparado, sin publicar. Head: `feature/caching-optimisation`; referencia actual `e3edee3`. La rama destino debe elegirse según la entrega del repositorio antes de publicar. No se ejecutó push ni se creó una PR remota.

## Título

Optimiza catálogos con TTL y difiere la cronología interna con next/dynamic

## Descripción para el revisor

Las lecturas repetidas de catálogo activo y valores Management consultaban todos los valores o página/count en cada petición. Se añaden cachés JSON por worker con TTL de 60/30 s, aisladas por actor/rol/área y página, con generación version+updated_at consultada en cada lectura y recheck antes de publicar. Las escrituras existentes invalidan mediante esa generación y la vigencia UTC se aplica en cada hit.

La vista interna Next.js `/internal/incident-history` carga Timeline tras consultar y EventDetails tras seleccionar. useMemo reutiliza la mezcla y ordenación de historiales con dependencias completas. La portada y el backoffice nativo se conservan. El proxy de historial es privado/no-store; la API sigue autorizando ambas lecturas.

## Validación

- Suite backend: 150 pruebas aprobadas; regresión contractual, TTL, invalidación, aislamiento, vigencia y fallos.
- Build Next.js y pruebas Node de cálculo/proxy aprobados.
- A/B secuencial: SELECT 2→1 y 3→1, bytes constantes y p95 inferior en tres rondas.
- HTTP concurrente: tres rondas de 200 peticiones por modo/ruta, concurrencia 10, p95 inferior; dos procesos ven alta/edición/desactivación en base temporal eliminada.
- React Profiler: 2000 eventos, tres rondas; 200→0 recálculos al seleccionar, p95 5,2–5,4→4,2–4,5 ms. Nueva consulta recalcula.
- Chrome: descargas bajo demanda, loading/error/reload, teclado y layout responsive revisados con fixture sintético; autorización API/proxy comprobada aparte.
- OpenAPI conserva las 28 operaciones backend; sin dependencias, migraciones ni cambios de autenticación/auditoría/infraestructura.

## Alcance y límites

Sólo desarrollo y evaluación con datos sintéticos. Sin frecuencia operacional real ni aprobación de privacidad/producción. Las escrituras externas deben avanzar la metadata; la caché no cubre las que la omitan. La nueva vista React es la alternativa mínima aprobada tras no encontrar un cálculo React costoso preexistente; no migra el backoffice. Los SDD históricos se preservan y el alcance revisado se traza en el informe.

## Documentación

- [CACHING_REPORT](CACHING_REPORT.md)
- [Matriz de evaluación](CACHING_DELIVERY.md)
- [Guía de demostración](CACHING_DEMO.md)

## Commits de implementación

- `82bfe92` — diseño SDD.
- `1d2260a` — caché backend y pruebas.
- `091c90d` — cronología React y herramientas de verificación.
- `e3edee3` — evidencia y revisión de entrega.
