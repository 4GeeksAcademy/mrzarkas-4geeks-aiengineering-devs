# Plan de implementación — gestor de incidencias

## Decisión y alcance

Este plan se ha preparado **antes de escribir código del gestor**. El primer alcance es registrar y seguir incidencias operativas de las 12 clínicas y de los sistemas que las soportan. No incluye historia clínica, automatización de decisiones médicas ni sustituir los EHR, la facturación o la agenda.

## Plan acordado de trabajo

1. Validar con James Osei, Claire Whitfield y los responsables de área el flujo, roles y catálogo de sistemas. Acordar estados, severidad, objetivos de respuesta y escalado.
2. Modelar OperationalIncident con identificador, clínica, jurisdicción (US/UK), sistema, área, descripción operativa, reportante, responsable, estado, marcas temporales y referencia a revisión de cumplimiento. Diseñar una bitácora inmutable.
3. Definir la política de datos: prohibir PHI en título/descripción, controles por rol, auditoría, retención y escalado hacia Cumplimiento.
4. Crear el módulo FastAPI: alta, consulta filtrable, asignación, transición validada, comentarios operativos y cierre; con validación, autorización, auditoría y pruebas.
5. Construir el backoffice en uis/: cola, alta, detalle con historial y asignación/cierre; mostrar sólo datos necesarios por rol.
6. Añadir observabilidad y notificaciones: alertas de salud futuras deduplicadas, aviso al responsable y métricas agregadas sin datos de pacientes.
7. Probar caída de EHR, problema de agenda, bloqueo de facturación y posible incumplimiento en ambos países; revisar permisos, auditoría y cierre.
8. Pilotar con pocas clínicas, medir detección/respuesta/resolución y extender a toda la red tras corregir el flujo.

## Criterios de salida

- Un usuario autorizado puede crear, asignar, actualizar y cerrar una incidencia sin añadir información clínica.
- Cada cambio registra actor, fecha, cambio y motivo.
- Se filtra por clínica, US/UK, sistema y estado acordado.
- Un posible impacto HIPAA o UK GDPR llega a Cumplimiento y queda auditado.
- Las pruebas cubren permisos, transiciones inválidas y aislamiento de datos.

