from contextlib import asynccontextmanager

import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from app import main


def request_status():
    async def request():
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
            return await client.get("/status")
    return asyncio.run(request())


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
    response = request_status()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
    assert statements == ["SELECT 1"]


def test_status_without_database_configuration(monkeypatch):
    monkeypatch.setattr(main, "engine", None)
    response = request_status()
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_status_does_not_expose_database_errors(monkeypatch):
    class Engine:
        @asynccontextmanager
        async def connect(self):
            raise SQLAlchemyError("sensitive connection details")
            yield

    monkeypatch.setattr(main, "engine", Engine())
    response = request_status()
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
    assert "sensitive" not in response.text
