from types import SimpleNamespace

from scripts import validate


def test_run_check_pass(monkeypatch):  # noqa: S101
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)

    def fake_run(cmd, capture_output=True, text=True):  # noqa: ARG001
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    success, name, out = validate.run_check(("ok", ["echo"]))
    assert success is True
    assert name == "ok"
    assert "ok" in out


def test_run_check_missing_tool(monkeypatch):  # noqa: S101
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    success, name, out = validate.run_check(("missing", ["nope"]))
    assert success is False
    assert name == "missing"
    assert "not found" in out
