# Proyecto HealthCore

## Elección del proyecto

He elegido **HealthCore** porque considero que representa uno de los casos con mayor aplicación práctica y potencial de impacto.

La compañía refleja problemas habituales en empresas que han crecido rápidamente: **sistemas y datos fragmentados, procesos manuales, falta de automatización, dificultades para obtener una visión global del negocio y fuertes requisitos regulatorios**. En este caso, además, hablamos del sector sanitario, donde cualquier solución debe prestar especial atención a la seguridad, privacidad y trazabilidad de los datos.

Esto permite plantear un proyecto en el que la IA no sea únicamente un asistente conversacional, sino una herramienta integrada en diferentes procesos de negocio.

Los casos de uso que considero más interesantes para desarrollar son:

* **Gestión y explotación del dato**

  * Centralización de información.
  * Reporting y dashboards.
  * Consultas sobre los datos mediante lenguaje natural.
  * Detección de tendencias y alertas.

* **Gestión inteligente de seguros y claims**

  * Consulta y comparación de coberturas.
  * Validación previa de intervenciones frente a las condiciones de la póliza.
  * Detección de posibles problemas antes de presentar un claim.
  * Gestión de incidencias y claims rechazados.
  * Presentación de evidencias que justifiquen las conclusiones del agente.

* **Gestión inteligente de citas**

  * Predicción de *no-shows*.
  * Propuesta y gestión de citas.
  * Recordatorios personalizados.
  * Adaptación según preferencias e historial del paciente.

* **Asistencia clínica**

  * Asistente conversacional para pacientes y profesionales.
  * Transcripción de consultas.
  * Generación asistida de documentación clínica.
  * Integración con los procesos posteriores de cobertura y facturación.

* **Gestión y planificación de personal**

  * Creación de un pool interno de talento.
  * Preclasificación de candidatos según requisitos.
  * Detección anticipada de necesidades de personal según la carga asistencial.
  * Asistencia en onboarding, credenciales y seguimiento de CME.

El objetivo será desarrollar estas capacidades de forma **incremental**, comenzando por funcionalidades sencillas y evolucionando hacia procesos más automatizados, manteniendo siempre controles de acceso, trazabilidad, supervisión humana y cumplimiento regulatorio.


## Mi idea de Agente de IA

### Contexto

HealthCore necesita desarrollar un agente de IA orientado a mejorar la atención y gestión del paciente, integrando soporte conversacional, información sobre seguros médicos, gestión inteligente de citas y análisis de datos.

El sistema deberá diseñarse de forma modular e incremental, comenzando por funcionalidades sencillas y evolucionando hacia automatizaciones más avanzadas.

### Funcionalidades

#### 1. Asistente clínico y de soporte al paciente

Crear un asistente conversacional utilizando **Responses API** que permita a pacientes y profesionales interactuar mediante lenguaje natural.

**Para el paciente**, el agente deberá resolver consultas básicas, proporcionar información disponible y determinar cuándo una petición requiere acceder a otros sistemas o escalarse a una persona.

Basándose en el historial médico y siempre dentro de los permisos establecidos, podrá recuperar resultados, informes y diagnósticos existentes y explicarlos al paciente en un lenguaje comprensible, indicando claramente cuándo la información debe ser revisada o confirmada por un profesional sanitario.

**Para el profesional sanitario**, el agente actuará como asistente clínico. Con los mecanismos de consentimiento, privacidad y seguridad correspondientes, podrá **grabar y transcribir la conversación entre médico y paciente** durante la consulta.

A partir de la transcripción y del historial disponible, podrá generar un **borrador estructurado de la documentación clínica**, destacando la información relevante de la consulta y reduciendo el trabajo administrativo del profesional.

El médico deberá revisar y validar siempre el contenido generado antes de incorporarlo al historial clínico.

La documentación validada podrá alimentar posteriormente otros procesos del sistema, como evaluación de cobertura, codificación, facturación y reporting.

#### 2. Seguros, cobertura y facturación

Crear un sistema **RAG** con la documentación de pólizas y condiciones de los seguros médicos, conectado con la información relevante del paciente y su historial.

