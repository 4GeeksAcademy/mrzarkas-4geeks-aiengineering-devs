"""Independent bounded diagnostic channel: failures only affect local counters."""
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.telemetry.identity import keys
from app.telemetry.schemas import TelemetryBatch, TelemetryReceipt, VERSION
from app.telemetry.server import ServerQueue

DIAGNOSTIC_EVENTS = frozenset({'telemetry_contract_rejected', 'telemetry_delivery_failed'})
STATE_KEY = 'healthcore_telemetry_contract_rejection'
logger = logging.getLogger('healthcore.telemetry.diagnostics')


async def diagnostic_sink(body):
    batch = TelemetryBatch.model_validate_json(body)
    if any(event.event_type not in DIAGNOSTIC_EVENTS for event in batch.events):
        raise ValueError('Diagnostic unavailable')
    logger.info('Telemetry diagnostic count=%d event_types=%s', len(batch.events),
                ','.join(sorted({event.event_type for event in batch.events})))
    return TelemetryReceipt(received=len(batch.events))


class DiagnosticChannel:
    def __init__(self, settings):
        self.settings = settings
        self.queue = ServerQueue(sink=diagnostic_sink, allowed_events=DIAGNOSTIC_EVENTS)
        self.discarded = 0

    def capture(self, event_type, jurisdiction, reason, request_id=None):
        try:
            keys(self.settings)
            if jurisdiction not in {'US', 'UK', None} or (request_id is not None and not isinstance(request_id, UUID)):
                raise ValueError('Diagnostic unavailable')
            event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(), sessionId=None,
                         userId=None, event_type=event_type, schemaVersion=VERSION,
                         requestId=str(request_id) if request_id is not None else None,
                         properties=dict(jurisdiction=jurisdiction, environment=self.settings.app_environment,
                                         reasonCode=reason, producer='api'))
            return self.queue.enqueue(event, jurisdiction or 'GENERAL')
        except Exception:
            self.discarded += 1
            return False

    async def close(self):
        await self.queue.close()


def mark_contract_rejection(request):
    try:
        request.scope.setdefault('state', {})[STATE_KEY] = True
    except Exception:
        pass


def capture_contract_rejection(request_id):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None or service.closed:
        return False
    try:
        return service.diagnostic_channel.capture('telemetry_contract_rejected', None, 'schema', request_id)
    except Exception:
        service.discarded += 1
        return False
