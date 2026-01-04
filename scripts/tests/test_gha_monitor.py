"""Unit tests for GitHub Actions monitor utilities."""

import json
from pathlib import Path

import pytest

from scripts import gha_monitor


def test_default_repo_parses_https(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse owner/repo from https remote."""
    monkeypatch.setattr(gha_monitor, "git", lambda *_args: "https://github.com/owner/repo.git")
    assert gha_monitor.default_repo() == "owner/repo"


def test_default_repo_parses_ssh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse owner/repo from ssh remote."""
    monkeypatch.setattr(gha_monitor, "git", lambda *_args: "git@github.com:owner/repo.git")
    assert gha_monitor.default_repo() == "owner/repo"


def test_require_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exit when no token configured."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        gha_monitor.require_token()


def test_latest_run_returns_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return first workflow run from API response."""
    monkeypatch.setattr(
        gha_monitor,
        "api_get",
        lambda *_args, **_kwargs: {"workflow_runs": [{"id": 1}, {"id": 2}]},
    )
    assert gha_monitor.latest_run("owner/repo", "main", "t") == {"id": 1}


def test_store_run(tmp_path: Path) -> None:
    """Persist latest run metadata to disk."""
    gha_monitor.STATE_DIR = tmp_path
    gha_monitor.STATE_FILE = tmp_path / "latest_run.json"
    run_id = 42
    gha_monitor.store_run({"id": run_id, "status": "queued", "conclusion": None})
    data = json.loads((tmp_path / "latest_run.json").read_text())
    assert data["id"] == run_id


def test_default_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default branch is current HEAD."""
    monkeypatch.setattr(gha_monitor, "git", lambda *_args: "main")
    assert gha_monitor.default_branch() == "main"


def test_require_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return token when set."""
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert gha_monitor.require_token() == "t"


def test_git_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrap git command execution."""
    monkeypatch.setattr(gha_monitor.subprocess, "check_output", lambda *_args, **_kwargs: "value")
    assert gha_monitor.git(["echo"]) == "value"


def test_watch_run_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Succeed when watched run completes successfully."""
    calls = iter(
        [
            {"status": "in_progress", "conclusion": None},
            {"status": "completed", "conclusion": "success"},
        ],
    )
    monkeypatch.setattr(gha_monitor, "api_get", lambda *_, **__: next(calls))
    monkeypatch.setattr(
        gha_monitor,
        "time",
        type("T", (), {"sleep": lambda *_args, **_kwargs: None})(),
    )
    gha_monitor.watch_run("owner/repo", 1, "t", interval=0)


def test_watch_run_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exit non-zero when watched run fails."""
    calls = iter(
        [
            {"status": "in_progress", "conclusion": None},
            {"status": "completed", "conclusion": "failure"},
        ],
    )
    monkeypatch.setattr(gha_monitor, "api_get", lambda *_, **__: next(calls))
    monkeypatch.setattr(
        gha_monitor,
        "time",
        type("T", (), {"sleep": lambda *_args, **_kwargs: None})(),
    )
    with pytest.raises(SystemExit):
        gha_monitor.watch_run("owner/repo", 1, "t", interval=0)
