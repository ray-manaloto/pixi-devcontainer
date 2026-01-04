from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import validate


def test_ensure_hadolint_present(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)
    assert validate.ensure_hadolint() is True


def test_ensure_hadolint_download_success(monkeypatch, tmp_path):
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    monkeypatch.setattr(validate.platform, "system", lambda: "Linux")
    monkeypatch.setattr(validate.platform, "machine", lambda: "x86_64")

    called = {"ran": False}

    def fake_run(cmd, check=True):  # noqa: ARG001
        called["ran"] = True
        dest = Path(cmd[-1]) if isinstance(cmd, list) else None
        if dest:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("bin")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    monkeypatch.setattr(validate.tempfile, "gettempdir", lambda: str(tmp_path))

    assert validate.ensure_hadolint() is True
    assert called["ran"] is True


def test_ensure_hadolint_download_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    monkeypatch.setattr(validate.platform, "system", lambda: "Linux")
    monkeypatch.setattr(validate.platform, "machine", lambda: "x86_64")

    def fake_run(cmd, check=True):  # noqa: ARG001
        raise validate.subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    monkeypatch.setattr(validate.tempfile, "gettempdir", lambda: str(tmp_path))

    assert validate.ensure_hadolint() is False


def test_list_shell_scripts_filters(monkeypatch):
    output = ".pixi/env.sh\nscripts/foo.sh\n\n"
    monkeypatch.setattr(validate.subprocess, "check_output", lambda *_, **__: output)
    assert validate.list_shell_scripts() == ["scripts/foo.sh"]


def test_list_shell_scripts_error(monkeypatch):
    def boom(*_, **__):  # noqa: ARG001
        raise validate.subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr(validate.subprocess, "check_output", boom)
    assert validate.list_shell_scripts() == []


def test_build_checks_with_shells(monkeypatch):
    monkeypatch.setattr(validate, "list_shell_scripts", lambda: ["scripts/foo.sh"])
    checks = validate.build_checks()
    names = [c[0] for c in checks]
    assert "ShellCheck" in names
    assert names[-1] == "Semgrep"


def test_build_checks_without_shells(monkeypatch):
    monkeypatch.setattr(validate, "list_shell_scripts", lambda: [])
    checks = validate.build_checks()
    names = [c[0] for c in checks]
    assert "ShellCheck" not in names
    assert names[-1] == "Semgrep"


def test_ensure_hadolint_unknown_platform(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    monkeypatch.setattr(validate.platform, "system", lambda: "Other")
    monkeypatch.setattr(validate.platform, "machine", lambda: "Foo")
    assert validate.ensure_hadolint() is False


def test_run_check_hadolint_missing(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    success, name, out = validate.run_check(("Hadolint", ["hadolint"]))
    assert success is True
    assert "skipped" in out.lower() or "missing" in out.lower()


def test_run_check_exception(monkeypatch):
    def boom(*_, **__):
        raise ValueError("boom")

    monkeypatch.setattr(validate.subprocess, "run", boom)
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)
    success, name, out = validate.run_check(("Other", ["tool"]))
    assert success is False
    assert out == "boom"


def test_run_check_success(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)

    def fake_run(cmd, capture_output=True, text=True):  # noqa: ARG001
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    success, _, out = validate.run_check(("ok", ["echo", "x"]))
    assert success is True
    assert "ok" in out
