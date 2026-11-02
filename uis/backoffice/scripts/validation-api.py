"""Fresh, synthetic PostgreSQL test API. Requires optional QA tooling pgserver.
Never reads .env or reuses an existing database. Stop with Ctrl-C.
"""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import os, secrets, subprocess, sys, tempfile
import pgserver

root = Path(__file__).resolve().parents[3] / "backend"
server = pgserver.get_server(tempfile.mkdtemp(prefix="hc-backoffice-validation-"), cleanup_mode="stop")
try:
    server.psql("CREATE DATABASE backoffice_validation;")
    uri = urlparse(server.get_uri())
    query = parse_qs(uri.query)
    user = uri.username or query.get("user", [os.getenv("USER", "")])[0]
    env = dict(os.environ, APP_ENVIRONMENT="test", TELEMETRY_ENABLED="false",
        JWT_SECRET_KEY=secrets.token_urlsafe(48),
        DATABASE_URL=f"postgresql+asyncpg://{user}@/backoffice_validation",
        PGHOST=query.get("host", [uri.hostname or "localhost"])[0],
        PGPORT=query.get("port", [str(uri.port or 5432)])[0])
    python = str(root / ".venv/bin/python")
    for args in (["-m", "alembic", "upgrade", "head"],
        ["-m", "app.catalogs.seed"],
        ["-c", "from app.reference_data.seed import main; main()"],
        ["-m", "app.inventory.demo"]):
        subprocess.run([python, *args], cwd=root, env=env, check=True)
    print("SYNTHETIC TEST API READY on port 18190; fresh database, no production data", flush=True)
    subprocess.run([python, "-m", "uvicorn", "app.main:app", "--host", os.getenv("HC_QA_API_HOST", "127.0.0.1"), "--port", "18190", "--no-access-log"], cwd=root, env=env, check=True)
finally:
    server.cleanup()
