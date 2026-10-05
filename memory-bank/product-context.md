# Contexto de producto y negocio — HealthCore

## Empresa y operación

HealthCore es una red de atención ambulatoria fundada en 2011 en Austin, Texas. Opera 12 clínicas: 9 en Estados Unidos (Texas, Florida y Georgia) y 3 en Reino Unido (Londres y Mánchester). Ofrece atención primaria, especialistas, enfermedades crónicas y prevención; reúne unas 200 personas y factura alrededor de 28 millones de dólares al año.

HealthCore Digital moderniza una operación construida sobre sistemas aislados: los EHR de EE. UU. y Reino Unido no se comunican; EE. UU. usa facturación propia y citas telefónicas, mientras Reino Unido usa una hoja de cálculo de facturación y agendas manuales. No hay capa de datos, telemetría ni registro centralizado.

HIPAA en EE. UU. y UK GDPR en Reino Unido obligan a minimizar datos, controlar accesos y conservar trazabilidad. No son requisitos secundarios.

## Usuarios del backoffice

El backoffice no lo usan pacientes ni sirve para registrar una consulta clínica. Lo usan los equipos que sostienen la red:

- Tecnología, dirigido por James Osei, recibe y coordina los fallos.
- Operaciones Clínicas (Dr. Marcus Reid) reporta bloqueos que impiden operar en una clínica.
- Experiencia del Paciente y Acceso (Priya Nair) reporta problemas de reserva, recordatorios o reprogramación.
- Ciclo de Ingresos y Facturación (Tom Callahan) reporta bloqueos de reclamaciones, cobros o facturación privada/NHS.
- Cumplimiento y Gobierno del Dato (Claire Whitfield) evalúa posibles impactos sobre datos de pacientes, auditoría e HIPAA/UK GDPR.

La Dra. Sandra Okonkwo y los responsables de área necesitan visibilidad agregada, no información clínica de pacientes.

## Incidencia en HealthCore

Una **incidencia operativa** es una interrupción, degradación o comportamiento anómalo de un sistema o integración que afecta —o puede afectar— la capacidad de una clínica para atender pacientes, gestionar citas, facturar, demostrar cumplimiento o acceder de forma autorizada a datos.

Ejemplos: una clínica no puede usar su EHR, no se puede registrar una cita en el flujo telefónico de EE. UU. o en la agenda manual de Reino Unido, una reclamación estadounidense no avanza, o falta una pista de auditoría. Un posible acceso indebido o exposición de datos se escala a Cumplimiento. El ticket nunca debe contener historia clínica, notas ni datos innecesarios del paciente.

No es un diagnóstico, una nota clínica ni una reclamación: es el registro para restaurar un servicio y dejar traza de la respuesta.

## Vocabulario de dominio

Nombres propuestos en inglés: OperationalIncident, Clinic, Reporter, AffectedSystem, Jurisdiction, IncidentStatus y ComplianceReview.

- Jurisdiction: US y UK.
- Clinic: una de las 12 sedes (9 en EE. UU.; 3 en Reino Unido).
- AffectedSystem: EHR de EE. UU., EHR de Reino Unido, facturación de EE. UU., hoja de cálculo de facturación de Reino Unido, programación telefónica de EE. UU. o agenda manual de Reino Unido.
- Áreas: Operaciones Clínicas, Experiencia del Paciente y Acceso, Ciclo de Ingresos y Facturación, Cumplimiento y Gobierno del Dato, y Tecnología.

CONTEXT.md no fija estados, severidades ni SLA. Deben validarse con los responsables antes de ser valores de producción.

