import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.catalogs.cache import CatalogCache, catalog_cache
from app.auth.dependencies import Actor
from app.auth.security import create_access_token
from app.db.session import get_session
from app.main import app


def test_ttl_isolation_serialization_eviction():
    now = [0]
    cache = CatalogCache(clock=lambda: now[0], max_entries=2, max_bytes=1000)
    actor = Actor(uuid4(), 'admin')
    key = cache.key('active', actor, uuid4(), 1)
    cache.put(key, {'items': [1]}, 30)
    result = cache.get(key); result['items'].append(2)
    assert cache.get(key) == {'items': [1]}
    assert str(actor.id) not in key
    assert cache.key('active', Actor(uuid4(), 'admin'), 'severity', 1) != cache.key('active', actor, 'severity', 1)
    assert cache.key('active', Actor(actor.id, 'compliance'), 'severity', 1) != cache.key('active', actor, 'severity', 1)
    assert cache.key('active', Actor(actor.id, 'responsibleArea', uuid4()), 'severity', 1) != cache.key('active', actor, 'severity', 1)
    cache.put('b', {}, 30); cache.put('c', {}, 30)
    assert cache.get(key) is None
    now[0] = 30
    assert cache.get('c') is None
    cache.put('large', {'x': 'x' * 1001}, 30)
    assert cache.get('large') is None
    cache.clear(); assert cache.size == 0


def test_singleflight_stale_fill_and_source_failures():
    async def run():
        cache = CatalogCache()
        calls = 0
        async def load():
            nonlocal calls
            calls += 1
            await asyncio.sleep(.001)
            return {'value': calls}
        async def current(): return True
        results = await asyncio.gather(*(cache.read('0' * 64, 30, load, current) for _ in range(10)))
        assert calls == 1 and all(r == {'value': 1} for r in results)
        async def stale(): return False
        await cache.read('1' * 64, 30, load, stale)
        assert cache.get('1' * 64) is None
        cache.get = lambda key: (_ for _ in ()).throw(ValueError('synthetic cache failure'))
        assert (await cache.read('2' * 64, 30, load, current))['value'] == 3
        async def failing(): raise RuntimeError('source unavailable')
        try: await cache.read('3' * 64, 30, failing, current)
        except RuntimeError: pass
        else: raise AssertionError('Source error masked')
        assert all(not lock.locked() for lock in cache.locks)
    asyncio.run(run())


class Result:
    def __init__(self, value): self.value = value
    def scalar_one_or_none(self): return self.value
    def scalar_one(self): return self.value
    def one_or_none(self): return self.value
    def scalars(self): return self
    def all(self): return self.value


class SyntheticSession:
    def __init__(self):
        self.catalog = SimpleNamespace(id=uuid4(), catalog_name='severity', version=1, is_active=True, updated_at=datetime.now(UTC))
        now = datetime.now(UTC)
        self.values = [SimpleNamespace(id=uuid4(), key='synthetic', label='Synthetic', description=None, is_active=True, is_open=True, sort_order=0,
            effective_from=now-timedelta(days=1), effective_to=None, created_at=now, updated_at=now, created_by=uuid4(), updated_by=uuid4())]
        self.queries = 0
    async def execute(self, statement):
        self.queries += 1
        sql = str(statement)
        if 'count(' in sql: return Result(len(self.values))
        if 'FROM catalog_value' in sql: return Result(self.values)
        if 'SELECT catalog.version, catalog.updated_at' in sql: return Result(self.catalog)
        if 'SELECT catalog.version' in sql: return Result(self.catalog.version)
        return Result(self.catalog if self.catalog.is_active else None)


def test_both_http_routes_hits_version_invalidation_and_auth():
    async def run():
        session = SyntheticSession()
        async def fake(): yield session
        old = app.dependency_overrides.get(get_session)
        app.dependency_overrides[get_session] = fake
        catalog_cache.clear()
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                actor = uuid4()
                headers = {'Authorization': 'Bearer ' + create_access_token(actor, 'admin')}
                for path in ['/catalogs/severity', '/management/catalogs/severity/values?offset=0&limit=50']:
                    cold = await client.get(path, headers=headers)
                    assert cold.status_code == 200
                    session.queries = 0
                    warm = await client.get(path, headers=headers)
                    assert warm.json() == cold.json() and session.queries == 1
                    assert (await client.get(path)).status_code == 401
                    denied = {'Authorization': 'Bearer ' + create_access_token(uuid4(), 'direction')}
                    assert (await client.get(path, headers=denied)).status_code == 403
                    session.catalog.version += 1
                    session.values[0].label = 'Synthetic updated'
                    updated = await client.get(path, headers=headers)
                    assert 'Synthetic updated' in updated.text
                    session.values[0].label = 'Synthetic'
                assert (await client.get('/management/catalogs/severity/values?limit=101', headers=headers)).status_code == 422
                # A separate actor cannot hit the first actor's private entry.
                session.queries = 0
                await client.get('/catalogs/severity', headers={'Authorization': 'Bearer ' + create_access_token(uuid4(), 'admin')})
                assert session.queries > 1
        finally:
            catalog_cache.clear()
            if old is None: app.dependency_overrides.pop(get_session, None)
            else: app.dependency_overrides[get_session] = old
    asyncio.run(run())


