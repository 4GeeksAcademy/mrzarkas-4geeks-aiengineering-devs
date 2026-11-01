"""Observe existing health checks without adding probes or changing responses."""
from time import monotonic
from uuid import uuid4

from app.telemetry.health_cache_producer import STATE_KEY, capture_health
from app.telemetry.request_completion import REQUEST_ID_KEY


class HealthCompletionMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        state = scope.setdefault('state', {})
        state.pop(STATE_KEY, None)
        started, complete = monotonic(), False

        async def observed_send(message):
            nonlocal complete
            await send(message)
            if message['type'] == 'http.response.body' and not message.get('more_body', False) and not complete:
                complete = True
                descriptor = state.pop(STATE_KEY, None)
                if descriptor is not None:
                    try:
                        capture_health(*descriptor, max(0, (monotonic() - started) * 1000),
                                       state.get(REQUEST_ID_KEY) or uuid4())
                    except Exception:
                        pass
        try:
            await self.app(scope, receive, observed_send)
        finally:
            state.pop(STATE_KEY, None)
