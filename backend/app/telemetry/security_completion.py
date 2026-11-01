"""Capture security descriptors only after the final response is sent."""
from uuid import uuid4

from app.telemetry.request_completion import REQUEST_ID_KEY
from app.telemetry.security_producer import STATE_KEY, capture_security


class SecurityCompletionMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        state = scope.setdefault('state', {})
        state.pop(STATE_KEY, None)
        status, complete = None, False

        async def observed_send(message):
            nonlocal status, complete
            await send(message)
            if message['type'] == 'http.response.start':
                status = message['status']
            elif message['type'] == 'http.response.body' and not message.get('more_body', False) and not complete:
                complete = True
                descriptor = state.pop(STATE_KEY, None)
                if descriptor is not None and status is not None:
                    try:
                        capture_security(descriptor, status, state.get(REQUEST_ID_KEY) or uuid4())
                    except Exception:
                        pass
        try:
            await self.app(scope, receive, observed_send)
        finally:
            state.pop(STATE_KEY, None)