def test_active_dates_are_projected_on_each_hit_without_mutation():
    async def run():
        from unittest.mock import patch
        from app.catalogs.router import get_catalog
        session = SyntheticSession(); actor = Actor(uuid4(), 'admin')
        instant = [datetime.now(UTC)]
        class Clock:
            @staticmethod
            def now(tz): return instant[0]
        session.values[0].effective_to = instant[0]
        catalog_cache.clear()
        with patch('app.catalogs.router.datetime', Clock):
            assert len((await get_catalog('severity', session, actor)).values) == 1
            instant[0] += timedelta(microseconds=1)
            assert (await get_catalog('severity', session, actor)).values == []
            catalog_cache.clear()
            session.values[0].effective_from = instant[0] + timedelta(seconds=1)
            session.values[0].effective_to = None
            assert (await get_catalog('severity', session, actor)).values == []
            instant[0] += timedelta(seconds=1)
            assert len((await get_catalog('severity', session, actor)).values) == 1
        catalog_cache.clear()
    asyncio.run(run())


def test_real_mutations_invalidate_both_caches_with_outer_rollback():
    async def run():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.pool import NullPool
        from app.db.session import engine as shared_engine
        engine = create_async_engine(shared_engine.url, poolclass=NullPool)
        from app.db.models.catalog import Catalog, CatalogValue
        from sqlalchemy import select
        actor = uuid4(); now = datetime.now(UTC); name = 'syntheticCacheTest' + uuid4().hex
        async with engine.connect() as connection:
            transaction = await connection.begin()
            async with AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode='create_savepoint') as session:
                catalog = Catalog(id=uuid4(), catalog_name=name, version=1, is_active=True, created_at=now, updated_at=now, created_by=actor, updated_by=actor)
                session.add(catalog); await session.flush()
                async def isolated(): yield session
                old = app.dependency_overrides.get(get_session); app.dependency_overrides[get_session] = isolated
                catalog_cache.clear()
                try:
                    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers={'Authorization': 'Bearer ' + create_access_token(actor, 'admin')}) as client:
                        active = f'/catalogs/{name}'; managed = f'/management/catalogs/{name}/values'
                        assert (await client.get(active)).json()['values'] == []
                        assert (await client.get(managed)).json()['items'] == []
                        created = await client.post(managed, json={'key': 'synthetic', 'label': 'Synthetic created', 'effective_from': (now-timedelta(days=1)).isoformat()})
                        assert created.status_code == 201
                        identifier = created.json()['id']
                        assert len((await client.get(active)).json()['values']) == 1
                        assert len((await client.get(managed)).json()['items']) == 1
                        updated = await client.patch(f'{managed}/{identifier}', json={'label': 'Synthetic changed'})
                        assert updated.status_code == 200
                        assert (await client.get(active)).json()['values'][0]['label'] == 'Synthetic changed'
                        assert (await client.get(managed)).json()['items'][0]['label'] == 'Synthetic changed'
                        deactivated = await client.post(f'{managed}/{identifier}/activation', json={'is_active': False, 'reason': 'Synthetic test only'})
                        assert deactivated.status_code == 200
                        assert (await client.get(active)).json()['values'] == []
                        assert (await client.get(managed)).json()['items'][0]['is_active'] is False
                        assert catalog.version == 4
                finally:
                    catalog_cache.clear()
                    if old is None: app.dependency_overrides.pop(get_session, None)
                    else: app.dependency_overrides[get_session] = old
            await transaction.rollback()
        async with engine.connect() as connection:
            assert (await connection.execute(select(Catalog.id).where(Catalog.catalog_name == name))).scalar_one_or_none() is None
    asyncio.run(run())
