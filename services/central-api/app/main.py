from fastapi import FastAPI

from app.catalogs.router import router as catalogs_router
from app.incidents.router import router as incidents_router

app = FastAPI(title="HealthCore API")
app.include_router(catalogs_router)
app.include_router(incidents_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}