"""Bounded package/runtime coherence check, not a clinical-data integrity scan."""
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import create_model

from app.telemetry import schemas

MAX_CONTRACT_BYTES = 128 * 1024


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Invalid contract')
        result[key] = value
    return result


def check_contract():
    try:
        with Path(schemas.__file__).with_name('event-contract.json').open('rb') as stream:
            body = stream.read(MAX_CONTRACT_BYTES + 1)
        if len(body) > MAX_CONTRACT_BYTES:
            return 'failed'
        contract = json.loads(body, object_pairs_hook=_unique_object)
        if contract != schemas.CONTRACT:
            return 'failed'
        # Equivalent JSON object ordering must not change generated field order.
        definitions = schemas.CONTRACT['definitions']
        envelope = definitions['envelope']['properties']
        names = set(definitions) - {'envelope'}
        if envelope['schemaVersion']['const'] != schemas.VERSION or names != set(schemas.EVENT_MODELS):
            return 'failed'
        mapping = schemas.TelemetryBatch.model_json_schema()['properties']['events']['items']['discriminator']
        if mapping['propertyName'] != 'event_type' or set(mapping['mapping']) != names:
            return 'failed'
        for name in names:
            model = schemas.EVENT_MODELS[name]
            definition = definitions[name]['allOf'][1]
            if definition['properties']['event_type']['const'] != name:
                return 'failed'
            fields = dict(envelope)
            fields.update(definition['properties'])
            expected = create_model(model.__name__, __base__=schemas.Envelope,
                                    **{key: (schemas.annotation(value), ...) for key, value in fields.items()})
            if model.model_json_schema() != expected.model_json_schema():
                return 'failed'
            if mapping['mapping'][name] != '#/$defs/' + model.__name__:
                return 'failed'
        return 'ok'
    except Exception:
        return 'failed'  # Never reflect file content, path or exception details.


def capture_startup_integrity(service):
    if service is None or service.closed or getattr(service, '_integrity_attempted', False):
        return False
    service._integrity_attempted = True
    try:
        outcome = check_contract()
        event = dict(eventId=str(uuid4()), timestamp=datetime.now(UTC).isoformat(),
                     userId=None, sessionId=None, requestId=None,
                     event_type='data_integrity_checked', schemaVersion=schemas.VERSION,
                     properties=dict(jurisdiction=None, environment=service.settings.app_environment,
                                     check='event_contract', outcome=outcome))
        return service.queue.enqueue(event, 'GENERAL')
    except Exception:
        service.discarded += 1
        return False
