"""Extended unit tests for validate module."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import validate


def test_ensure_hadolint_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return True when hadolint already installed."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)
    assert validate.ensure_hadolint() is True


def test_ensure_hadolint_download_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Download hadolint successfully when missing."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    monkeypatch.setattr(validate.platform, "system", lambda: "Linux")
    monkeypatch.setattr(validate.platform, "machine", lambda: "x86_64")

    called = {"ran": False}

    def fake_run(cmd: list[str] | str, *, check: bool = True) -> SimpleNamespace:
        _ = check
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


def test_ensure_hadolint_download_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Handle hadolint download failure gracefully."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    monkeypatch.setattr(validate.platform, "system", lambda: "Linux")
    monkeypatch.setattr(validate.platform, "machine", lambda: "x86_64")

    def fake_run(cmd: list[str] | str, *, check: bool = True) -> SimpleNamespace:
        _ = check
        raise validate.subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    monkeypatch.setattr(validate.tempfile, "gettempdir", lambda: str(tmp_path))

    assert validate.ensure_hadolint() is False


def test_list_shell_scripts_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    """Filter out vendored .pixi shell scripts."""
    output = ".pixi/env.sh\nscripts/foo.sh\n\n"
    monkeypatch.setattr(validate.subprocess, "check_output", lambda *_, **__: output)
    assert validate.list_shell_scripts() == ["scripts/foo.sh"]


def test_list_shell_scripts_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return empty list on git error."""

    def boom(*_: object, **__: object) -> None:
        raise validate.subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr(validate.subprocess, "check_output", boom)
    assert validate.list_shell_scripts() == []


def test_build_checks_with_shells(monkeypatch: pytest.MonkeyPatch) -> None:
    """Include ShellCheck when shell scripts are present."""
    monkeypatch.setattr(validate, "list_shell_scripts", lambda: ["scripts/foo.sh"])
    checks = validate.build_checks()
    names = [c[0] for c in checks]
    assert "ShellCheck" in names
    assert names[-1] == "Semgrep"


def test_build_checks_without_shells(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip ShellCheck when no shell scripts tracked."""
    monkeypatch.setattr(validate, "list_shell_scripts", list)
    checks = validate.build_checks()
    names = [c[0] for c in checks]
    assert "ShellCheck" not in names
    assert names[-1] == "Semgrep"


def test_ensure_hadolint_unknown_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return False when platform is unsupported."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    monkeypatch.setattr(validate.platform, "system", lambda: "Other")
    monkeypatch.setattr(validate.platform, "machine", lambda: "Foo")
    assert validate.ensure_hadolint() is False


def test_run_check_hadolint_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gracefully skip hadolint when not installed."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: False)
    success, _name, out = validate.run_check(("Hadolint", ["hadolint"]))
    assert success is True
    assert "skipped" in out.lower() or "missing" in out.lower()


def test_run_check_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return failure when subprocess raises unexpected error."""

    def boom(*_: object, **__: object) -> None:
        msg = "boom"
        raise ValueError(msg)

    monkeypatch.setattr(validate.subprocess, "run", boom)
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)
    success, _name, out = validate.run_check(("Other", ["tool"]))
    assert success is False
    assert out == "boom"


def test_run_check_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return success when command exits 0."""
    monkeypatch.setattr(validate.shutil, "which", lambda _: True)

    def fake_run(
        cmd: list[str] | str,
        *,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        **kwargs: object,
    ) -> SimpleNamespace:
        _ = (cmd, check, capture_output, text, kwargs)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(validate.subprocess, "run", fake_run)
    success, _, out = validate.run_check(("ok", ["echo", "x"]))
    assert success is True
    assert "ok" in out
