"""Synthetic transaction rolled back. Run explicitly, never collected as a test."""
import asyncio
from datetime import UTC, datetime, timedelta
import json
import math
import time
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, func, select
from app.auth.security import create_access_token
from app.catalogs.cache import catalog_cache
from app.db.models.catalog import Catalog, CatalogValue
from app.db.session import SessionLocal, engine, get_session
from app.main import app

async def main():
    async with SessionLocal() as session:
        before = (await session.execute(select(func.count()).select_from(CatalogValue))).scalar_one()
        actor = uuid4(); now = datetime.now(UTC); name = 'syntheticCaching' + uuid4().hex
        catalog = Catalog(id=uuid4(), catalog_name=name, version=1, is_active=True, created_at=now, updated_at=now, created_by=actor, updated_by=actor)
        session.add(catalog)
        await session.flush()
        for i in range(200):
            session.add(CatalogValue(id=uuid4(), catalog_id=catalog.id, key=f'synthetic{i}', label=f'Synthetic {i}', description=None, is_active=True, is_open=True, sort_order=i,
                effective_from=now-timedelta(days=1), effective_to=None, created_at=now, updated_at=now, created_by=actor, updated_by=actor))
        await session.flush()
        after = (await session.execute(select(func.count()).select_from(CatalogValue))).scalar_one()
        statements = [0]
        def count(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith('SELECT'): statements[0] += 1
        event.listen(engine.sync_engine, 'before_cursor_execute', count)
        async def isolated(): yield session
        old = app.dependency_overrides.get(get_session); app.dependency_overrides[get_session] = isolated
        result = {'method': 'ASGI + PostgreSQL in Podman; single transaction/session; 200 synthetic catalog values, rollback; sequential only. Before=current code cache disabled, after=warm cache, not old implementation or network traffic.', 'rows_before': before, 'rows_during': after, 'warmup': 20, 'samples_per_round': 200, 'concurrency': 1, 'results': []}
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers={'Authorization': 'Bearer ' + create_access_token(actor, 'admin')}) as client:
                for endpoint, path in [('active-catalog', f'/catalogs/{name}'), ('managed-values', f'/management/catalogs/{name}/values?limit=100')]:
                    for round in range(3):
                        for enabled in [False, True]:
                            catalog_cache.clear(); catalog_cache.enabled = enabled
                            hits, misses = catalog_cache.hits, catalog_cache.misses
                            samples = []; queries = []; sizes = []
                            for i in range(220):
                                statements[0] = 0; start = time.perf_counter()
                                response = await client.get(path)
                                elapsed = (time.perf_counter()-start)*1000
                                assert response.status_code == 200
                                if i >= 20: samples.append(elapsed); queries.append(statements[0]); sizes.append(len(response.content))
                            ordered = sorted(samples)
                            result['results'].append({'endpoint': endpoint, 'round': round+1, 'cache': enabled, 'p50_ms': ordered[math.ceil(.5*len(ordered))-1], 'p95_ms': ordered[math.ceil(.95*len(ordered))-1], 'selects_per_request': sorted(set(queries)), 'response_bytes': sorted(set(sizes)), 'hits_including_warmup': catalog_cache.hits-hits, 'misses_including_warmup': catalog_cache.misses-misses})
        finally:
            event.remove(engine.sync_engine, 'before_cursor_execute', count)
            if old is None: app.dependency_overrides.pop(get_session, None)
            else: app.dependency_overrides[get_session] = old
            catalog_cache.enabled = True; catalog_cache.clear()
            await session.rollback()
        result['rows_after_rollback'] = (await session.execute(select(func.count()).select_from(CatalogValue))).scalar_one()
        assert result['rows_after_rollback'] == before
    await engine.dispose()
    print(json.dumps(result, indent=2))

if __name__ == '__main__': asyncio.run(main())
