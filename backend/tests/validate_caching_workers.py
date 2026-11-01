"""Explicit validator: isolated temporary PostgreSQL database, always dropped.
Run in the test image; never runs against application data or as a pytest test.
"""
import asyncio
import json
import multiprocessing as mp
import os
from uuid import uuid4


def worker(url, channel):
    os.environ['DATABASE_URL'] = url
    async def run():
        from httpx import ASGITransport, AsyncClient
        from app.auth.security import create_access_token
        from app.catalogs.cache import catalog_cache
        from app.db.session import engine
        from app.main import app
        actor = __import__('uuid').UUID('00000000-0000-0000-0000-000000000001')
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers={'Authorization': 'Bearer '+create_access_token(actor, 'admin')}) as client:
            channel.send({'pid': os.getpid()})
            while True:
                command = await asyncio.to_thread(channel.recv)
                if command['action'] == 'stop': break
                try:
                    if command['action'] == 'read':
                        first = await client.get('/catalogs/syntheticWorkers')
                        second = await client.get('/management/catalogs/syntheticWorkers/values')
                        assert first.status_code == second.status_code == 200
                        channel.send({'active': first.json(), 'managed': second.json(), 'hits': catalog_cache.hits, 'misses': catalog_cache.misses})
                    elif command['action'] == 'write':
                        response = await client.request(command['method'], command['path'], json=command['body'])
                        channel.send({'status': response.status_code, 'body': response.json()})
                    elif command['action'] == 'concurrent':
                        catalog_cache.clear()
                        semaphore = asyncio.Semaphore(10)
                        hits, misses = catalog_cache.hits, catalog_cache.misses
                        async def read_one(path):
                            async with semaphore:
                                response = await client.get(path)
                                assert response.status_code == 200
                                return response.json()
                        responses = await asyncio.gather(*(read_one(path) for path in ['/catalogs/syntheticWorkers', '/management/catalogs/syntheticWorkers/values'] * 10))
                        assert all(r == responses[i % 2] for i, r in enumerate(responses))
                        channel.send({'requests': len(responses), 'concurrency': 10, 'hits': catalog_cache.hits-hits, 'misses': catalog_cache.misses-misses, 'consistent': True})
                    elif command['action'] == 'benchmark':
                        import math
                        import time
                        import socket
                        import uvicorn
                        from sqlalchemy import event
                        listener = socket.socket()
                        listener.bind(('127.0.0.1', 0))
                        listener.listen(128)
                        server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False, lifespan='off'))
                        serving = asyncio.create_task(server.serve(sockets=[listener]))
                        while not server.started:
                            if serving.done():
                                await serving
                                raise RuntimeError('temporary HTTP server failed to start')
                            await asyncio.sleep(.01)
                        network_client = AsyncClient(base_url=f'http://127.0.0.1:{listener.getsockname()[1]}', headers=client.headers, timeout=10)
                        results = []
                        selects = [0]
                        def count(conn, cursor, statement, parameters, context, executemany):
                            if statement.lstrip().upper().startswith('SELECT'):
                                selects[0] += 1
                        event.listen(engine.sync_engine, 'before_cursor_execute', count)
                        try:
                            for path in ['/catalogs/syntheticWorkers', '/management/catalogs/syntheticWorkers/values']:
                                for round_number in range(1, 4):
                                    for enabled in [False, True]:
                                        catalog_cache.clear()
                                        catalog_cache.enabled = enabled
                                        # Warm both modes sequentially; measured requests use independent sessions.
                                        for _ in range(20):
                                            assert (await network_client.get(path)).status_code == 200
                                        selects[0] = 0
                                        hits, misses = catalog_cache.hits, catalog_cache.misses
                                        semaphore = asyncio.Semaphore(10)
                                        async def sample():
                                            async with semaphore:
                                                started = time.perf_counter()
                                                response = await network_client.get(path)
                                                elapsed = (time.perf_counter() - started) * 1000
                                                assert response.status_code == 200
                                                return elapsed, len(response.content)
                                        samples = await asyncio.gather(*(sample() for _ in range(200)))
                                        ordered = sorted(x[0] for x in samples)
                                        results.append({'path': path, 'round': round_number, 'cache': enabled,
                                            'samples': 200, 'concurrency': 10,
                                            'p50_ms': ordered[math.ceil(.5 * len(ordered)) - 1],
                                            'p95_ms': ordered[math.ceil(.95 * len(ordered)) - 1],
                                            'selects_per_request_average': selects[0] / len(samples),
                                            'response_bytes': sorted({x[1] for x in samples}),
                                            'hits': catalog_cache.hits - hits, 'misses': catalog_cache.misses - misses})
                        finally:
                            event.remove(engine.sync_engine, 'before_cursor_execute', count)
                            catalog_cache.enabled = True
                            catalog_cache.clear()
                            await network_client.aclose()
                            server.should_exit = True
                            await serving
                            listener.close()
                        channel.send({'transport': 'Loopback HTTP + Uvicorn + real PostgreSQL; independent request sessions',
                            'dataset': 'Two synthetic values, one inactive after mutation validation',
                            'warmup_per_mode': 20, 'results': results})
                except Exception as error:
                    channel.send({'error_type': type(error).__name__})
        await engine.dispose()
    try: asyncio.run(run())
    finally: channel.close()


