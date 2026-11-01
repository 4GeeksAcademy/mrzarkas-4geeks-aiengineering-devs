"""Bounded authenticated ingress: acknowledges validation, never persists events."""
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.auth.dependencies import Actor, get_current_actor
from app.auth.security import decode_access_token
from app.core.config import get_settings
from app.telemetry.context import issue_context, resolve_clinic
from app.telemetry.identity import ConfigurationError, ContextError, decode_context, keys, user_id, region_settings
from app.telemetry.diagnostic_producer import mark_contract_rejection
from app.telemetry.schemas import ContextRequest, ContextResponse, GENERAL_EVENTS, TelemetryBatch, TelemetryReceipt

logger = logging.getLogger('healthcore.telemetry')
MAX_BODY_BYTES = 48 * 1024


class SafeTelemetryRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handle(request):
            try:
                chunks, size = [], 0
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_BODY_BYTES:
                        return JSONResponse({'detail': 'Telemetry payload too large'}, status_code=413)
                    chunks.append(chunk)
                request._body = b''.join(chunks)
                response = await original(request)
            except HTTPException as error:
                detail = 'Authentication required' if error.status_code == 401 else error.detail
                response = JSONResponse({'detail': detail}, status_code=error.status_code)
            except RequestValidationError:
                mark_contract_rejection(request)
                response = JSONResponse({'detail': 'Invalid telemetry payload'}, status_code=422)
            except ConfigurationError:
                response = JSONResponse({'detail': 'Telemetry unavailable'}, status_code=503)
            except ContextError:
                response = JSONResponse({'detail': 'Invalid telemetry context'}, status_code=401)
            except (SQLAlchemyError, OSError, TimeoutError):
                response = JSONResponse({'detail': 'Telemetry context unavailable'}, status_code=503)
            response.headers['Cache-Control'] = 'no-store'
            return response
        return handle


class TelemetryError(BaseModel):
    detail: str


router = APIRouter(prefix='/telemetry', tags=['telemetry'], route_class=SafeTelemetryRoute,
                   responses={code: {'model': TelemetryError} for code in [401, 403, 404, 413, 422, 503]})


@router.post('/context', response_model=ContextResponse)
async def context(payload: ContextRequest, request: Request, actor: Actor = Depends(get_current_actor),
                  previous: str | None = Header(default=None, alias='X-Telemetry-Context')):
    settings = get_settings()
    keys(settings)
    # get_current_actor has verified the same Bearer already; preserve its real expiry.
    token = request.headers['authorization'].split(' ', 1)[1]
    expiry = decode_access_token(token).get('exp')
    if not isinstance(expiry, int) or isinstance(expiry, bool):
        raise HTTPException(401, 'Authentication required')
    return await issue_context(settings, actor, payload, expiry, previous)


@router.post('/events', response_model=TelemetryReceipt)
async def events(payload: TelemetryBatch, actor: Actor = Depends(get_current_actor),
                 credential: str = Header(alias='X-Telemetry-Context')):
    settings = get_settings()
    claims = decode_context(settings, credential, actor)
    settings = region_settings(settings, claims['jurisdiction'])
    if claims['clinicBinding'] is not None:
        await resolve_clinic(settings, actor, binding=claims['clinicBinding'])
    expected_user = user_id(settings, actor.id)
    for event in payload.events:
        # Only the reviewed frontend technical producer is enabled in this stub.
        # Server/worker facts cannot be asserted by a browser just because they fit JSON.
        diagnostic = event.event_type in {'telemetry_contract_rejected', 'telemetry_delivery_failed'}
        if diagnostic:
            if (event.properties.producer != 'frontend' or event.properties.jurisdiction is not None
                    or event.requestId is not None
                    or claims['clinicBinding'] is not None or claims['jurisdiction'] is not None):
                raise HTTPException(403, 'Event producer unavailable')
        elif event.event_type not in GENERAL_EVENTS:
            raise HTTPException(403, 'Event producer unavailable')
        if (event.sessionId != claims['sid'] or event.properties.jurisdiction != claims['jurisdiction']
                or event.properties.environment != claims['environment']
                or not isinstance(event.userId, str) or not hmac.compare_digest(event.userId, expected_user)):
            raise HTTPException(403, 'Telemetry context mismatch')
    logger.info('Telemetry received count=%d event_types=%s', len(payload.events),
                ','.join(sorted({event.event_type for event in payload.events})))
    return TelemetryReceipt(received=len(payload.events))
