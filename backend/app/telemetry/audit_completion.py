"""Observe ASGI completion without changing response messages or error handling."""
from app.telemetry.audit_producer import STATE_KEY, capture_audit
from app.telemetry.inventory_audit_producer import STATE_KEY as INVENTORY_STATE_KEY, capture_inventory_audit


class AuditCompletionMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        state = scope.setdefault('state', {})
        state.pop(STATE_KEY, None)
        state.pop(INVENTORY_STATE_KEY, None)
        status = None
        complete = False

        async def observed_send(message):
            nonlocal status, complete
            await send(message)  # A failed/cancelled send never becomes a completed read.
            if message['type'] == 'http.response.start':
                status = message['status']
            elif message['type'] == 'http.response.body' and not message.get('more_body', False) and not complete:
                complete = True
                descriptor = state.pop(STATE_KEY, None)
                inventory = state.pop(INVENTORY_STATE_KEY, None)
                if status is not None and 200 <= status < 300 and descriptor is not None:
                    try:
                        capture_audit(*descriptor)
                    except Exception:
                        pass  # Telemetry errors never change a delivered business response.
                elif status is not None and 200 <= status < 300 and inventory is not None:
                    try:
                        capture_inventory_audit(*inventory)
                    except Exception:
                        pass

        try:
            await self.app(scope, receive, observed_send)
        finally:
            state.pop(STATE_KEY, None)
            state.pop(INVENTORY_STATE_KEY, None)