El agente utilizará esta información durante todo el ciclo:

**Antes de la consulta**

* Identificar la póliza activa del paciente.
* Consultar condiciones y exclusiones.
* Evaluar si una consulta, prueba o intervención tiene cobertura.
* Mostrar la evidencia utilizada y un nivel estimado de cobertura.

**Después de la consulta**

* Analizar la documentación clínica generada.
* Sugerir los códigos de facturación correspondientes.
* Preparar un borrador del claim con la información disponible.
* Validarlo contra las reglas y condiciones conocidas de la aseguradora.

**Antes de enviar el claim**

* Detectar información ausente o inconsistente.
* Identificar posibles causas de rechazo.
* Asignar un nivel de riesgo de rechazo.
* Solicitar revisión humana cuando exista riesgo elevado o información insuficiente.

El objetivo será reducir errores de codificación y disminuir progresivamente la tasa actual de **claims rechazados del 14 %**, manteniendo siempre trazabilidad sobre la información y evidencia utilizada por el agente.

Los claims rechazados podrán iniciar automáticamente un flujo de revisión que identifique el motivo del rechazo, recupere la documentación relacionada y prepare la información necesaria para su corrección o reclamación.

#### 3. Gestión inteligente de citas

Crear un sistema de citas médicas integrado con el agente.

Después de una consulta, el sistema podrá detectar la necesidad de seguimiento, consultar disponibilidad y proponer citas teniendo en cuenta:

* Disponibilidad médica.
* Preferencias del paciente.
* Historial de citas.
* Necesidades de seguimiento indicadas.

Un proceso automático revisará diariamente las próximas citas y decidirá cuándo enviar recordatorios.

El contenido y frecuencia de los recordatorios podrán adaptarse a la importancia del seguimiento, evitando que el agente realice por sí mismo diagnósticos o valoraciones clínicas.

#### 4. Datos, reporting y gobierno del dato

Registrar los eventos relevantes generados por el sistema en una **base de datos estructurada** para análisis y reporting.

Crear una plataforma para managers que permita:

* Consultar KPIs.
* Analizar actividad y tendencias.
* Visualizar información mediante dashboards.
* Realizar preguntas en lenguaje natural sobre los datos disponibles.

Además, el sistema permitirá **recopilar y consolidar la información asociada a un paciente procedente de los diferentes sistemas**, facilitando la gestión de solicitudes de acceso, consulta, exportación o revisión de sus datos conforme a los requisitos regulatorios aplicables.


#### 5. Gestión inteligente de RR. HH. y planificación de recursos

Crear un sistema de gestión y planificación de talento que permita a RR. HH. anticipar las necesidades de personal y reducir los tiempos de contratación.

El sistema mantendrá un **pool interno de talento**, incluyendo interns y otros perfiles potencialmente incorporables, registrando especialidad, experiencia, evaluaciones autorizadas y evolución dentro de la organización.

Para nuevas contrataciones, la IA podrá analizar los CVs recibidos y **preclasificarlos según los requisitos objetivos del puesto**, identificando qué requisitos cumple cada candidato y cuáles no. La decisión final permanecerá siempre bajo responsabilidad del equipo de RR. HH.

El sistema analizará además datos operativos como volumen de citas, carga asistencial, disponibilidad y evolución histórica para **detectar posibles carencias de personal antes de que se conviertan en una necesidad crítica**.

Cuando se detecte una necesidad, podrá generar automáticamente un borrador del perfil requerido —especialidad, experiencia, ubicación y otros requisitos— para su revisión y aprobación por RR. HH. antes de iniciar el proceso de búsqueda.

Una vez contratado un profesional, el sistema podrá gestionar su **onboarding**, verificación de credenciales y seguimiento de formación médica continua (**CME**), generando alertas ante documentación, certificaciones o formación próximas a caducar.


### Información necesaria

El agente podrá trabajar, según permisos y jurisdicción, con:

* Perfil e identificación del paciente.
* Región y jurisdicción aplicable.
* Seguro y póliza contratada.
* Documentación de aseguradoras.
* Historial relevante del paciente.
* Historial y preferencias de citas.
* Disponibilidad de profesionales y clínicas.
* Eventos e interacciones generados por el propio sistema.

