#!/usr/bin/env python3
"""Build and publish devcontainer images with reproducible hashing."""

import hashlib
import os
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()
BASE_IMAGES = {
    "focal": "ghcr.io/prefix-dev/pixi:focal",
    "noble": "ghcr.io/prefix-dev/pixi:noble",
}


def get_remote_digest(image: str) -> str:  # pragma: no cover - external docker call
    """Fetch upstream digest to ensure security updates trigger rebuilds."""
    cmd = [
        "docker",
        "buildx",
        "imagetools",
        "inspect",
        "--format",
        "{{ (index .Manifest.Manifests 0).Digest }}",
        image,
    ]
    try:
        output = subprocess.check_output(cmd, text=True)  # noqa: S603
    except (subprocess.CalledProcessError, ValueError):
        return "latest"

    for line in output.splitlines():
        if "sha256:" not in line:
            continue
        parts = line.strip().split()
        for part in parts:
            if part.startswith("sha256:"):
                return part
    return "latest"


def calculate_hash(digests: dict[str, str]) -> str:
    """Combine file contents and remote digests into a short config hash."""
    hasher = hashlib.sha256()
    for f in ["pixi.lock", "pixi.toml", "docker/Dockerfile", "docker/docker-bake.hcl"]:
        path = Path(f)
        if not path.exists():
            continue
        with path.open("rb") as file:
            hasher.update(file.read())
    for k, v in digests.items():
        hasher.update(f"{k}:{v}".encode())
    return hasher.hexdigest()[:12]


def upload_artifacts(
    *_: str,
) -> None:  # pragma: no cover
    """Skip artifact upload; handled by BuildKit export target."""
    console.log("Artifact upload skipped (handled by artifacts target)", style="yellow")


def main() -> None:  # pragma: no cover
    """Entrypoint for building and optionally publishing images."""
    console.rule("[bold blue]Starting Build")

    digests = {k: get_remote_digest(v) for k, v in BASE_IMAGES.items()}
    config_hash = calculate_hash(digests)
    console.print(f"🔑 Hash: {config_hash}")

    if "GITHUB_OUTPUT" in os.environ:
        output_path = Path(os.environ["GITHUB_OUTPUT"])
        with output_path.open("a", encoding="utf-8") as file:
            file.write(f"HASH={config_hash}\n")

    env = os.environ.copy()
    env.update(
        {
            "CONFIG_HASH": config_hash,
            "DIGEST_FOCAL": digests["focal"],
            "DIGEST_NOBLE": digests["noble"],
        },
    )

    skip_push = os.getenv("CI_SKIP_PUSH") == "1" or os.getenv("SKIP_PUSH") == "1"
    is_ci = bool(os.getenv("CI"))
    push_enabled = is_ci and not skip_push

    base_cmd = ["docker", "buildx", "bake", "-f", "docker/docker-bake.hcl"]

    if push_enabled:
        # CI: push multi-arch images and export artifacts
        subprocess.run(  # noqa: S603
            [*base_cmd, "default", "--push"],
            env=env,
            check=True,
        )
    else:
        # Local or CI with push disabled: load single-arch image only
        subprocess.run(  # noqa: S603
            [
                *base_cmd,
                "image",
                "--load",
                "--set",
                "*.platforms=linux/amd64",
            ],
            env=env,
            check=True,
        )


if __name__ == "__main__":
    main()
