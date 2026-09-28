from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.catalogs.router import router as catalogs_router
from app.compliance.router import router as compliance_router
from app.incidents.router import router as incidents_router
from app.management.router import router as management_router

app = FastAPI(title="HealthCore API")
app.include_router(auth_router)
app.include_router(catalogs_router)
app.include_router(compliance_router)
app.include_router(incidents_router)
app.include_router(management_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
