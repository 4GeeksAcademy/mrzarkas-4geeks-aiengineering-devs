"""Bounded authenticated ingress for declared UI selection/start gestures."""
import asyncio
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.auth.dependencies import Actor, get_current_actor
from app.auth.security import decode_access_token
from app.telemetry.router import SafeTelemetryRoute, TelemetryError
from app.telemetry.identity import region_settings
from app.telemetry.inventory_flow_identity import resolve_flow, issue_flow
from app.telemetry.inventory_flow_producer import capture_flow
from app.inventory.flow_lifecycle import record


class FlowRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['product_selected', 'order_started', 'activity', 'confirmation']
    clinicId: UUID
    itemId: UUID
    direction: Literal['inbound', 'outbound'] | None = None
    flowId: str | None = Field(default=None, pattern=r'^ps_[0-9a-f]{64}$')
    flowToken: str | None = Field(default=None, max_length=4096)

    @model_validator(mode='after')
    def action_direction(self):
        if self.action in {'activity','confirmation'}:
            if self.flowId is None or self.direction is not None or self.flowToken is not None:
                raise ValueError('Lifecycle requires existing flowId only')
            return self
        if self.flowId is not None:
            raise ValueError('Flow identity is server assigned')
        if (self.action == 'order_started') != (self.direction is not None):
            raise ValueError('Direction does not match gesture')
        return self


class FlowResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    accepted: bool
    flowId: str
    flowToken: str
    expiresAt: str


router = APIRouter(prefix='/telemetry', tags=['telemetry'], route_class=SafeTelemetryRoute,
    responses={code: {'model': TelemetryError} for code in [401, 403, 404, 409, 413, 422, 503]})


@router.post('/inventory-flow', response_model=FlowResponse)
async def inventory_flow(payload: FlowRequest, request: Request, actor: Actor = Depends(get_current_actor)):
    from app.telemetry import incident_producer
    service = incident_producer._producer
    if service is None or service.closed:
        raise HTTPException(503, 'Telemetry unavailable')
    count = getattr(service, 'flow_preparations', 0)
    if count >= 16:
        raise HTTPException(503, 'Telemetry unavailable')
    service.flow_preparations = count + 1
    try:
        try:
            region = await asyncio.wait_for(resolve_flow(actor, payload.clinicId, payload.itemId, 'order_started' if payload.action in {'activity','confirmation'} else payload.action), timeout=.1)
        except ValueError:
            raise HTTPException(404, 'Inventory flow unavailable') from None
        settings = region_settings(service.settings, region)
        if payload.action in {'activity','confirmation'}:
            try:
                accepted = await asyncio.wait_for(record(actor,payload.clinicId,payload.itemId,settings,
                    payload.flowId,payload.action,None), timeout=.1)
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(503, 'Telemetry unavailable') from None
            return FlowResponse(accepted=accepted,flowId=payload.flowId,flowToken='',expiresAt=datetime.now(UTC).isoformat())
        expiry = decode_access_token(request.headers['authorization'].split(' ', 1)[1]).get('exp')
        if not isinstance(expiry, int) or isinstance(expiry, bool):
            raise HTTPException(401, 'Authentication required')
        flow_id, token, expires = issue_flow(settings, actor, payload.clinicId, payload.itemId,
            payload.direction, expiry, payload.flowToken)
        try:
            recorded = await asyncio.wait_for(record(actor,payload.clinicId,payload.itemId,settings,
                flow_id,payload.action,payload.direction),timeout=.1)
        except HTTPException:
            raise
        except Exception:
            recorded = False
        accepted = recorded and capture_flow(service, settings, actor, payload.clinicId, payload.action, flow_id, payload.direction)
        return FlowResponse(accepted=accepted, flowId=flow_id, flowToken=token,
            expiresAt=datetime.fromtimestamp(expires, UTC).isoformat())
    finally:
        service.flow_preparations -= 1
