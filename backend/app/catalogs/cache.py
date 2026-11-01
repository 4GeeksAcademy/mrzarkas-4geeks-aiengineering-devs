"""Bounded per-worker JSON TTL cache. Authorization stays in route dependencies."""
from collections import OrderedDict
from dataclasses import dataclass
import asyncio
import hashlib
import json
import time


@dataclass(frozen=True)
class Entry:
    payload: bytes
    expires: float


class CatalogCache:
    def __init__(self, *, clock=time.monotonic, max_entries=256, max_bytes=8 * 1024 * 1024, max_item_bytes=256 * 1024):
        self.clock = clock
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.max_item_bytes = max_item_bytes
        self.entries = OrderedDict()
        self.size = 0
        self.enabled = True
        self.hits = self.misses = self.bypasses = 0
        # Fixed stripe count bounds locks even for arbitrarily many actor keys.
        self.locks = [asyncio.Lock() for _ in range(64)]

    def key(self, namespace, actor, catalog, version, *parameters):
        dimensions = [namespace, 'contract-v1', str(actor.id), actor.role, str(actor.area_id), str(catalog), version, *parameters]
        return hashlib.sha256(json.dumps(dimensions, separators=(',', ':')).encode()).hexdigest()

    def _remove(self, key):
        entry = self.entries.pop(key)
        self.size -= len(entry.payload)

    def get(self, key):
        if not self.enabled:
            self.bypasses += 1
            return None
        entry = self.entries.get(key)
        if entry is None or entry.expires <= self.clock():
            if entry is not None:
                self._remove(key)
            self.misses += 1
            return None
        self.entries.move_to_end(key)
        self.hits += 1
        return json.loads(entry.payload)

    def put(self, key, value, ttl):
        if not self.enabled or ttl <= 0:
            return
        payload = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
        if len(payload) > min(self.max_item_bytes, self.max_bytes):
            self.bypasses += 1
            return
        for existing in list(self.entries):
            if self.entries[existing].expires <= self.clock():
                self._remove(existing)
        if key in self.entries:
            self._remove(key)
        while self.entries and (len(self.entries) >= self.max_entries or self.size + len(payload) > self.max_bytes):
            self._remove(next(iter(self.entries)))
        self.entries[key] = Entry(payload, self.clock() + ttl)
        self.size += len(payload)

    def clear(self):
        self.entries.clear()
        self.size = 0

    async def read(self, key, ttl, load, still_current):
        if not self.enabled:
            self.bypasses += 1
            return await load()
        def lookup():
            try:
                return self.get(key)
            except Exception:
                self.bypasses += 1
                return None
        result = lookup()
        if result is not None:
            return result
        lock = self.locks[int(key[:8], 16) % len(self.locks)]
        try:
            await asyncio.wait_for(lock.acquire(), timeout=2)
        except TimeoutError:
            self.bypasses += 1
            return await load()
        try:
            # Recheck after a concurrent fill without double-counting initial misses.
            previous_hits, previous_misses = self.hits, self.misses
            result = lookup()
            self.hits, self.misses = previous_hits, previous_misses
            if result is not None:
                return result
            result = await load()  # Source failures must propagate unchanged.
            if await still_current():
                try:
                    self.put(key, result, ttl)
                except Exception:
                    self.bypasses += 1
            return result
        finally:
            lock.release()


catalog_cache = CatalogCache()
