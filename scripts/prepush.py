#!/usr/bin/env python3
"""Pre-push safety gate: require clean git tree, run full validation, dry-run bake."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    """Run a command, streaming output, raising on failure."""
    console.log(f"[cyan]$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)  # noqa: S603,S607


def ensure_clean_git() -> None:
    """Fail fast if the working tree is dirty."""
    result = subprocess.check_output(["git", "status", "--porcelain"], text=True)  # noqa: S603,S607
    if result.strip():
        console.print("[red]❌ Working tree is dirty. Commit or stash changes before pushing.")
        console.print(result)
        sys.exit(1)
    console.print("[green]✅ Git working tree clean")


def main() -> None:
    ensure_clean_git()

    # Run full validation (linters, static analysis, tests).
    console.rule("[bold blue]Validation")
    run([sys.executable, "-m", "scripts.validate"])

    # Dry-run docker bake to catch template errors early.
    console.rule("[bold blue]Docker Bake --print")
    run(["docker", "buildx", "bake", "-f", "docker/docker-bake.hcl", "--print"])

    console.print("[bold green]All pre-push checks passed. Safe to push.")


if __name__ == "__main__":
    main()
