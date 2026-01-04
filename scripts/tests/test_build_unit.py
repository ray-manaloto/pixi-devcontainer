"""Unit tests for build helper utilities."""

import subprocess
from pathlib import Path

import pytest

from scripts import build


def test_get_remote_digest_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return parsed digest when docker output contains sha."""
    expected = "sha256:" + ("a" * 64)

    def fake_check_output(cmd: list[str], *, text: bool = True) -> str:
        _ = text
        assert "imagetools" in cmd
        assert "--format" in cmd
        return expected

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert build.get_remote_digest("ghcr.io/example") == expected


def test_get_remote_digest_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return latest when docker inspection fails."""

    def fake_check_output(cmd: list[str], *, text: bool = True) -> str:
        _ = text
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert build.get_remote_digest("ghcr.io/example") == "latest"


def test_calculate_hash_depends_on_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Hash should change when tracked files change."""
    # Create dummy files expected by calculate_hash
    for filename in ["pixi.lock", "pixi.toml", "docker/Dockerfile", "docker/docker-bake.hcl"]:
        path = tmp_path / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(filename, encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    base_digests = {"focal": "digest1", "noble": "digest2"}
    first = build.calculate_hash(base_digests)

    # Changing a file should change the hash
    (tmp_path / "pixi.toml").write_text("pixi.toml-updated", encoding="utf-8")
    second = build.calculate_hash(base_digests)

    expected_length = 12
    assert len(first) == expected_length
    assert len(second) == expected_length
    assert first != second
