"""Existing backend suite against a fresh isolated synthetic database only."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import pgserver, tempfile,os,subprocess,secrets
root=Path(__file__).resolve().parents[3]/'backend'
server=pgserver.get_server(tempfile.mkdtemp(prefix='hc-backoffice-regression-'),cleanup_mode='stop')
try:
 server.psql('CREATE DATABASE inventory_validation_backoffice;')
 uri=urlparse(server.get_uri());q=parse_qs(uri.query);user=uri.username or q.get('user',[os.getenv('USER','')])[0]
 url=f'postgresql+asyncpg://{user}@/inventory_validation_backoffice'
 env=dict(os.environ,APP_ENVIRONMENT='test',DATABASE_URL=url,INVENTORY_TEST_DATABASE_URL=url,JWT_SECRET_KEY=secrets.token_urlsafe(48),TELEMETRY_ENABLED='false',PGHOST=q.get('host',[uri.hostname or 'localhost'])[0],PGPORT=q.get('port',[str(uri.port or 5432)])[0])
 python=str(root/'.venv/bin/python')
 for args in [['-m','alembic','upgrade','head'],['-m','app.catalogs.seed'],['-c','from app.reference_data.seed import main; main()']]:subprocess.run([python,*args],cwd=root,env=env,check=True,stdout=subprocess.DEVNULL)
 r=subprocess.run([python,'-m','pytest','-q','tests/test_auth.py','tests/test_http_authorization.py','tests/test_incident_workflows.py','tests/test_inventory.py','tests/test_inventory_demo.py','tests/test_inventory_audit_policy.py','tests/test_management_openapi.py'],cwd=root,env=env)
 raise SystemExit(r.returncode)
finally:server.cleanup()
