"""Bounded process-local delivery to the validating, non-persistent stub sink."""
import asyncio
import json
import logging
from collections import deque

from app.telemetry.schemas import EVENT_MODELS, TelemetryBatch, TelemetryReceipt

INCIDENT_EVENTS = frozenset({'incident_created', 'incident_transitioned', 'incident_assigned'})
SERVER_EVENTS = INCIDENT_EVENTS | {'audit_accessed', 'management_mutation_completed', 'api_request_completed',
                                   'authentication_succeeded', 'authentication_failed', 'authorization_denied',
                                   'catalog_cache_observed', 'service_health_checked', 'data_integrity_checked',
                                   'inbound_order_completed', 'outbound_order_completed', 'inventory_adjustment_completed',
                                   'inventory_validation_failed', 'inventory_viewed', 'product_selected', 'order_started',
                                   'inventory_threshold_activated', 'inventory_threshold_cleared', 'stock_direct_update_rejected', 'order_abandoned', 'inventory_reconciliation_failed'}
logger = logging.getLogger('healthcore.telemetry')


async def stub_sink(body):
    batch = TelemetryBatch.model_validate_json(body)
    if any(event.event_type not in SERVER_EVENTS for event in batch.events):
        raise ValueError('Producer unavailable')
    logger.info('Telemetry received count=%d event_types=%s', len(batch.events),
                ','.join(sorted({event.event_type for event in batch.events})))
    return TelemetryReceipt(received=len(batch.events))


class ServerQueue:
    def __init__(self, *, sink=stub_sink, loop=None, allowed_events=None, diagnostic_callback=None):
        self.loop = loop or asyncio.get_running_loop()
        self.sink = sink
        self.allowed_events = SERVER_EVENTS if allowed_events is None else frozenset(allowed_events)
        self.diagnostic_callback = diagnostic_callback
        self.pending = deque()
        self.flight = None
        self.timer = None
        self.task = None
        self.size = 0
        self.closed = False
        self.counts = dict(received=0, rejected=0, discarded=0)

    def _schedule(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if self.closed or self.flight is not None or not self.pending:
            return
        delay = 0 if len(self.pending) >= 20 else max(0, self.pending[0][0] + 10 - self.loop.time())
        self.timer = self.loop.call_later(delay, self._launch)

    def _launch(self):
        self.timer = None
        if not self.closed and self.task is None:
            self.task = self.loop.create_task(self.flush())
            self.task.add_done_callback(self._done)

    def _done(self, task):
        # Always consume task exceptions; a delivery error must not escape into the API.
        if not task.cancelled():
            task.exception()
        if self.task is task:
            self.task = None
        self._schedule()

    def _diagnose(self, event_type, jurisdiction, reason):
        if self.diagnostic_callback is not None:
            try:
                self.diagnostic_callback(event_type, jurisdiction, reason)
            except Exception:
                pass  # A diagnostic failure cannot change queue accounting or recurse.

    def enqueue(self, event, scope):
        failure = ('telemetry_contract_rejected', None, 'schema')
        try:
            if self.closed:
                failure = ('telemetry_delivery_failed', None, 'unavailable')
                raise ValueError('Unavailable')
            if event.get('event_type') not in self.allowed_events or not isinstance(scope, str):
                raise ValueError('Unavailable')
            value = EVENT_MODELS[event['event_type']].model_validate(event)
            body = value.model_dump_json().encode()
            if len(body) > 2048:
                raise ValueError('Invalid event size')
            jurisdiction = value.properties.jurisdiction
            count = len(self.pending) + len(self.flight or [])
            if count >= 200 or self.size + len(body) > 256 * 1024:
                failure = ('telemetry_delivery_failed', jurisdiction, 'queue_full')
                raise ValueError('Queue full')
            # Scope cannot supply jurisdiction; metadata comes only from the validated model.
            self.pending.append((self.loop.time(), scope, body, jurisdiction))
            self.size += len(body)
            self._schedule()
            return True
        except Exception:
            self.counts['rejected'] += 1
            self._diagnose(*failure)
            return False

    async def flush(self):
        if self.closed or self.flight is not None or not self.pending:
            return
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        scope, jurisdiction = self.pending[0][1], self.pending[0][3]
        entries, remaining = [], deque()
        size = len(b'{"events":[]}')
        for entry in self.pending:
            if entry[1] == scope and entry[3] == jurisdiction and len(entries) < 20 and size + len(entry[2]) + 1 <= 48 * 1024:
                entries.append(entry)
                size += len(entry[2]) + 1
            else:
                remaining.append(entry)
        self.pending = remaining
        self.flight = entries
        body = b'{"events":[' + b','.join(entry[2] for entry in entries) + b']}'
        accepted, cancelled, reason = False, False, 'unavailable'
        try:
            receipt = await asyncio.wait_for(self.sink(body), timeout=1)
            accepted = isinstance(receipt, TelemetryReceipt) and receipt.received == len(entries)
        except asyncio.CancelledError:
            cancelled = True
            raise
        except TimeoutError:
            reason = 'timeout'
        except Exception:
            pass  # Count-only diagnostics, no exception text or recursive telemetry.
        finally:
            self.counts['received' if accepted else 'discarded'] += len(entries)
            if not accepted and not cancelled and not self.closed:
                self._diagnose('telemetry_delivery_failed', jurisdiction, reason)
            self.size -= sum(len(entry[2]) for entry in entries)
            self.flight = None
            self._schedule()

    async def close(self):
        self.closed = True
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
            self.task = None
        self.counts['discarded'] += len(self.pending)
        self.pending.clear()
        self.size = 0
