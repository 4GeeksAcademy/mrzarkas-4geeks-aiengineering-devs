# Backoffice de incidencias operativas

UI estática de desarrollo, sin dependencias, para la API OperationalIncident.
Incluye cola paginada, detalle y editor de título/descripción limitado por área.
La API es la frontera de autorización. Solo datos sintéticos: no autorizado
para escritura compartida, datos reales, piloto ni producción.

## Arranque local integrado

Desde la raíz del monorepo: `podman compose up --build -d` o
`docker compose up --build -d`, con el `.env` raíz preparado según la
[guía de configuración](../../../frontend/README.es.md).
Abrir http://localhost:8080 y usar http://localhost:8000 como URL API.
El arranque aplica migraciones y seeds sintéticos. Next.js está en 3000 y
Management en http://localhost:8080/management/.

Para servir solo la UI: `python -m http.server 8080 --directory uis/backoffice/operational-incidents`.
Introducir la URL API y un JWT de desarrollo. El JWT solo vive en memoria,
se descarta al recargar o desconectar y no se guarda en URL ni almacenamiento.
Fuera de desarrollo local se necesita HTTPS. Para orígenes distintos, la API
requiere CORS explícito con Authorization y Content-Type, nunca comodines.

## Páginas y comportamiento

- `#/incidents`: cola paginada, filtros de estado/severidad; roles amplios pueden
  filtrar área, responsibleArea queda limitado a su área JWT. Muestra carga,
  error recuperable y lista vacía. Alta disponible para admin, technology y responsibleArea.
- `#/incidents/new`: alta con catálogos y referencias activas de la API. Clínicas
  según jurisdicción; el backend valida jurisdicción del sistema afectado. La
  identidad del reportante deriva del JWT y no se envía desde el formulario.
- `#/incidents/{uuid}`: detalle; responsibleArea edita título y descripción solo
  en su área. Admin y technology usan sus permisos generales. Roles de lectura
  no tienen editor. La autorización de la API siempre prevalece.

ResponsibleArea solo puede crear para su área JWT. Tras un alta correcta se
abre el detalle y se muestra confirmación. La UI decodifica claims para mostrar
controles, pero no verifica firmas ni concede permisos. Etiquetas de catálogos
y referencias vienen de la API, insertadas como texto y nunca como HTML.

Límites actuales: título de 200 caracteres y descripción de 10.000. El aviso
sobre PHI es un recordatorio, no un detector ni un control de cumplimiento.
Los valores siguen sujetos a aprobación M0.

[English](./README.md).


## Identidad visual

La interfaz utiliza la paleta de la portada HealthCore Digital, CSS nativo,
distribución responsive y foco visible de teclado. Se conservan las consultas
a la API, las rutas y el manejo del token. Las tablas se desplazan dentro de
sus contenedores en pantallas pequeñas.

Validación: sintaxis JavaScript y comprobación del diff correctas; HTTP
confirma que ambas páginas y CSS coinciden con los archivos locales. Se
revisaron las pantallas iniciales en escritorio y Management a 393px.
Quedan pendientes las vistas con datos autenticados, el recorrido completo
por teclado y las incidencias en móvil; no se proporcionó JWT de desarrollo
para revisar las vistas con datos.
