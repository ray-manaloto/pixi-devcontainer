from types import SimpleNamespace

from scripts import validate


def test_run_check_pass(monkeypatch):
    def fake_run(cmd, capture_output=False):  # noqa: ARG001 - match subprocess signature
        _ = capture_output
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    assert validate.run_check("ok", ["echo"]) is True


def test_run_check_fail(monkeypatch):
    def fake_run(cmd, capture_output=False):  # noqa: ARG001 - match subprocess signature
        _ = capture_output
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    assert validate.run_check("fail", ["false"]) is False
