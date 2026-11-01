import asyncio
import json
from copy import deepcopy
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import create_model

from app import main
from app.telemetry import schemas, incident_producer, integrity_producer as integrity
from app.telemetry.diagnostic_producer import DiagnosticChannel
from app.telemetry.schemas import TelemetryReceipt
from app.telemetry.server import stub_sink
from test_telemetry_incident_producer import settings
from test_telemetry_shared import shared


def test_packaged_contract_and_semantically_reordered_document(monkeypatch, tmp_path):
    assert integrity.check_contract() == 'ok'
    path=tmp_path/'event-contract.json'
    path.write_text(json.dumps(schemas.CONTRACT,sort_keys=True))
    monkeypatch.setattr(integrity,'Path',lambda _:tmp_path/'schemas.py')
    assert integrity.check_contract() == 'ok'


@pytest.mark.parametrize('failure',['missing','size','json','duplicate','version','catalog','field'])
def test_bounded_document_rejections(monkeypatch,tmp_path,failure):
    path=tmp_path/'event-contract.json';value=deepcopy(schemas.CONTRACT)
    if failure=='version':value['definitions']['envelope']['properties']['schemaVersion']['const']='0.0.0'
    if failure=='catalog':value['definitions'].pop('data_integrity_checked')
    if failure=='field':value['definitions']['envelope']['required'].pop()
    if failure!='missing':
        path.write_text('x'*(integrity.MAX_CONTRACT_BYTES+1) if failure=='size' else '{' if failure=='json' else '{"a":1,"a":2}' if failure=='duplicate' else json.dumps(value))
    monkeypatch.setattr(integrity,'Path',lambda _:tmp_path/'schemas.py')
    assert integrity.check_contract()=='failed'


@pytest.mark.parametrize('failure',['model','mapping','version','fields'])
def test_runtime_discrepancies(monkeypatch,failure):
    if failure=='version':monkeypatch.setattr(schemas,'VERSION','0.0.0')
    else:
        models=dict(schemas.EVENT_MODELS)
        if failure=='model':models.pop('data_integrity_checked')
        elif failure=='fields':models['data_integrity_checked']=create_model('InvalidModel',value=(str,...))
        else:monkeypatch.setattr(schemas.TelemetryBatch,'model_json_schema',lambda:{'properties':{'events':{'items':{'discriminator':{'propertyName':'wrong','mapping':{}}}}}})
        monkeypatch.setattr(schemas,'EVENT_MODELS',models)
    assert integrity.check_contract()=='failed'


def test_capture_once_anonymous_closed_and_disabled(monkeypatch):
    async def run():
        calls=[]
        monkeypatch.setattr(integrity,'check_contract',lambda:calls.append(True) or 'failed')
        assert not integrity.capture_startup_integrity(None) and not calls
        service=incident_producer.IncidentProducer(shared(settings()))
        assert integrity.capture_startup_integrity(service)
        assert not integrity.capture_startup_integrity(service) and calls==[True]
        event=json.loads(service.queue.pending[0][2])
        assert event['properties']==dict(jurisdiction=None,environment='test',check='event_contract',outcome='failed')
        assert all(event[name] is None for name in ['userId','sessionId','requestId'])
        assert (await stub_sink(b'{"events":['+service.queue.pending[0][2]+b']}')).received==1
        channel=DiagnosticChannel(shared(settings()))
        assert not channel.queue.enqueue(event,'GENERAL')
        assert event['event_type'] not in schemas.GENERAL_EVENTS
        await channel.close();await service.close()
        assert not integrity.capture_startup_integrity(service) and calls==[True]
        second=incident_producer.IncidentProducer(shared(settings()))
        assert integrity.capture_startup_integrity(second) and calls==[True,True]
        await second.close()
    asyncio.run(run())


def test_capture_exception_and_full_queue_do_not_repeat(monkeypatch):
    async def run():
        service=incident_producer.IncidentProducer(shared(settings()))
        def broken():raise RuntimeError('Synthetic sensitive error')
        monkeypatch.setattr(integrity,'check_contract',broken)
        assert not integrity.capture_startup_integrity(service) and service.discarded==1
        assert not integrity.capture_startup_integrity(service)
        await service.close()
        service=incident_producer.IncidentProducer(shared(settings()))
        monkeypatch.setattr(integrity,'check_contract',lambda:'ok')
        from test_telemetry_server import event
        for _ in range(200):assert service.queue.enqueue(event(),'US')
        assert not integrity.capture_startup_integrity(service)
        diagnostic=json.loads(service.diagnostic_channel.queue.pending[0][2])
        assert diagnostic['properties']['reasonCode']=='queue_full' and diagnostic['properties']['jurisdiction'] is None
        assert not integrity.capture_startup_integrity(service)
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('enabled',[True,False])
def test_real_lifespan_optional_once_and_failed_check_preserves_health(monkeypatch,enabled):
    config=shared(settings());config.telemetry_enabled=enabled
    monkeypatch.setattr(incident_producer,'get_settings',lambda:config)
    monkeypatch.setattr(incident_producer,'_producer',None)
    calls=[];monkeypatch.setattr(integrity,'check_contract',lambda:calls.append(True) or 'failed')
    async def run():
        async with main.app.router.lifespan_context(main.app):
            service=incident_producer._producer
            assert calls==([True] if enabled else [])
            if enabled:
                assert incident_producer.start() is service
                assert not integrity.capture_startup_integrity(service) and calls==[True]
                assert json.loads(service.queue.pending[0][2])['properties']['outcome']=='failed'
                async def broken(body):raise RuntimeError('Synthetic sink failure')
                service.queue.sink=broken
                await service.queue.flush()
                assert service.queue.counts['discarded']==1
                assert len(service.diagnostic_channel.queue.pending)==1
            else:assert service is None
            async with AsyncClient(transport=ASGITransport(app=main.app),base_url='http://test') as client:
                response=await client.get('/health');assert response.status_code==200 and response.json()=={'status':'ok'}
        if enabled:assert service.closed and service.queue.task is None and service.diagnostic_channel.queue.closed
    asyncio.run(run())
