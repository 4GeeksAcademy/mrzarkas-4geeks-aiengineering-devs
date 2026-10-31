from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth.router import router as auth_router
from app.catalogs.router import router as catalogs_router
from app.compliance.router import router as compliance_router
from app.core.config import get_settings
from app.incidents.router import router as incidents_router
from app.management.router import router as management_router
from app.db.session import engine


class HealthResponse(BaseModel):
    status: Literal["ok"]


class StatusConnectedResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["connected"]


class StatusUnavailableResponse(BaseModel):
    status: Literal["error"]
    database: Literal["unavailable"]


app = FastAPI(title="HealthCore API")
settings = get_settings()
if settings.app_environment in {"development", "test"}:
    # Local static backoffice only. Shared environments should serve the UI
    # through a same-origin reverse proxy with an explicitly reviewed policy.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
app.include_router(auth_router)
app.include_router(catalogs_router)
app.include_router(compliance_router)
app.include_router(incidents_router)
app.include_router(management_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/status",
    response_model=StatusConnectedResponse,
    responses={
        503: {
            "model": StatusUnavailableResponse,
            "description": "Database unavailable",
        }
    },
)
async def status() -> StatusConnectedResponse | JSONResponse:
    """Check connectivity without reading or creating application data."""
    if engine is None:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError):
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    return StatusConnectedResponse(status="ok", database="connected")
