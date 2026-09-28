from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.catalogs.router import router as catalogs_router
from app.compliance.router import router as compliance_router
from app.core.config import get_settings
from app.incidents.router import router as incidents_router
from app.management.router import router as management_router

app = FastAPI(title="HealthCore API")
settings = get_settings()
if settings.app_environment in {"development", "test"}:
    # Local static backoffice only. Shared environments should serve the UI
    # through a same-origin reverse proxy with an explicitly reviewed policy.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_methods=["GET", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
app.include_router(auth_router)
app.include_router(catalogs_router)
app.include_router(compliance_router)
app.include_router(incidents_router)
app.include_router(management_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
