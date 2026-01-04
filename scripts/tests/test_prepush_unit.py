import sys

import pytest

from scripts import prepush


def test_run_logs(monkeypatch):
    captured = {}

    def fake_run(cmd, check=True, cwd=None):  # noqa: ARG001
        captured["cmd"] = cmd

    monkeypatch.setattr(prepush.subprocess, "run", fake_run)
    prepush.run(["echo", "hi"])
    assert captured["cmd"] == ["echo", "hi"]


def test_ensure_clean_git_clean(monkeypatch, capsys):
    monkeypatch.setattr(prepush.subprocess, "check_output", lambda *_, **__: "")
    prepush.ensure_clean_git()
    assert "clean" in capsys.readouterr().out.lower()


def test_ensure_clean_git_dirty(monkeypatch, capsys):
    monkeypatch.setattr(prepush.subprocess, "check_output", lambda *_, **__: "M file\n")
    with pytest.raises(SystemExit):
        prepush.ensure_clean_git()
    out = capsys.readouterr().out
    assert "dirty" in out.lower()


def test_main(monkeypatch):
    monkeypatch.setattr(prepush, "ensure_clean_git", lambda: None)
    calls = []
    monkeypatch.setattr(prepush, "run", lambda cmd: calls.append(cmd))
    prepush.main()
    assert len(calls) == 2
