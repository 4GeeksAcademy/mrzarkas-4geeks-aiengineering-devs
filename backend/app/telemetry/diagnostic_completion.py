"""Observe schema-error completion without inspecting rejected input."""
from uuid import uuid4

from app.telemetry.diagnostic_producer import STATE_KEY, capture_contract_rejection
from app.telemetry.request_completion import REQUEST_ID_KEY


class DiagnosticCompletionMiddleware:
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
                marked = state.pop(STATE_KEY, None)
                if marked and status == 422:
                    try:
                        capture_contract_rejection(state.get(REQUEST_ID_KEY) or uuid4())
                    except Exception:
                        pass
        try:
            await self.app(scope, receive, observed_send)
        finally:
            state.pop(STATE_KEY, None)
