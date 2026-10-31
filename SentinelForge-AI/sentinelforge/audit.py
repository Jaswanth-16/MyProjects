"""Simple append-only audit log for local operator activity.

Never logs bearer tokens or raw evidence. Set SENTINELFORGE_AUDIT_LOG to enable.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_lock = Lock()


def record(event: str, *, finding_id: str | None = None, source: str | None = None) -> None:
    destination = os.getenv("SENTINELFORGE_AUDIT_LOG")
    if not destination:
        return
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event,
             "finding_id": finding_id, "source": source}
    path = Path(destination)
    with _lock:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, sort_keys=True) + "\n")
