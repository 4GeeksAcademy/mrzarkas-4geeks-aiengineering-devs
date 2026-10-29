# Entorno integrado de HealthCore

Un único proyecto Compose comparte API y PostgreSQL entre la página Next.js,
el backoffice de incidencias y Management. Prototipo local con datos sintéticos,
sin datos de pacientes; no autorizado para piloto ni producción.

## Arranque

Desde la raíz del monorepo:

```sh
podman compose up --build -d
```

Con Docker activo, usar `docker compose up --build -d`. El `.env` local ya está
preparado. En una nueva copia, copiar `.env.example` a `.env` y completar las
variables antes del arranque. No subir `.env` a Git.

El arranque aplica migraciones y seeds existentes sobre la base compartida.
Ya no es una base vacía: esta integración prima sobre el alcance mínimo del
ejercicio inicial. No se borran volúmenes ni se importan datos del stack histórico.
El volumen `mvp-postgres-data` conserva su nombre para no reemplazar la base local.

## Aplicaciones

| Aplicación | URL local |
| --- | --- |
| Página Next.js de estado y enlaces | http://localhost:3000 |
| Incidencias operativas | http://localhost:8080 |
| Management | http://localhost:8080/management/ |
| Estado API y PostgreSQL | http://localhost:8000/status |
| OpenAPI | http://localhost:8000/docs |

Next.js consulta `http://backend:8000/status` en el servidor, sin caché y con
límite de cinco segundos. El backend usa `db:5432`. Incidencias y Management
usan el mismo origen 8080 y los controles de autorización existentes.
Para utilizar sus pantallas, introducir la URL local de la API y un JWT de
desarrollo siguiendo la guía existente de la API.

| Variable | Local value / Valor local |
| --- | --- |
| POSTGRES_DB | healthcore_stack |
| POSTGRES_USER | healthcore_stack |
| POSTGRES_PASSWORD | openssl rand -hex 32 |
| DATABASE_URL | postgresql+asyncpg://USER:PASSWORD@db:5432/DATABASE |
| BACKEND_URL | http://backend:8000 |
| APP_ENVIRONMENT | development |
| JWT_SECRET_KEY | openssl rand -hex 32 |
| API_PORT | 8000 |
| FRONTEND_PORT | 3000 |
| BACKOFFICE_PORT | 8080 |
| BACKOFFICE_URL | http://localhost:8080 |

Usar en DATABASE_URL los mismos valores de usuario, contraseña y base definidos
arriba. Generar cada secreto por separado. No reutilizar credenciales de otros
entornos. BACKOFFICE_URL es una URL para el navegador; BACKEND_URL es interna.
Si se cambia 8080, hay que revisar la política CORS existente antes de usar la UI.
Node 24 y Python 3.12 se instalan en las imágenes; la primera construcción
requiere Internet. Se mantiene uv para Python y pnpm para Next.js.

## Comprobaciones y parada

```sh
podman compose ps
podman compose logs -f
curl --fail http://localhost:8000/status
curl --fail http://localhost:3000
curl --fail http://localhost:8080
curl --fail http://localhost:8080/management/
podman compose down
```

`db-init` termina correctamente después de preparar la base; los otros cuatro
servicios permanecen activos. `test` solo se ejecuta con su perfil explícito.
No usar `down -v` si se quiere conservar la base. El archivo
`docker-compose.operational-incidents.yml` queda como copia histórica de la
configuración anterior; ya no se necesita para levantar el proyecto.

[English](./README.md).


## Portada HealthCore Digital

La página principal contiene cabecera, hero de bienvenida, tarjetas de
Incidencias operativas y Management, presentación institucional y footer.
Los destinos originales se mantienen. Inventario no está implementado y no
se presenta como herramienta disponible. Un indicador discreto en el footer
conserva la consulta existente a /status desde el servidor.

Se utilizan CSS Modules nativos de Next.js (`app/page.module.css`), fuentes
del sistema, foco visible de teclado y soporte de movimiento reducido. El
hero reutiliza `app/assets/imgs/AdobeStock_2207054294.jpeg` con next/image.
El original no se modifica; no hay imágenes ni fuentes externas en ejecución.

Compilar con `podman compose build frontend`. Para ver solo este cambio,
ejecutar `podman compose up -d --no-deps frontend` y abrir el puerto 3000.
No requiere reiniciar backend ni inicializar la base. El paquete ofrece
build/dev/start; no tiene scripts de lint ni pruebas configurados. Revisar
escritorio/móvil, navegación por teclado y ambos enlaces en el navegador.

Validación realizada: build de producción correcto; portada, ambos destinos
y los nueve recursos referenciados responden HTTP 200. Se revisó visualmente
el escritorio. La revisión visual completa en móvil, el recorrido por teclado
y la consola quedan pendientes: los cambios concurrentes de foco de Chrome
impidieron completar esas comprobaciones. No se ejecutaron lint ni tests al
no existir scripts configurados.

## Auditoría de rendimiento

El hero conserva next/image, dimensiones intrínsecas y preload, y añade
`fetchPriority="high"` para su petición LCP. Mediciones reproducibles de
producción y capturas en `../audit/`; análisis en `../AUDIT.md`.
