"""Measure completed responses without changing HTTP messages or error handling."""
from datetime import UTC, datetime
from time import monotonic
from uuid import uuid4

from app.telemetry.request_producer import STATE_KEY, GENERAL_STATE_KEY, AUTH_GENERAL_STATE_KEY, capture_request, capture_general_request, capture_authenticated_general_request


REQUEST_ID_KEY = 'healthcore_telemetry_request_id'


class RequestCompletionMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        state = scope.setdefault('state', {})
        state.pop(STATE_KEY, None)
        state.pop(GENERAL_STATE_KEY, None)
        state.pop(AUTH_GENERAL_STATE_KEY, None)
        started, request_id = monotonic(), uuid4()
        state[REQUEST_ID_KEY] = request_id
        status, complete = None, False

        async def observed_send(message):
            nonlocal status, complete
            await send(message)
            if message['type'] == 'http.response.start':
                status = message['status']
            elif message['type'] == 'http.response.body' and not message.get('more_body', False) and not complete:
                complete = True
                descriptor = state.pop(STATE_KEY, None)
                general_route = state.pop(GENERAL_STATE_KEY, None)
                authenticated = state.pop(AUTH_GENERAL_STATE_KEY, None)
                if descriptor is not None and status is not None:
                    try:
                        capture_request(*descriptor, request_id, status,
                                        max(0, (monotonic() - started) * 1000), datetime.now(UTC).isoformat())
                    except Exception:
                        pass
                elif authenticated is not None and status is not None:
                    try:
                        capture_authenticated_general_request(*authenticated, request_id, status,
                            max(0, (monotonic() - started) * 1000), datetime.now(UTC).isoformat())
                    except Exception:
                        pass
                elif general_route is not None and status is not None:
                    try:
                        capture_general_request(general_route, request_id, status,
                            max(0, (monotonic() - started) * 1000), datetime.now(UTC).isoformat())
                    except Exception:
                        pass

        try:
            await self.app(scope, receive, observed_send)
        finally:
            state.pop(STATE_KEY, None)
            state.pop(GENERAL_STATE_KEY, None)
            state.pop(AUTH_GENERAL_STATE_KEY, None)
            state.pop(REQUEST_ID_KEY, None)
