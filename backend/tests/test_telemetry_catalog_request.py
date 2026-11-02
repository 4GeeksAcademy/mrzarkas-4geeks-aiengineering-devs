"""Authorized catalogue completion, general HMAC and cache-independent capture."""
import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4
import pytest
from app.auth.dependencies import Actor
from app.telemetry import request_producer as producer, incident_producer
from app.telemetry.identity import user_id,region_settings
from app.telemetry.request_completion import RequestCompletionMiddleware,REQUEST_ID_KEY
from app.telemetry.server import ServerQueue
from app.telemetry.schemas import TelemetryReceipt
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared

@pytest.mark.parametrize('case',['valid','role','regional','bad-key','id','route','closed','nan','disabled','saturated'])
def test_catalogue_identity_and_rejections(monkeypatch,case):
    async def run():
        if case=='disabled':
            monkeypatch.setattr(incident_producer,'_producer',None)
            assert not producer.capture_authenticated_general_request(None,None,None,None,None,None)
            return
        events=[]
        async def sink(body):
            batch=json.loads(body);events.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink))
        monkeypatch.setattr(incident_producer,'_producer',service)
        actor=Actor(uuid4(),'direction' if case=='role' else 'admin');request_id=uuid4()
        if case=='regional': service.settings=region_settings(service.settings,'US')
        if case=='bad-key': service.settings.telemetry_user_key=None
        if case=='closed': await service.close()
        if case=='saturated': monkeypatch.setattr(service.queue,'enqueue',lambda *args:False)
        accepted=producer.capture_authenticated_general_request(actor,'unknown' if case=='route' else 'catalogs',
            'caller-id' if case=='id' else request_id,200,float('nan') if case=='nan' else 125,datetime.now(UTC).isoformat())
        assert accepted==(case=='valid')
        while service.queue.pending: await service.queue.flush()
        if case=='valid':
            event=events[0]
            assert event['userId']==user_id(service.settings,actor.id)
            assert event['userId']!=user_id(region_settings(service.settings,'US'),actor.id)
            assert event['userId']!=user_id(region_settings(service.settings,'UK'),actor.id)
            assert event['requestId']==str(request_id) and event['sessionId'] is None
            assert event['properties']==dict(jurisdiction=None,environment='test',route='catalogs',statusCode=200,durationMs=125)
            assert str(actor.id) not in json.dumps(events)
        await service.close()
    asyncio.run(run())

@pytest.mark.parametrize('case',['stream','send','cancel','incomplete','duplicate','clinical','anonymous','capture'])
def test_authenticated_general_asgi_boundary(monkeypatch,case):
    async def run():
        captured=[];clinical=[];anonymous=[]
        actor=Actor(uuid4(),'admin');clock=iter([10,10.125])
        monkeypatch.setattr('app.telemetry.request_completion.monotonic',lambda:next(clock))
        def capture(*args):
            captured.append(args)
            if case=='capture':raise RuntimeError('synthetic')
        monkeypatch.setattr('app.telemetry.request_completion.capture_authenticated_general_request',capture)
        monkeypatch.setattr('app.telemetry.request_completion.capture_request',lambda *args:clinical.append(args))
        monkeypatch.setattr('app.telemetry.request_completion.capture_general_request',lambda *args:anonymous.append(args))
        async def app(scope,receive,send):
            producer.mark_authenticated_general_request(type('Request',(),{'scope':scope})(),actor,'catalogs')
            scope['state'][producer.GENERAL_STATE_KEY]='health'
            if case=='clinical':scope['state'][producer.STATE_KEY]=(actor,uuid4())
            if case=='anonymous':scope['state'].pop(producer.AUTH_GENERAL_STATE_KEY)
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'a','more_body':True})
            assert not captured
            if case!='incomplete':
                await send({'type':'http.response.body','body':b'b'})
                if case=='duplicate':await send({'type':'http.response.body','body':b''})
        async def send(message):
            if message['type']=='http.response.body' and not message.get('more_body',False):
                if case=='send':raise OSError('synthetic')
                if case=='cancel':raise asyncio.CancelledError()
        scope={'type':'http'}
        if case in {'send','cancel'}:
            with pytest.raises(OSError if case=='send' else asyncio.CancelledError):await RequestCompletionMiddleware(app)(scope,None,send)
        else: await RequestCompletionMiddleware(app)(scope,None,send)
        assert len(captured)==(1 if case in {'stream','duplicate','capture'} else 0)
        if captured:assert captured[0][:2]==(actor,'catalogs') and captured[0][4]==125
        assert len(clinical)==(1 if case=='clinical' else 0)
        assert len(anonymous)==(1 if case=='anonymous' else 0)
        assert not any(k in scope['state'] for k in [producer.STATE_KEY,producer.AUTH_GENERAL_STATE_KEY,producer.GENERAL_STATE_KEY,REQUEST_ID_KEY])
    asyncio.run(run())

