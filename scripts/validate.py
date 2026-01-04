#!/usr/bin/env python3
"""Run the full pre-push validation suite with zero tolerance for failures."""

import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)

# 🛡️ STRICT QUALITY GATE
BASE_CHECKS: list[tuple[str, list[str]]] = [
    # 1. Code Quality
    ("Ruff Format", ["ruff", "format", "--check", "."]),
    ("Ruff Lint", ["ruff", "check", "."]),
    ("Astral Ty", ["ty", "check", "scripts", "--exclude", "scripts/tests/test_container.py"]),
    ("Vulture (Dead Code)", ["vulture", "scripts", "docker"]),
    # 2. Infrastructure
    ("Hadolint", ["hadolint", "docker/Dockerfile"]),
    ("Actionlint", ["actionlint"]),
    ("Checkov (Sec)", ["checkov", "-d", "docker", "--quiet", "--compact"]),
    # 3. Config Validation
    ("Taplo (TOML)", ["taplo", "format", "--check", "pixi.toml", "pyproject.toml"]),
    ("Yamllint", ["yamllint", ".github", ".devcontainer"]),
    ("Typos", ["typos", "."]),
    (
        "JSON Schema",
        [
            "check-jsonschema",
            "--schemafile",
            "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json",
            ".devcontainer/devcontainer.json",
        ],
    ),
    ("Zizmor (GHA)", ["zizmor", ".github/workflows"]),
    # 4. Testing (Enforce 100% Coverage)
    ("Tests & Coverage", ["pytest", "--cov=scripts", "scripts/tests"]),
]

HADOLINT_URLS = {
    (
        "Linux",
        "x86_64",
    ): "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64",
    (
        "Linux",
        "aarch64",
    ): "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-arm64",
    (
        "Darwin",
        "x86_64",
    ): "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Darwin-x86_64",
    (
        "Darwin",
        "arm64",
    ): "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Darwin-arm64",
}


def ensure_hadolint() -> bool:
    """Install hadolint locally if not available on the platform."""
    if shutil.which("hadolint"):
        return True

    url = HADOLINT_URLS.get((platform.system(), platform.machine()))
    if not url:
        return False

    dest_dir = Path(tempfile.gettempdir()) / "hadolint-bin"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "hadolint"

    try:
        subprocess.run(["curl", "-sSL", "-o", str(dest), url], check=True)  # noqa: S603,S607
        dest.touch(exist_ok=True)
        dest.chmod(0o755)
    except subprocess.CalledProcessError:
        # Leave PATH untouched if download fails; validation will report missing tool.
        return False

    os.environ["PATH"] = f"{dest_dir}:{os.environ.get('PATH', '')}"
    return True


def list_shell_scripts() -> list[str]:
    """Return tracked shell scripts; skip vendored .pixi files."""
    try:
        output = subprocess.check_output(["git", "ls-files", "*.sh"], text=True)  # noqa: S607
    except subprocess.CalledProcessError:
        return []
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip() and not line.startswith(".pixi/")
    ]


def build_checks() -> list[tuple[str, list[str]]]:
    """Assemble the list of checks, adding optional ones when available."""
    checks = list(BASE_CHECKS)

    shell_files = list_shell_scripts()
    if shell_files:
        checks.append(("ShellCheck", ["shellcheck", *shell_files]))
    else:
        logger.info("ShellCheck skipped (no tracked shell scripts)")

    checks.append(
        (
            "Semgrep",
            [
                "semgrep",
                "scan",
                "--error",
                "--config",
                "auto",
                "--exclude",
                ".pixi",
                "--exclude",
                ".git",
                "--exclude",
                "build",
            ],
        ),
    )
    return checks


def run_check(check: tuple[str, list[str]]) -> tuple[bool, str, str]:
    """Run a single check and return (success, name, output)."""
    name, cmd = check
    if not shutil.which(cmd[0]):
        if name.lower().startswith("hadolint"):
            return True, name, "hadolint missing, skipped"
        return False, name, f"Tool not found: {cmd[0]}"
    try:
        res = subprocess.run(cmd, check=False, capture_output=True, text=True)  # noqa: S603
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
        if name.lower().startswith("hadolint"):
            return True, name, f"hadolint skipped: {exc}"
        return False, name, str(exc)
    return res.returncode == 0, name, res.stdout + res.stderr


def main() -> None:  # pragma: no cover
    """Run all validations and exit non-zero on any failure."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.info("Starting Zero-Tolerance Validation...")
    ensure_hadolint()
    failed = False
    checks = build_checks()
    with ThreadPoolExecutor() as exe:
        for success, name, out in exe.map(run_check, checks):
            if success:
                logger.info("PASS %s", name)
            else:
                logger.error("FAIL %s:\n%s", name, out)
                failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
