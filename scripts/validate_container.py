#!/usr/bin/env python3
"""Validate devcontainer builds and runs correctly with all tools."""

import subprocess
import sys
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

console = Console()

EXPECTED_TOOLS = [
    ("gcc", "--version", "gcc"),
    ("g++", "--version", "g++"),
    ("clang", "--version", "clang version"),
    ("clang++", "--version", "clang version"),
    ("clang-format", "--version", "clang-format version"),
    ("clang-tidy", "--version", "LLVM"),
    ("ld.lld", "--version", "LLD"),
    ("cmake", "--version", "cmake version"),
    ("ninja", "--version", ""),
    ("python", "--version", "Python"),
]


@dataclass
class ToolResult:
    """Result of a tool validation within the container."""

    name: str
    version: str
    success: bool
    error: str = ""


def run_cmd(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and capture output."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)  # noqa: S603


def get_tool_version(container_id: str, tool: str, args: str, expected: str) -> ToolResult:
    """Execute a tool inside the container and validate its output."""
    result = run_cmd(
        [
            "docker",
            "exec",
            container_id,
            "/app/python_runtime",
            "/app/entrypoint.py",
            tool,
            args,
        ],
        check=False,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        return ToolResult(name=tool, version="", success=False, error=output[:100])

    version_line = output.strip().split("\n")[0]
    if expected and expected not in version_line:
        return ToolResult(
            name=tool,
            version=version_line,
            success=False,
            error="unexpected version string",
        )
    return ToolResult(name=tool, version=version_line, success=True)


def build_image() -> bool:
    """Build the devcontainer image for validation."""
    console.print("\n[bold cyan]Building devcontainer image...[/]")
    result = run_cmd(
        [
            "docker",
            "buildx",
            "build",
            "--load",
            "-f",
            "docker/Dockerfile",
            "--build-arg",
            "BASE_IMAGE=ghcr.io/prefix-dev/pixi:noble",
            "--build-arg",
            "PIXI_ENV=stable",
            "--build-arg",
            "PIXIPACK_PLATFORM=linux-64",
            "-t",
            "cpp-devcontainer:validation",
            ".",
        ],
        check=False,
    )
    if result.returncode != 0:
        console.print(f"[red]Build failed:[/]\n{result.stderr}")
        return False
    console.print("[green]✓ Image built successfully[/]")
    return True


def start_container() -> str | None:
    """Start the validation container and return its ID."""
    console.print("\n[bold cyan]Starting container...[/]")
    result = run_cmd(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            "cpp-validation-test",
            "--entrypoint",
            "/bin/sh",
            "cpp-devcontainer:validation",
            "-c",
            "sleep 300",
        ],
        check=False,
    )
    if result.returncode != 0:
        console.print(f"[red]Failed to start container:[/]\n{result.stderr}")
        return None
    container_id = result.stdout.strip()
    console.print(f"[green]✓ Container started: {container_id[:12]}[/]")
    return container_id


def stop_container(container_id: str) -> None:
    """Stop and remove the validation container."""
    run_cmd(["docker", "stop", container_id], check=False)


def validate_tools(container_id: str) -> list[ToolResult]:
    """Validate expected tool versions inside the container."""
    console.print("\n[bold cyan]Validating tools...[/]")
    results = []
    for tool, args, expected in EXPECTED_TOOLS:
        result = get_tool_version(container_id, tool, args, expected)
        results.append(result)
    return results


def print_results(results: list[ToolResult]) -> bool:
    """Render a results table and return True if all passed."""
    table = Table(title="Tool Validation Results")
    table.add_column("Tool", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="bold")

    all_passed = True
    for r in results:
        status = "[green]✓ PASS[/]" if r.success else "[red]✗ FAIL[/]"
        version = r.version if r.success else r.error
        table.add_row(r.name, version[:60], status)
        if not r.success:
            all_passed = False

    console.print(table)
    return all_passed


def main() -> int:
    """Entrypoint for devcontainer validation."""
    console.rule("[bold blue]Devcontainer Validation")

    if not build_image():
        return 1

    container_id = start_container()
    if not container_id:
        return 1

    try:
        results = validate_tools(container_id)
        success = print_results(results)

        console.print()
        if success:
            console.print("[bold green]✓ All validations passed![/]")
            return 0
        console.print("[bold red]✗ Some validations failed[/]")
        return 1
    finally:
        console.print("\n[dim]Cleaning up...[/]")
        stop_container(container_id)


if __name__ == "__main__":
    sys.exit(main())
