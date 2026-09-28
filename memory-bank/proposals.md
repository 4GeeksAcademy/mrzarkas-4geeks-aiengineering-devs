# Propuestas de mejora

## Estado

Pendientes de validación.

## Propuesta: convención formal de calidad

**Descripción:**  
Definir y documentar una convención formal para formateo, linting, testing y CI/CD.

**Motivo:**  
Aunque el Dev Container incluye algunas herramientas, actualmente no existe una política común ni comprobaciones automatizadas visibles.

**Estado:**  
Pendiente de validación.

**Acción posterior:**  
Si se aprueba, documentarla e incorporarla a `conventions.md`.

## Propuesta: autenticación JWT propia como paso intermedio hacia SSO

**Descripción:**
Implementar en `central-api` un mecanismo de autenticación propio basado en
JWT firmado por la propia API (HS256, secreto en variable de entorno), con
claims de `sub` (actor), `role` y, cuando aplique, `area_id`. Un endpoint
`POST /auth/tokens` emite tokens de forma explícita para desarrollo y
pruebas, ya que todavía no existe un proveedor de identidad corporativo.

**Motivo:**
Las specs de `OperationalIncident` asumen una matriz de permisos que se
"mapea al mecanismo de autenticación que exista en el monorepo", pero ese
mecanismo no existe (ver `discrepancies.md`). Sin autenticación no es
posible aplicar la matriz de capacidades ni proteger `audit:read` ni las
transiciones de estado.

**Diseño para ser reemplazable:**
- La verificación de JWT vive en un módulo aislado
  (`app/auth/security.py` y `app/auth/dependencies.py`).
- Los endpoints de negocio dependen de una interfaz mínima (`Actor` con
  `id`, `role`, `area_id`) y de funciones `require_capability(...)`, no del
  formato concreto del token.
- Sustituir el emisor propio por SSO/OIDC del cliente implicará cambiar
  cómo se obtiene y valida el token (por ejemplo, verificar firma contra
  las claves públicas del IdP), sin tocar los routers de incidencias.

**Plan de migración futuro:**
1. Integrar el IdP del cliente (SSO, probablemente OIDC) cuando esté
   disponible.
2. Mantener el emisor propio sólo para entornos de desarrollo/test.
3. Retirar `POST /auth/tokens` de cualquier entorno expuesto públicamente.

**Estado:**
Implementado como solución temporal (2026-09-28). Pendiente de sustitución
por el IdP real del cliente y de validación formal de Cumplimiento y
Tecnología.