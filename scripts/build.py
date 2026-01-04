#!/usr/bin/env python3
"""Build and publish devcontainer images with reproducible hashing."""

import hashlib
import os
import subprocess
from pathlib import Path

import boto3
from rich.console import Console

console = Console()
S3_BUCKET = os.getenv("S3_BUCKET", "my-artifacts")
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
    except (subprocess.CalledProcessError, Exception):
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
    config_hash: str,
    os_name: str,
    env: str,
    tag: str,
) -> None:  # pragma: no cover
    """Upload built images and pixi packs to S3 for later reuse."""
    console.log(f"📤 Uploading artifacts for {tag}...")
    s3 = boto3.client("s3")

    # 1. Docker Save
    img_file = f"{os_name}-{env}.tar"
    subprocess.run(["docker", "save", "-o", img_file, tag], check=True)  # noqa: S603,S607
    s3.upload_file(img_file, S3_BUCKET, f"images/{config_hash}/{img_file}")
    Path(img_file).unlink(missing_ok=True)

    # 2. Pixi Pack Extraction
    pack_file = "environment.tar.gz"
    cid = subprocess.check_output(["docker", "create", tag]).decode().strip()  # noqa: S603,S607
    subprocess.run(["docker", "cp", f"{cid}:/app/environment.tar.gz", pack_file], check=True)  # noqa: S603,S607
    subprocess.run(["docker", "rm", "-v", cid], check=True)  # noqa: S603,S607
    s3.upload_file(pack_file, S3_BUCKET, f"packs/{config_hash}/{os_name}-{env}.tar.gz")
    Path(pack_file).unlink(missing_ok=True)


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

    target = "--push" if os.getenv("CI") else "--load"
    subprocess.run(  # noqa: S603
        ["docker", "buildx", "bake", "-f", "docker/docker-bake.hcl", target],  # noqa: S607
        env=env,
        check=True,
    )

    if os.getenv("CI"):
        for os_n in ["focal", "noble"]:
            for env_n in ["stable"]:
                tag = f"{os.getenv('REGISTRY', 'ghcr.io/my-org/cpp')}:{os_n}-{env_n}-{config_hash}"
                upload_artifacts(config_hash, os_n, env_n, tag)


if __name__ == "__main__":
    main()
