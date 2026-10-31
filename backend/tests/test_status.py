from contextlib import asynccontextmanager

import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from app import main


def request(path):
    async def request():
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
            return await client.get(path)
    return asyncio.run(request())


def test_health_response_matches_its_contract():
    response = request("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_and_status_openapi_declare_success_and_unavailable_contracts():
    paths = main.app.openapi()["paths"]
    health_response = paths["/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    status_responses = paths["/status"]["get"]["responses"]
    status_success = status_responses["200"]["content"]["application/json"]["schema"]
    status_unavailable = status_responses["503"]["content"]["application/json"]["schema"]

    assert health_response["$ref"].endswith("/HealthResponse")
    assert status_success["$ref"].endswith("/StatusConnectedResponse")
    assert status_unavailable["$ref"].endswith("/StatusUnavailableResponse")


def test_status_confirms_database_without_application_tables(monkeypatch):
    statements = []

    class Connection:
        async def execute(self, statement):
            statements.append(str(statement))

    class Engine:
        @asynccontextmanager
        async def connect(self):
            yield Connection()

    monkeypatch.setattr(main, "engine", Engine())
    response = request("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
    assert statements == ["SELECT 1"]


def test_status_without_database_configuration(monkeypatch):
    monkeypatch.setattr(main, "engine", None)
    response = request("/status")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_status_does_not_expose_database_errors(monkeypatch):
    class Engine:
        @asynccontextmanager
        async def connect(self):
            raise SQLAlchemyError("sensitive connection details")
            yield

    monkeypatch.setattr(main, "engine", Engine())
    response = request("/status")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
    assert "sensitive" not in response.text
