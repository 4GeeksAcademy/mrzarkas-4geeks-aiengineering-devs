import pytest
from test_telemetry_context import telemetry, ACTOR
from test_telemetry import event


@pytest.mark.parametrize('name',['telemetry_contract_rejected','telemetry_delivery_failed'])
def test_frontend_diagnostics_only_general_authenticated_context(telemetry,name):
    _,request=telemetry
    context=request('/telemetry/context',{'clinicId':None}).json()
    value=event(context);value['event_type']=name
    value['properties']=dict(jurisdiction=None,environment='test',producer='frontend',
                             reasonCode='schema' if name=='telemetry_contract_rejected' else 'unavailable')
    headers={'X-Telemetry-Context':context['contextToken']}
    assert request('/telemetry/events',{'events':[value]},headers).json()=={'received':1}
    for producer in ['api','worker']:
        value['properties']['producer']=producer
        assert request('/telemetry/events',{'events':[value]},headers).status_code==403
    value['properties']['producer']='frontend'
    value['requestId']=str(ACTOR)
    assert request('/telemetry/events',{'events':[value]},headers).status_code==403
    value['requestId']=None
    value['userId']='ps_'+'b'*64
    assert request('/telemetry/events',{'events':[value]},headers).status_code==403


def test_clinical_context_cannot_assert_frontend_diagnostic(telemetry,monkeypatch):
    from app.telemetry import context as module, router
    async def resolve(*args,**kwargs):return 'b'*64,'US'
    monkeypatch.setattr(module,'resolve_clinic',resolve);monkeypatch.setattr(router,'resolve_clinic',resolve)
    _,request=telemetry
    context=request('/telemetry/context',{'clinicId':str(ACTOR)}).json()
    value=event(context);value['event_type']='telemetry_delivery_failed'
    value['properties']=dict(jurisdiction='US',environment='test',producer='frontend',reasonCode='unavailable')
    headers={'X-Telemetry-Context':context['contextToken']}
    assert request('/telemetry/events',{'events':[value]},headers).status_code==403
    value['properties']['jurisdiction']=None
    assert request('/telemetry/events',{'events':[value]},headers).status_code==403
