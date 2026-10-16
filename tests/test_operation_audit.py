import json

import pytest

from core.operations.operation_audit import AuditWriteError, append_command_audit


def test_audit_appends_redacted_jsonl_records(tmp_path, monkeypatch):
    path = tmp_path / "audit" / "commands.jsonl"
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(path))
    append_command_audit(
        event="command.requested",
        command_id="system.summary",
        status="requested",
        session_id="session-123",
    )
    append_command_audit(
        event="command.completed",
        command_id="system.summary",
        status="passed",
        session_id="session-123",
        duration_ms=12,
        returncode=0,
    )
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert records[0]["event"] == "command.requested"
    assert records[1]["duration_ms"] == 12
    assert "stdout" not in records[1]
    assert "stderr" not in records[1]
    assert "target_path" not in records[1]
    assert all(record["schema"] == "dgm-mat.command-audit.v1" for record in records)


def test_audit_rejects_unknown_event(tmp_path, monkeypatch):
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    with pytest.raises(ValueError, match="Unsupported audit event"):
        append_command_audit(event="command.secret", command_id="x", status="denied")


def test_audit_fails_closed_when_parent_is_not_writable_file(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(blocker / "audit.jsonl"))
    with pytest.raises(AuditWriteError, match="Could not persist"):
        append_command_audit(event="command.requested", command_id="system.summary", status="requested")
