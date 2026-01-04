import json
import sys

import pytest

from scripts import gha_monitor


def test_default_repo_parses_https(monkeypatch):
    monkeypatch.setattr(gha_monitor, "git", lambda args: "https://github.com/owner/repo.git")
    assert gha_monitor.default_repo() == "owner/repo"


def test_default_repo_parses_ssh(monkeypatch):
    monkeypatch.setattr(gha_monitor, "git", lambda args: "git@github.com:owner/repo.git")
    assert gha_monitor.default_repo() == "owner/repo"


def test_require_token_missing(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        gha_monitor.require_token()


def test_latest_run_returns_first(monkeypatch):
    monkeypatch.setattr(
        gha_monitor,
        "api_get",
        lambda path, token, params=None: {"workflow_runs": [{"id": 1}, {"id": 2}]},
    )
    assert gha_monitor.latest_run("owner/repo", "main", "t") == {"id": 1}


def test_store_run(tmp_path, monkeypatch):
    gha_monitor.STATE_DIR = tmp_path
    gha_monitor.STATE_FILE = tmp_path / "latest_run.json"
    gha_monitor.store_run({"id": 42, "status": "queued", "conclusion": None})
    data = json.loads((tmp_path / "latest_run.json").read_text())
    assert data["id"] == 42


def test_default_branch(monkeypatch):
    monkeypatch.setattr(gha_monitor, "git", lambda args: "main")
    assert gha_monitor.default_branch() == "main"


def test_require_token_success(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert gha_monitor.require_token() == "t"


def test_git_wrapper(monkeypatch):
    monkeypatch.setattr(gha_monitor.subprocess, "check_output", lambda cmd, text=True: "value")
    assert gha_monitor.git(["echo"]) == "value"


def test_watch_run_success(monkeypatch):
    calls = iter(
        [
            {"status": "in_progress", "conclusion": None},
            {"status": "completed", "conclusion": "success"},
        ]
    )
    monkeypatch.setattr(gha_monitor, "api_get", lambda *_, **__: next(calls))
    monkeypatch.setattr(gha_monitor, "time", type("T", (), {"sleep": lambda self, x: None})())
    gha_monitor.watch_run("owner/repo", 1, "t", interval=0)


def test_watch_run_failure(monkeypatch):
    calls = iter(
        [
            {"status": "in_progress", "conclusion": None},
            {"status": "completed", "conclusion": "failure"},
        ]
    )
    monkeypatch.setattr(gha_monitor, "api_get", lambda *_, **__: next(calls))
    monkeypatch.setattr(gha_monitor, "time", type("T", (), {"sleep": lambda self, x: None})())
    with pytest.raises(SystemExit):
        gha_monitor.watch_run("owner/repo", 1, "t", interval=0)
