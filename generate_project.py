#!/usr/bin/env python3
"""Generate the C++ project scaffold from the current templates."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Files to materialize in the target directory. The contents are read from this
# repository so the generator stays in sync with the source templates.
TEMPLATE_PATHS = [
    "pixi.toml",
    "pixi.lock",
    "pyproject.toml",
    "renovate.json",
    ".gitignore",
    ".dockerignore",
    ".devcontainer/devcontainer.json",
    ".devcontainer/otel-config.yaml",
    ".github/workflows/ci.yml",
    "docker/Dockerfile",
    "docker/docker-bake.hcl",
    "docker/entrypoint.py",
    "scripts/__init__.py",
    "scripts/build.py",
    "scripts/validate.py",
    "scripts/validate_container.py",
    "scripts/setup_dev.py",
    "scripts/lib/__init__.py",
    "scripts/lib/container_init.py",
    "scripts/tests/__init__.py",
    "scripts/tests/test_build_unit.py",
    "scripts/tests/test_validate_unit.py",
    "scripts/tests/test_container.py",
    "scripts/tests/test_placeholder.py",
]


def load_templates() -> dict[str, str]:
    files: dict[str, str] = {}
    for rel_path in TEMPLATE_PATHS:
        src = BASE_DIR / rel_path
        if not src.exists():
            raise FileNotFoundError(f"Template missing: {src}")
        content = src.read_text(encoding="utf-8").rstrip() + "\n"
        files[rel_path] = content
    return files


def write_files(root: Path, files: dict[str, str]) -> None:
    for rel_path, content in files.items():
        dest = root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print(f"wrote {dest}")


def maybe_lock(root: Path, run_lock: bool) -> None:
    if not run_lock:
        print("Skipping pixi lock generation (requested).")
        return
    if shutil.which("pixi") is None:
        print("pixi not found; skipping pixi lock generation.")
        return
    try:
        print("Generating pixi.lock (stable, automation, dev-container)...")
        subprocess.run(["pixi", "lock"], cwd=root, check=True)  # noqa: S603,S607
    except subprocess.CalledProcessError as exc:
        print(f"pixi lock failed (non-fatal): {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", default="cpp-bleeding-edge", help="Output directory")
    parser.add_argument(
        "--skip-lock",
        action="store_true",
        help="Skip running pixi lock after generation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)

    templates = load_templates()
    write_files(root, templates)
    maybe_lock(root, not args.skip_lock)

    print("\n✅ Project scaffold ready.")
    print(f"cd {root}")
    print("pixi install  # (recreates lock on your platform if needed)")


if __name__ == "__main__":
    main()
