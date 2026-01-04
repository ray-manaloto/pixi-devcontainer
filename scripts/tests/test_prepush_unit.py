"""Unit tests for prepush helper tasks."""

import pytest

from scripts import prepush


def test_run_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure run delegates to subprocess.run with given command."""
    captured: dict[str, list[str]] = {}

    def fake_run(cmd: list[str], *, check: bool = True, cwd: str | None = None) -> None:
        _ = (check, cwd)
        captured["cmd"] = cmd

    monkeypatch.setattr(prepush.subprocess, "run", fake_run)
    prepush.run(["echo", "hi"])
    assert captured["cmd"] == ["echo", "hi"]


def test_ensure_clean_git_clean(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pass clean git state without exiting."""
    monkeypatch.setattr(prepush.subprocess, "check_output", lambda *_, **__: "")
    prepush.ensure_clean_git()
    assert "clean" in capsys.readouterr().out.lower()


def test_ensure_clean_git_dirty(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit when git status shows dirty files."""
    monkeypatch.setattr(prepush.subprocess, "check_output", lambda *_, **__: "M file\n")
    with pytest.raises(SystemExit):
        prepush.ensure_clean_git()
    out = capsys.readouterr().out
    assert "dirty" in out.lower()


def test_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Main should call clean + dependent tasks."""
    monkeypatch.setattr(prepush, "ensure_clean_git", lambda: None)
    calls: list[list[str]] = []
    monkeypatch.setattr(prepush, "run", lambda cmd: calls.append(cmd))
    prepush.main()
    expected_call_count = 2
    assert len(calls) == expected_call_count
