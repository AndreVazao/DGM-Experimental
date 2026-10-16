"""Append-only, redacted audit events for governed local operations."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditWriteError(RuntimeError):
    """Raised when an audit event cannot be durably appended."""


_LOCK = threading.Lock()
_ALLOWED_EVENTS = {"command.requested", "command.completed", "command.denied"}


def _audit_path() -> Path:
    configured = os.getenv("DGM_COMMAND_AUDIT_PATH")
    if configured:
        return Path(configured).expanduser()
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "DGM-MAT" / "audit" / "command-audit.jsonl"
    # Explicitly local per-user fallback for non-Windows development/test environments.
    return Path.home() / ".dgm-mat" / "audit" / "command-audit.jsonl"


def append_command_audit(
    *,
    event: str,
    command_id: str,
    status: str,
    session_id: str | None = None,
    duration_ms: int | None = None,
    returncode: int | None = None,
) -> None:
    """Append only low-sensitivity metadata; never store stdout, stderr, tokens, or target paths."""
    if event not in _ALLOWED_EVENTS:
        raise ValueError("Unsupported audit event.")
    if not command_id or len(command_id) > 100:
        raise ValueError("Invalid command identifier.")
    if not status or len(status) > 40:
        raise ValueError("Invalid audit status.")
    record: dict[str, Any] = {
        "schema": "dgm-mat.command-audit.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "event": event,
        "command_id": command_id,
        "status": status,
        "session_id": session_id if isinstance(session_id, str) and len(session_id) <= 128 else None,
        "duration_ms": max(0, int(duration_ms)) if duration_ms is not None else None,
        "returncode": int(returncode) if returncode is not None else None,
    }
    encoded = json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n"
    path = _audit_path()
    try:
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
    except (OSError, ValueError) as exc:
        raise AuditWriteError("Could not persist command audit event.") from exc
