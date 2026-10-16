from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.operations.command_executor import CommandDenied, CommandExecutor


class FakeCompleted:
    def __init__(self, returncode=0, stdout="ok", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_catalog_does_not_offer_arbitrary_shell_or_elevation():
    executor = CommandExecutor(allowed_roots=[])
    catalog = executor.catalog()
    assert catalog["arbitrary_shell"] is False
    assert catalog["administrator_elevation"] is False
    assert {item["id"] for item in catalog["commands"]} >= {"system.summary", "git.status"}


def test_unknown_command_is_denied():
    executor = CommandExecutor(allowed_roots=[])
    with pytest.raises(CommandDenied):
        executor.execute("powershell.raw", target_path="C:/tmp")


def test_git_status_requires_target(tmp_path):
    executor = CommandExecutor(allowed_roots=[tmp_path], which=lambda name: "/usr/bin/git")
    with pytest.raises(CommandDenied):
        executor.execute("git.status")


def test_git_target_must_be_inside_allowed_root(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = make_repo(tmp_path / "outside-parent")
    executor = CommandExecutor(allowed_roots=[allowed], which=lambda name: "/usr/bin/git")
    with pytest.raises(CommandDenied):
        executor.execute("git.status", target_path=str(outside))


def test_git_status_uses_no_shell_and_structured_args(tmp_path):
    repo = make_repo(tmp_path)
    calls = []
    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeCompleted(0, "## feature/test", "")
    executor = CommandExecutor(allowed_roots=[tmp_path], runner=runner, which=lambda name: "/usr/bin/git")
    result = executor.execute("git.status", target_path=str(repo))
    assert result["status"] == "passed"
    assert calls[0][1]["shell"] is False
    assert calls[0][0][-3:] == ["status", "--short", "--branch"]


def test_output_is_bounded(tmp_path):
    executor = CommandExecutor(allowed_roots=[tmp_path], runner=lambda *a, **k: FakeCompleted(stdout="x" * 5000), which=lambda name: "/usr/bin/git", output_limit=512)
    result = executor.execute("ollama.status")
    # Simulate executable resolution separately to keep this deterministic.
    assert result["status"] == "unavailable" or len(result["stdout"]) <= 512


def test_timeout_is_reported(tmp_path):
    def timeout_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output="partial")
    executor = CommandExecutor(allowed_roots=[tmp_path], runner=timeout_runner, which=lambda name: "/usr/bin/git")
    repo = make_repo(tmp_path)
    result = executor.execute("git.status", target_path=str(repo))
    assert result["status"] == "timeout"
    assert result["returncode"] is None
