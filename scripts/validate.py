#!/usr/bin/env python3
import shutil
import subprocess
import sys

from rich.console import Console

console = Console()


def run_check(name: str, cmd: list[str]) -> bool:
    console.print(f"\n[bold cyan]Running {name}...[/]")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        console.print(f"[red]✗ {name} failed[/]")
        return False
    console.print(f"[green]✓ {name} passed[/]")
    return True


def main() -> None:  # pragma: no cover
    console.rule("[bold blue]Quality Gate")

    checks = [
        ("Ruff Format Check", ["ruff", "format", "--check", "scripts", "docker"]),
        ("Ruff Lint", ["ruff", "check", "scripts", "docker"]),
        ("Ty Type Check", ["ty", "check", "scripts", "docker"]),
        ("Vulture Dead Code", ["vulture", "scripts", "docker"]),
        ("Typos Spell Check", ["typos", "."]),
        (
            "Pytest (unit)",
            [
                "pytest",
                "--cov=scripts",
                "--cov-report=term-missing",
                "--ignore=scripts/tests/test_container.py",
            ],
        ),
    ]

    optional_checks = [
        ("Hadolint Dockerfile", ["hadolint", "docker/Dockerfile"]),
        ("Actionlint GHA", ["actionlint", ".github/workflows/ci.yml"]),
    ]

    for name, cmd in optional_checks:
        if shutil.which(cmd[0]):
            checks.append((name, cmd))

    failed = []
    for name, cmd in checks:
        if not run_check(name, cmd):
            failed.append(name)

    console.rule("[bold blue]Summary")
    if failed:
        console.print(f"[red]Failed checks: {', '.join(failed)}[/]")
        sys.exit(1)
    else:
        console.print("[green]All checks passed![/]")


if __name__ == "__main__":
    main()
