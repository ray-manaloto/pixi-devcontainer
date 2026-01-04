"""Unit tests for validate module helpers."""

from types import SimpleNamespace

import pytest

from scripts import validate


def test_run_check_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate a passing check returns success."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)

    def fake_run(
        cmd: list[str] | str,
        *,
        capture_output: bool = True,
        text: bool = True,
    ) -> SimpleNamespace:
        _ = (cmd, capture_output, text)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    success, name, out = validate.run_check(("ok", ["echo"]))
    assert success is True
    assert name == "ok"
    assert "ok" in out


def test_run_check_missing_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate missing tools fail the check."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    success, name, out = validate.run_check(("missing", ["nope"]))
    assert success is False
    assert name == "missing"
    assert "not found" in out
