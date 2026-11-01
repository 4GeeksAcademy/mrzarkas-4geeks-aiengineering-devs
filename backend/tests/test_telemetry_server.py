import asyncio
import json
from uuid import uuid4
from datetime import datetime, UTC

from app.telemetry.server import ServerQueue, stub_sink
from app.telemetry.schemas import TelemetryReceipt


def event():
    return dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), sessionId=None,
                userId='ps_'+'a'*64, event_type='incident_created', schemaVersion='1.2.0', requestId=None,
                properties=dict(jurisdiction='US', environment='test', incidentId='ps_'+'b'*64, auditId='ps_'+'c'*64))


class Timer:
    def __init__(self, at, fn): self.at, self.fn, self.cancelled = at, fn, False
    def cancel(self): self.cancelled = True


class Clock:
    def __init__(self): self.now, self.timers = 0, []
    def time(self): return self.now
    def call_later(self, delay, fn):
        timer = Timer(self.now+delay, fn); self.timers.append(timer); return timer
    def create_task(self, coro): return asyncio.create_task(coro)
    async def advance(self, value):
        self.now += value
        for timer in list(self.timers):
            if not timer.cancelled and timer.at <= self.now:
                timer.cancel(); timer.fn()
        for _ in range(6): await asyncio.sleep(0)


def test_deadline_from_first_capture_and_twenty_trigger():
    async def run():
        clock, batches = Clock(), []
        async def sink(body):
            data=json.loads(body);batches.append(data);return TelemetryReceipt(received=len(data['events']))
        queue=ServerQueue(loop=clock,sink=sink)
        queue.enqueue(event(),'clinic'); await clock.advance(9)
        queue.enqueue(event(),'clinic'); await clock.advance(1)
        assert [len(b['events']) for b in batches]==[2]
        for _ in range(20):queue.enqueue(event(),'clinic')
        await clock.advance(0)
        assert [len(b['events']) for b in batches]==[2,20]
        await queue.close();assert queue.size==0
    asyncio.run(run())


def test_single_flight_preserves_new_events_and_partitions_clinics():
    async def run():
        batches=[];gate=asyncio.Event()
        async def sink(body):
            batches.append(json.loads(body));await gate.wait();return TelemetryReceipt(received=len(batches[-1]['events']))
        queue=ServerQueue(sink=sink)
        original=event();queue.enqueue(original,'clinicA');original['properties']['incidentId']='private-invalid'
        flight=asyncio.create_task(queue.flush());await asyncio.sleep(0)
        queue.enqueue(event(),'clinicB');queue.enqueue(event(),'clinicA')
        await queue.flush();assert len(batches)==1 and len(queue.pending)==2
        gate.set();await flight
        assert batches[0]['events'][0]['properties']['incidentId']=='ps_'+'b'*64
        await queue.flush();await queue.flush()
        assert [len(b['events']) for b in batches]==[1,1,1]
        assert queue.counts['received']==3
        await queue.close()
    asyncio.run(run())


def test_limits_validation_failure_and_shutdown_cleanup():
    async def run():
        queue=ServerQueue()
        for _ in range(200):assert queue.enqueue(event(),'clinic')
        assert not queue.enqueue(event(),'clinic')
        bad=event();bad['properties']['title']='synthetic-sensitive';assert not queue.enqueue(bad,'clinic')
        assert queue.size<=256*1024 and queue.counts['rejected']==2
        await queue.close();assert not queue.pending and queue.timer is None and queue.task is None
        assert queue.counts['discarded']==200
        assert not queue.enqueue(event(),'clinic')
        async def broken(body):raise RuntimeError('synthetic-sensitive-not-logged')
        queue=ServerQueue(sink=broken);queue.enqueue(event(),'clinic');await queue.flush()
        assert queue.counts['discarded']==1 and queue.size==0
        await queue.close()
    asyncio.run(run())


def test_stub_sink_contract_and_count_only_logging(caplog):
    async def run():
        with caplog.at_level('INFO',logger='healthcore.telemetry'):
            result=await stub_sink(json.dumps({'events':[event()]}).encode())
        assert result.received==1
        assert 'count=1' in caplog.text and 'incident_created' in caplog.text
        assert 'ps_' not in caplog.text and 'auditId' not in caplog.text
    asyncio.run(run())


def test_queue_inflight_quota_and_cancelled_sink_cleanup():
    async def run():
        gate=asyncio.Event();clock=Clock()
        async def sink(body):await gate.wait();return TelemetryReceipt(received=20)
        queue=ServerQueue(sink=sink,loop=clock)
        for _ in range(20):queue.enqueue(event(),'clinic')
        await clock.advance(0)
        assert len(queue.flight)==20
        for _ in range(180):assert queue.enqueue(event(),'clinic')
        assert not queue.enqueue(event(),'clinic')
        await queue.close()
        assert queue.size==0 and not queue.pending and queue.flight is None
        assert queue.counts['discarded']==200 and queue.task is None
    asyncio.run(run())


def test_malformed_ack_discards_without_retry_or_recursive_event():
    async def run():
        async def wrong(body):return TelemetryReceipt(received=99)
        queue=ServerQueue(sink=wrong);queue.enqueue(event(),'clinic');await queue.flush()
        assert queue.counts==dict(received=0,rejected=0,discarded=1)
        assert not queue.pending and queue.flight is None
        await queue.close()
    asyncio.run(run())
