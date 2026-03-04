"""
Log Handler

In-memory log buffer + SSE streaming for the QLC system.
"""

import logging
import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from typing import AsyncGenerator

MAX_BUFFER = 500

log_buffer: deque = deque(maxlen=MAX_BUFFER)
_subscribers: list = []  # list of (asyncio.Queue, asyncio.AbstractEventLoop)


class MemoryLogHandler(logging.Handler):
    """Logging handler that stores records in memory and notifies SSE subscribers.

    emit() may be called from any thread (e.g. FastAPI sync route threadpool).
    We use loop.call_soon_threadsafe() so that queue operations always happen
    on the correct event-loop thread, making this fully thread-safe.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            }
            log_buffer.append(entry)
            for q, loop in list(_subscribers):
                try:
                    loop.call_soon_threadsafe(q.put_nowait, entry)
                except RuntimeError:
                    # Loop is closed; subscriber will clean itself up
                    pass
        except Exception:
            self.handleError(record)


_handler_instance: MemoryLogHandler | None = None


def get_handler() -> MemoryLogHandler:
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = MemoryLogHandler()
        _handler_instance.setFormatter(logging.Formatter("%(message)s"))
    return _handler_instance


async def log_event_generator(request=None) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted log entries."""
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    loop = asyncio.get_running_loop()
    subscriber = (q, loop)
    _subscribers.append(subscriber)
    try:
        # Replay buffered logs first
        for entry in list(log_buffer):
            yield f"data: {json.dumps(entry)}\n\n"

        # Stream new entries
        while True:
            if request is not None:
                try:
                    disconnected = await request.is_disconnected()
                except Exception:
                    disconnected = False
                if disconnected:
                    break
            try:
                entry = await asyncio.wait_for(q.get(), timeout=25)
                yield f"data: {json.dumps(entry)}\n\n"
            except asyncio.TimeoutError:
                # Keepalive comment
                yield ": ping\n\n"
    finally:
        if subscriber in _subscribers:
            _subscribers.remove(subscriber)
