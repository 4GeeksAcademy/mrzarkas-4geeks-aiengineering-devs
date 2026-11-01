from typing import Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
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
from app.telemetry.router import router as telemetry_router
from app.telemetry.audit_completion import AuditCompletionMiddleware
from app.telemetry.request_completion import RequestCompletionMiddleware
from app.telemetry.security_completion import SecurityCompletionMiddleware
from app.telemetry.health_completion import HealthCompletionMiddleware
from app.telemetry.diagnostic_completion import DiagnosticCompletionMiddleware
from app.telemetry.health_cache_producer import mark_health


class HealthResponse(BaseModel):
    status: Literal["ok"]


class StatusConnectedResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["connected"]


class StatusUnavailableResponse(BaseModel):
    status: Literal["error"]
    database: Literal["unavailable"]


@asynccontextmanager
async def lifespan(app):
    from app.telemetry import incident_producer
    from app.telemetry.integrity_producer import capture_startup_integrity
    capture_startup_integrity(incident_producer.start())
    try:
        yield
    finally:
        await incident_producer.stop()


app = FastAPI(title="HealthCore API", lifespan=lifespan)
app.add_middleware(AuditCompletionMiddleware)
app.add_middleware(SecurityCompletionMiddleware)
app.add_middleware(HealthCompletionMiddleware)
app.add_middleware(DiagnosticCompletionMiddleware)
app.add_middleware(RequestCompletionMiddleware)
settings = get_settings()
if settings.app_environment in {"development", "test"}:
    # Local static backoffice only. Shared environments should serve the UI
    # through a same-origin reverse proxy with an explicitly reviewed policy.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-Telemetry-Context"],
    )
app.include_router(auth_router)
app.include_router(catalogs_router)
app.include_router(compliance_router)
app.include_router(incidents_router)
app.include_router(management_router)
app.include_router(telemetry_router)


@app.get("/health", response_model=HealthResponse)
def health(request: Request = None) -> HealthResponse:
    mark_health(request, "liveness", "ok")
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
async def status(request: Request = None) -> StatusConnectedResponse | JSONResponse:
    """Check connectivity without reading or creating application data."""
    if engine is None:
        mark_health(request, "database", "failed")
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError) as error:
        mark_health(request, "database", "timeout" if isinstance(error, TimeoutError) else "failed")
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    mark_health(request, "database", "ok")
    return StatusConnectedResponse(status="ok", database="connected")
