import subprocess

from scripts import build


def test_get_remote_digest_success(monkeypatch):
    expected = "sha256:" + ("a" * 64)

    def fake_check_output(cmd, text=True):  # noqa: ARG001 - match subprocess signature
        _ = text
        assert "imagetools" in cmd
        assert "--format" in cmd
        return expected

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert build.get_remote_digest("ghcr.io/example") == expected


def test_get_remote_digest_fallback(monkeypatch):
    def fake_check_output(cmd, text=True):  # noqa: ARG001 - match subprocess signature
        _ = text
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert build.get_remote_digest("ghcr.io/example") == "latest"


def test_calculate_hash_depends_on_files(monkeypatch, tmp_path):
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

    assert len(first) == 12
    assert len(second) == 12
    assert first != second
