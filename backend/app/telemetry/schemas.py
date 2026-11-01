"""Models derived from the packaged documentary contract, not a second catalogue."""
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, create_model

CONTRACT = json.loads(Path(__file__).with_name('event-contract.json').read_text())
VERSION = CONTRACT['definitions']['envelope']['properties']['schemaVersion']['const']
NULLABLE_EVENTS = frozenset(
    name for name, schema in CONTRACT['definitions'].items()
    if name != 'envelope' and None in schema['allOf'][1]['properties']['properties']['properties']['jurisdiction'].get('enum', [])
)

# Producer admission is independent of nullable jurisdiction in the catalogue.
GENERAL_EVENTS = frozenset({'navigation_viewed', 'frontend_timing_measured',
                            'application_error_observed', 'session_started', 'session_ended'})



def annotation(schema):
    if 'anyOf' in schema:
        return Union[tuple(annotation(part) for part in schema['anyOf'])]
    if 'const' in schema:
        return Literal[schema['const']]
    if 'enum' in schema:
        return Literal[tuple(schema['enum'])]
    kind = schema['type']
    if kind == 'null':
        return type(None)
    if kind == 'object':
        fields = {name: (annotation(value), ...) for name, value in schema['properties'].items()}
        return create_model('TelemetryProperties', __config__=ConfigDict(extra='forbid', strict=True, allow_inf_nan=False), **fields)
    value = {'string': str, 'integer': int, 'number': float}[kind]
    constraints = {}
    for source, target in [('pattern', 'pattern'), ('minimum', 'ge'), ('maximum', 'le')]:
        if source in schema:
            constraints[target] = schema[source]
    if schema.get('format') == 'date-time':
        # Keep the lexical value in the envelope; validate actual date separately.
        from pydantic import AfterValidator
        def valid_date(text):
            parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                raise ValueError('Timezone required')
            return text
        return Annotated[str, Field(**constraints), AfterValidator(valid_date)]
    return Annotated[value, Field(**constraints)] if constraints else value


class Envelope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


EVENT_MODELS = {}
for name, definition in CONTRACT['definitions'].items():
    if name == 'envelope':
        continue
    fields = dict(CONTRACT['definitions']['envelope']['properties'])
    fields.update(definition['allOf'][1]['properties'])
    EVENT_MODELS[name] = create_model(
        ''.join(part.title() for part in name.split('_')) + 'Event',
        __base__=Envelope, **{key: (annotation(value), ...) for key, value in fields.items()}
    )
TelemetryEvent = Annotated[Union[tuple(EVENT_MODELS.values())], Field(discriminator='event_type')]


class TelemetryBatch(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    events: list[TelemetryEvent] = Field(min_length=1, max_length=20)


class TelemetryReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid')
    received: int


class ContextRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    clinicId: UUID | None


class ContextResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    contextToken: str
    sessionId: str
    userId: str
    jurisdiction: Literal['US', 'UK'] | None
    schemaVersion: Literal[VERSION]
    expiresAt: str
