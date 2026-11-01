"""General health facts and counter-only, process-local cache windows."""
import asyncio
import math
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.telemetry.identity import keys
from app.telemetry.schemas import VERSION

STATE_KEY = 'healthcore_telemetry_health'


def enqueue_general(service, event_type, scope, request_id=None, **properties):
    try:
        if service.closed:
            return False
        keys(service.settings)
        event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), sessionId=None,
                     userId=None, event_type=event_type, schemaVersion=VERSION,
                     requestId=str(request_id) if request_id is not None else None,
                     properties=dict(jurisdiction=None, environment=service.settings.app_environment, **properties))
        return service.queue.enqueue(event, scope)
    except Exception:
        service.discarded += 1
        return False


def mark_health(request, check, outcome):
    try:
        if request is not None and check in {'liveness', 'database'} and outcome in {'ok', 'failed', 'timeout'}:
            request.scope.setdefault('state', {})[STATE_KEY] = (check, outcome)
    except Exception:
        pass


def capture_health(check, outcome, duration, request_id):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None:
        return False
    try:
        if not isinstance(request_id, UUID) or not math.isfinite(duration) or duration < 0:
            return False
        return enqueue_general(service, 'service_health_checked', 'GENERAL:health', request_id,
                               check=check, outcome=outcome, durationMs=duration)
    except Exception:
        service.discarded += 1
        return False


class CacheSampler:
    def __init__(self, service, cache, *, clock=time.monotonic, sleep=asyncio.sleep):
        self.service, self.cache = service, cache
        self.clock, self.sleep = clock, sleep
        self.previous = self._counts()
        self.started = clock()
        self.task = None

    def _counts(self):
        try:
            values = tuple(getattr(self.cache, name) for name in ('hits', 'misses', 'bypasses'))
            if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
                return None
            return values
        except Exception:
            return None

    def cut(self):
        now, counts = self.clock(), self._counts()
        previous, started = self.previous, self.started
        self.previous, self.started = counts, now
        if self.service.closed:
            return False
        if counts is None or previous is None or any(value < old for value, old in zip(counts, previous)):
            self.service.discarded += 1
            return False
        elapsed = now - started
        if not math.isfinite(elapsed) or elapsed <= 0:
            self.service.discarded += 1
            return False
        hits, misses, bypasses = (value - old for value, old in zip(counts, previous))
        return enqueue_general(self.service, 'catalog_cache_observed', 'GENERAL:cache',
                               hits=hits, misses=misses, bypasses=bypasses, windowSeconds=max(1, math.floor(elapsed)))

    async def run(self):
        while not self.service.closed:
            await self.sleep(300)
            try:
                self.cut()
            except Exception:
                self.service.discarded += 1

    def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self.run())
        return self

    async def close(self):
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
            self.task = None
        self.previous = None
