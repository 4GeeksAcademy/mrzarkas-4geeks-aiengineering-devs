import asyncio, json, math, statistics, time
from datetime import UTC, datetime
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from app.main import app
from app.db.session import SessionLocal, engine, get_session
from app.db.models.catalog import CatalogValue
from app.incidents.models import OperationalIncident
from app.auth.security import create_access_token
from tests.reference_fixtures import reference_ids

async def main():
    refs = await reference_ids()
    async with SessionLocal() as session:
        ids = dict((await session.execute(select(CatalogValue.key, CatalogValue.id))).all())
        actor = uuid4(); now = datetime.now(UTC)
        for i in range(100):
            session.add(OperationalIncident(id=uuid4(), incident_identifier="PERF-" + uuid4().hex,
                title=f"Synthetic performance {i:03d}", description="Synthetic description. " * 400,
                reporter_id=actor, clinic_id=refs["dev-us-clinic-01"], jurisdiction_id=refs["US"],
                affected_system_id=refs["usEhr"], responsible_area_id=refs["technology"],
                entry_channel_value_id=ids["clinicPhone"], incident_type_value_id=ids["systemAvailability"],
                severity_value_id=ids["critical"], status_value_id=ids["new"],
                created_at=now, updated_at=now, created_by=actor, updated_by=actor))
        await session.flush()
        statements=[]; columns=[]; relationship_loads=[]
        def sql(conn,cursor,statement,parameters,context,executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)
                compiled=getattr(context,"compiled",None)
                selected=getattr(getattr(compiled,"statement",None),"selected_columns",None)
                if selected is not None: columns.append(list(selected.keys()))
        def orm(state):
            if state.is_relationship_load: relationship_loads.append(True)
        event.listen(engine.sync_engine,"before_cursor_execute",sql)
        event.listen(session.sync_session,"do_orm_execute",orm)
        async def isolated(): yield session
        old=app.dependency_overrides.get(get_session); app.dependency_overrides[get_session]=isolated
        result={"dataset":{"incidents":100,"description_chars":len("Synthetic description. " * 400),"page_limit":25},"samples_per_round":50,"warmup":5,"transport":"HTTP ASGI in test container; SQL to PostgreSQL in Podman; single reused transaction/session"}
        try:
            async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test",headers={"Authorization":"Bearer " + create_access_token(actor,"admin")}) as client:
                for path in ("/incidents?limit=25&sort_by=title&sort_direction=asc", "/management/reference-data/clinics?limit=25"):
                    rounds=[]
                    for label in ("before_no_change","after_no_change"):
                        samples=[]; sizes=[]; counts=[]; loads=[]
                        for i in range(55):
                            statements.clear(); columns.clear(); relationship_loads.clear()
                            start=time.perf_counter(); response=await client.get(path); elapsed=(time.perf_counter()-start)*1000
                            assert response.status_code==200
                            if i>=5:
                                samples.append(elapsed); sizes.append(len(response.content)); counts.append(len(statements)); loads.append(len(relationship_loads))
                        ordered=sorted(samples)
                        rounds.append({"round":label,"p50_ms":round(statistics.median(samples),3),"p95_ms":round(ordered[math.ceil(.95*len(ordered))-1],3),"payload_bytes":sorted(set(sizes)),"queries_per_request":sorted(set(counts)),"relationship_loads":sorted(set(loads)),"selected_columns":columns.copy(),"sql_without_parameters":statements.copy()})
                    result[path]=rounds
        finally:
            event.remove(engine.sync_engine,"before_cursor_execute",sql); event.remove(session.sync_session,"do_orm_execute",orm)
            if old is None: app.dependency_overrides.pop(get_session,None)
            else: app.dependency_overrides[get_session]=old
            await session.rollback()
    await engine.dispose()
    print(json.dumps(result,indent=2))
asyncio.run(main())
