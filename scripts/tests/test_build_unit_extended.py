from scripts import build


def test_get_remote_digest_parses_sha(monkeypatch):
    output = "sha256:abc123\n"
    monkeypatch.setattr(build.subprocess, "check_output", lambda *_, **__: output)
    assert build.get_remote_digest("img") == "sha256:abc123"


def test_get_remote_digest_handles_exception(monkeypatch):
    def boom(*_, **__):
        raise ValueError("fail")

    monkeypatch.setattr(build.subprocess, "check_output", boom)
    assert build.get_remote_digest("img") == "latest"


def test_get_remote_digest_no_sha(monkeypatch):
    monkeypatch.setattr(build.subprocess, "check_output", lambda *_, **__: "no digest here")
    assert build.get_remote_digest("img") == "latest"


def test_calculate_hash(tmp_path, monkeypatch):
    files = {
        "pixi.lock": "a",
        "pixi.toml": "b",
    }
    for path, content in files.items():
        full = tmp_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)

    monkeypatch.chdir(tmp_path)
    digest = build.calculate_hash({"focal": "sha256:x", "noble": "sha256:y"})
    assert len(digest) == 12
