"""Read-only clinic resolution and contexts bound to the authenticated actor."""
import hmac
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from app.auth.roles import has_capability
from app.db import session as database
from app.reference_data.models import Clinic, Jurisdiction
from app.telemetry.identity import (
    AUDIENCE, ISSUER, clinic_binding, decode_context, now_seconds,
    sign_context, subject_binding, user_id, region_settings,
)
from app.telemetry.schemas import ContextResponse, VERSION


async def resolve_clinic(settings, actor, clinic_id=None, binding=None):
    if not has_capability(actor.role, 'referenceData:read'):
        raise HTTPException(404, 'Clinic context unavailable')
    if database.SessionLocal is None:
        raise HTTPException(503, 'Telemetry context unavailable')
    statement = select(Clinic.id, Clinic.is_active, Jurisdiction.key, Jurisdiction.is_active).join(
        Jurisdiction, Clinic.jurisdiction_id == Jurisdiction.id)
    if clinic_id is not None:
        statement = statement.where(Clinic.id == clinic_id)
    async with database.SessionLocal() as session:
        result = await session.stream(statement)
        async for identity, active, region, region_active in result:
            matches = identity == clinic_id if clinic_id is not None else (region in {'US', 'UK'} and (settings.telemetry_processing_region is None or region == settings.telemetry_processing_region) and hmac.compare_digest(clinic_binding(region_settings(settings, region), identity), binding))
            if matches:
                if not active or not region_active or region not in {'US', 'UK'}:
                    raise HTTPException(422, 'Invalid clinic context')
                if settings.telemetry_processing_region is not None and region != settings.telemetry_processing_region:
                    raise HTTPException(403, 'Regional context unavailable')
                return clinic_binding(region_settings(settings, region), identity), region
    raise HTTPException(404, 'Clinic context unavailable')


async def issue_context(settings, actor, request, bearer_expiry, previous=None):
    timestamp = now_seconds()
    expiry = min(timestamp + settings.telemetry_context_ttl_seconds, bearer_expiry)
    if expiry <= timestamp:
        raise HTTPException(401, 'Authentication required')
    binding, jurisdiction = None, None
    if request.clinicId is not None:
        binding, jurisdiction = await resolve_clinic(settings, actor, clinic_id=request.clinicId)
    scoped = region_settings(settings, jurisdiction)
    sid = str(uuid4())
    if previous:
        # Invalid/expired previous credentials never silently create a new scope.
        sid = decode_context(settings, previous, actor)['sid']
    claims = dict(iss=ISSUER, aud=AUDIENCE, iat=timestamp, exp=expiry, sid=sid,
                  subjectBinding=subject_binding(scoped, actor.id), clinicBinding=binding,
                  processingRegion=scoped.telemetry_processing_region,
                  environment=settings.app_environment, jurisdiction=jurisdiction,
                  pseudonymVersion=settings.telemetry_key_version)
    return ContextResponse(contextToken=sign_context(scoped, claims), sessionId=sid,
                           userId=user_id(scoped, actor.id), jurisdiction=jurisdiction,
                           schemaVersion=VERSION, expiresAt=datetime.fromtimestamp(expiry, UTC).isoformat())