@pytest.mark.integration
def test_postgres_cache_hit_miss_and_authorized_catalogue(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from httpx import ASGITransport,AsyncClient
    from app.catalogs import router
    from app.catalogs.cache import CatalogCache
    from app.db.models.catalog import Catalog,CatalogValue
    from app.db.session import get_session
    from app.auth.security import create_access_token
    from app.main import app
    from test_inventory import isolated_url
    async def run():
        engine=create_async_engine(isolated_url());factory=async_sessionmaker(engine,expire_on_commit=False)
        actor=Actor(uuid4(),'admin');now=datetime.now(UTC);name='synthetic-'+str(uuid4())
        async with factory() as session,session.begin():
            catalog=Catalog(catalog_name=name,version=1,is_active=True,created_at=now,updated_at=now,created_by=actor.id,updated_by=actor.id)
            session.add(catalog);await session.flush()
            value=CatalogValue(catalog_id=catalog.id,key='synthetic-value',label='Synthetic confidential label',description=None,is_active=True,is_open=True,sort_order=0,effective_from=now-timedelta(seconds=1),created_at=now,updated_at=now,created_by=actor.id,updated_by=actor.id)
            session.add(value);await session.flush()
        cache=CatalogCache();monkeypatch.setattr(router,'catalog_cache',cache)
        events=[]
        async def sink(body):
            batch=json.loads(body);events.extend(batch['events']);return TelemetryReceipt(received=len(batch['events']))
        service=incident_producer.IncidentProducer(shared(settings()),queue=ServerQueue(sink=sink));monkeypatch.setattr(incident_producer,'_producer',service)
        async def sessions():
            async with factory() as session:yield session
        old=app.dependency_overrides.get(get_session);app.dependency_overrides[get_session]=sessions
        try:
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                headers={'Authorization':'Bearer '+create_access_token(actor.id,actor.role),'X-Request-Id':'caller-id'}
                first=await client.get('/catalogs/'+name,headers=headers)
                second=await client.get('/catalogs/'+name,headers=headers)
                assert first.status_code==second.status_code==200 and first.json()==second.json()
                assert cache.misses==1 and cache.hits==1
                assert (await client.get('/catalogs/'+name)).status_code==401
                denied={'Authorization':'Bearer '+create_access_token(uuid4(),'direction')}
                assert (await client.get('/catalogs/'+name,headers=denied)).status_code==403
                assert (await client.get('/catalogs/not-found',headers=headers)).status_code==404
                while service.tasks:await asyncio.gather(*service.tasks)
                while service.queue.pending:await service.queue.flush()
                api=[e for e in events if e['event_type']=='api_request_completed']
                assert len(api)==2 and len({e['requestId'] for e in api})==2
                assert all(e['properties']['route']=='catalogs' and e['properties']['jurisdiction'] is None for e in api)
                assert all(e['userId']==user_id(service.settings,actor.id) for e in api)
                payload=json.dumps(api)
                assert all(str(x) not in payload for x in [actor.id,catalog.id,value.id,name,'Synthetic confidential label','caller-id'])
        finally:
            if old is None:app.dependency_overrides.pop(get_session,None)
            else:app.dependency_overrides[get_session]=old
            await service.close();await engine.dispose()
    asyncio.run(run())