def ask(channel, **command):
    channel.send(command)
    if not channel.poll(60): raise RuntimeError('worker timeout')
    result = channel.recv()
    assert 'error_type' not in result, result
    return result


async def main():
    from datetime import UTC, datetime, timedelta
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.config import get_settings
    # Imports register the same complete models as the running application.
    from app.main import app
    from app.db.base import Base
    from app.db.models.catalog import Catalog, CatalogValue
    from sqlalchemy.engine import make_url
    original = make_url(get_settings().require_database_url())
    database = 'caching_validation_' + uuid4().hex
    admin = create_async_engine(original.set(database='postgres'), isolation_level='AUTOCOMMIT', poolclass=NullPool)
    isolated = create_async_engine(original.set(database=database), poolclass=NullPool)
    children = []
    created = False
    try:
        async with admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{database}"'))
            created = True
        async with isolated.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        now = datetime.now(UTC); actor = __import__('uuid').UUID('00000000-0000-0000-0000-000000000001')
        sessions = async_sessionmaker(isolated, expire_on_commit=False)
        async with sessions() as session:
            catalog = Catalog(id=uuid4(), catalog_name='syntheticWorkers', version=1, is_active=True, created_at=now, updated_at=now, created_by=actor, updated_by=actor)
            session.add(catalog); await session.flush()
            value = CatalogValue(id=uuid4(), catalog_id=catalog.id, key='synthetic', label='Synthetic before', description=None, is_active=True, is_open=True, sort_order=0, effective_from=now-timedelta(days=1), effective_to=None, created_at=now, updated_at=now, created_by=actor, updated_by=actor)
            session.add(value); await session.commit(); identifier = str(value.id)
        context = mp.get_context('spawn')
        for _ in range(2):
            parent, child = context.Pipe()
            process = context.Process(target=worker, args=(original.set(database=database).render_as_string(hide_password=False), child))
            process.start(); child.close()
            assert parent.poll(20)
            metadata = parent.recv()
            children.append((process, parent, metadata['pid']))
        a, b = children[0][1], children[1][1]
        ask(a, action='read'); ask(b, action='read')
        assert ask(a, action='read')['hits'] >= 2
        assert ask(b, action='read')['hits'] >= 2
        base = '/management/catalogs/syntheticWorkers/values'
        assert ask(a, action='write', method='PATCH', path=f'{base}/{identifier}', body={'label':'Synthetic after'})['status'] == 200
        changed = ask(b, action='read')
        assert changed['active']['values'][0]['label'] == changed['managed']['items'][0]['label'] == 'Synthetic after'
        created_value = ask(a, action='write', method='POST', path=base, body={'key':'syntheticSecond','label':'Synthetic second','effective_from':now.isoformat()})
        assert created_value['status'] == 201
        assert len(ask(b, action='read')['active']['values']) == 2
        assert ask(a, action='write', method='POST', path=f'{base}/{identifier}/activation', body={'is_active':False,'reason':'Synthetic validation only'})['status'] == 200
        deactivated = ask(b, action='read')
        assert len(deactivated['active']['values']) == 1 and deactivated['managed']['total'] == 2
        concurrency = ask(b, action='concurrent')
        benchmark = ask(b, action='benchmark')
        result = {'workers': [x[2] for x in children], 'distinct_processes': children[0][2] != children[1][2], 'both_warm_before_write':True, 'cross_process_update_create_activation': 'PASS', 'concurrent_reads': concurrency, 'concurrent_benchmark': benchmark, 'application_database_untouched':True}
    finally:
        for process, channel, _ in children:
            if process.is_alive(): channel.send({'action':'stop'})
            process.join(10)
            if process.is_alive(): process.terminate(); process.join(5)
            channel.close()
        await isolated.dispose()
        if created:
            async with admin.connect() as connection:
                await connection.execute(text(f'DROP DATABASE "{database}"'))
        await admin.dispose()
    result['isolated_database_dropped'] = True
    print(json.dumps(result, indent=2))

if __name__ == '__main__': asyncio.run(main())