### Guardrails

La **región del paciente será una restricción obligatoria** en cualquier recuperación o procesamiento de información.

El sistema deberá impedir consultas sobre datos, pólizas o documentación pertenecientes a regiones no autorizadas.

Además:

* Aplicar control de acceso basado en identidad y permisos.
* Mantener trazabilidad de consultas y acciones.
* Separar información de EE.UU. y Reino Unido cuando sea necesario.
* Aplicar los requisitos correspondientes de **HIPAA y UK GDPR**.
* No presentar estimaciones de IA como decisiones médicas o confirmaciones contractuales definitivas.

### KPIs

Mediremos inicialmente:

* % de consultas resueltas automáticamente.
* % de consultas escaladas a soporte humano.
* Precisión de recuperación del RAG.
* % de evaluaciones de cobertura con evidencia suficiente.
* Tiempo medio de respuesta.
* Tasa de citas propuestas → aceptadas.
* Tasa de no-shows.
* Reducción de no-shows tras recordatorios.
* Tiempo administrativo ahorrado.
* Número de incidencias o bloqueos producidos por los guardrails.
* Tiempo medio de contratación.
* % de posiciones cubiertas mediante el pool interno.
* Tiempo entre detección de una necesidad y apertura de la posición.
* Carga asistencial por profesional/sede.
* % de candidatos que cumplen los requisitos mínimos.
* Tiempo medio de onboarding.
* % de profesionales con credenciales y CME actualizados.

### Milestones

**M1 — Support Agent:** asistente conversacional funcional con Responses API.

**M2 — Insurance RAG:** consulta de pólizas, evaluación de cobertura y asistencia en claims basada en evidencia.

**M3 — Smart Scheduling:** propuesta automática de citas y recordatorios personalizados.

**M4 — Data & Intelligence:** almacenamiento centralizado, dashboards, alertas y consultas en lenguaje natural.

**M5 — Workforce Intelligence:** gestión del pool de talento, preclasificación de candidatos, detección predictiva de necesidades de personal y asistencia en onboarding, credenciales y CME.


### Reto principal de automatización

Conseguir que el agente pueda pasar de una conversación con el paciente a una acción útil —por ejemplo, **detectar que necesita seguimiento, validar preliminarmente su cobertura, localizar citas compatibles y proponerlas automáticamente**— manteniendo permisos, trazabilidad y restricciones regulatorias durante todo el flujo.

### Propuesta tecnológica

A grandes rasgos, la plataforma se apoyará en los siguientes componentes:

* **API centralizada desarrollada en Python** que actúe como capa común de acceso e integración con los diferentes sistemas de HealthCore.
* **Agente de IA mediante Responses API**, conectado de forma controlada con las herramientas y fuentes de información disponibles.
* **Sistema RAG**, utilizando embeddings y una base de datos vectorial para consultar pólizas, documentación clínica y documentación interna.
* **Bases de datos segregadas por región y jurisdicción**, garantizando el aislamiento y residencia adecuada de los datos sujetos a HIPAA y UK GDPR.
* **Sistema de identidad, roles y permisos**, limitando tanto el acceso a información como las acciones que puede realizar cada usuario y el propio agente.
* **Capa de herramientas e integraciones** para conectar el agente con EHR, citas, seguros, facturación, RR. HH. y otros sistemas corporativos.
* **Procesamiento asíncrono y tareas programadas** para recordatorios, análisis periódicos, procesamiento documental y otras automatizaciones.
* **Pipeline de datos y capa de analytics** para consolidar la información necesaria para KPIs, reporting, dashboards y consultas en lenguaje natural.
* **Sistema de auditoría y observabilidad** que permita mantener trazabilidad sobre accesos, decisiones y acciones realizadas por el sistema. Monitorización y observabilidad técnica, con health checks, métricas, logs centralizados y alertas automáticas sobre los diferentes componentes e integraciones de la plataforma.
* **Speech-to-Text** para la transcripción de consultas y generación asistida de documentación clínica.
* **Interfaces diferenciadas** para pacientes, profesionales sanitarios, managers y RR. HH.

