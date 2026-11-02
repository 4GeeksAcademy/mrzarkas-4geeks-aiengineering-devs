"""Short-lived UI-flow credentials: independent audience, regional and resource bound."""
import hmac
from uuid import uuid4

import jwt

from app.db import session as database
from app.inventory.models import InventoryItem, InventoryClinicItem
from app.inventory.policies import allow, scope
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import keys, region_settings, subject_binding, clinic_binding, ContextError, now_seconds
from app.telemetry.inventory_producer import resource_id

AUDIENCE = 'healthcore-inventory-flow'
ISSUER = 'healthcore-telemetry-inventory-flow'
FIELDS = {'iss', 'aud', 'iat', 'exp', 'flowId', 'subjectBinding', 'clinicBinding',
          'itemBinding', 'region', 'environment', 'keyVersion', 'direction'}


async def resolve_flow(actor, clinic_id, item_id, action):
    allow(actor, 'movement:write' if action == 'order_started' else 'stock:read')
    if database.SessionLocal is None:
        raise ValueError('Inventory flow unavailable')
    async with database.SessionLocal() as session:
        clinic = await session.get(Clinic, clinic_id)
        if clinic is None:
            raise ValueError('Inventory scope unavailable')
        scope(actor, clinic)
        country = await session.get(Jurisdiction, clinic.jurisdiction_id)
        item = await session.get(InventoryItem, item_id)
        if (country is None or not country.is_active or country.key not in {'US', 'UK'}
                or item is None or not item.is_active):
            raise ValueError('Inventory scope unavailable')
        if action == 'order_started' and await session.get(InventoryClinicItem, (item_id, clinic_id)) is None:
            raise ValueError('Inventory flow unavailable')
        return country.key


def issue_flow(settings, actor, clinic_id, item_id, direction, bearer_expiry, previous=None):
    decoded = keys(settings)
    current = now_seconds()
    expiry = min(current + 300, bearer_expiry)
    if expiry <= current:
        raise ContextError('Inventory flow expired')
    bindings = dict(subjectBinding=subject_binding(settings, actor.id),
                    clinicBinding=clinic_binding(settings, clinic_id),
                    itemBinding=resource_id(settings, 'inventory_item', item_id))
    flow_id = resource_id(settings, 'inventory_flow', uuid4())
    if previous:
        try:
            header = jwt.get_unverified_header(previous)
            if header.get('region') != settings.telemetry_processing_region or header.get('kid') != settings.telemetry_key_version:
                raise ValueError('Invalid flow selector')
            claims = jwt.decode(previous, decoded[3], algorithms=['HS256'], audience=AUDIENCE,
                issuer=ISSUER, options={'require': sorted(FIELDS - {'direction'})})
            if (set(claims) != FIELDS or claims['region'] != settings.telemetry_processing_region
                    or claims['environment'] != settings.app_environment or claims['keyVersion'] != settings.telemetry_key_version
                    or any(not isinstance(claims[name], str) or not hmac.compare_digest(claims[name], value)
                           for name, value in bindings.items())
                    or claims['direction'] not in {None, 'inbound', 'outbound'}
                    or (claims['direction'] is not None and claims['direction'] != direction)):
                raise ValueError('Invalid flow scope')
            from re import fullmatch
            if not isinstance(claims['flowId'], str) or not fullmatch(r'ps_[0-9a-f]{64}', claims['flowId']):
                raise ValueError('Invalid flow identity')
            flow_id = claims['flowId']
            expiry = min(expiry, claims['exp'])  # Never extend an existing flow's lifetime.
        except Exception as error:
            raise ContextError('Invalid inventory flow') from error
    claims = dict(iss=ISSUER, aud=AUDIENCE, iat=current, exp=expiry, flowId=flow_id,
        **bindings, region=settings.telemetry_processing_region, environment=settings.app_environment,
        keyVersion=settings.telemetry_key_version, direction=direction)
    token = jwt.encode(claims, decoded[3], algorithm='HS256',
        headers={'kid': settings.telemetry_key_version, 'region': settings.telemetry_processing_region})
    return flow_id, token, expiry
