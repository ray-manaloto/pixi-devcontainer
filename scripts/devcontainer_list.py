"""List devcontainer containers with status, user, and ports."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Any

DOCKER = shutil.which("docker") or "/usr/bin/docker"


def _docker_json(cmd: list[str]) -> dict:
    """Run a docker command and parse JSON output."""
    return json.loads(subprocess.check_output(cmd, text=True))  # noqa: S603


def get_devcontainer_ids() -> list[str]:
    """Return container IDs labeled as devcontainers."""
    raw = subprocess.check_output(  # noqa: S603
        [
            DOCKER,
            "ps",
            "-a",
            "--filter",
            "label=devcontainer.local_folder",
            "--format",
            "{{json .ID}}",
        ],
        text=True,
    )
    return [line.strip().strip('"') for line in raw.splitlines() if line.strip()]


def render_ports(ports: dict[str, Any]) -> str:
    """Render port bindings in a compact string."""
    bindings = []
    for container_port, host in (ports or {}).items():
        if not host:
            continue
        for entry in host:
            host_ip = entry.get("HostIp", "")
            host_port = entry.get("HostPort", "")
            bindings.append(f"{host_ip}:{host_port}->{container_port}")
    return ", ".join(bindings) if bindings else "n/a"


def main() -> None:
    """List devcontainer containers with status, user, and ports."""
    if not shutil.which("docker"):
        sys.stdout.write("docker not found on PATH; cannot list devcontainers\n")
        raise SystemExit(1)

    ids = get_devcontainer_ids()
    if not ids:
        sys.stdout.write("No devcontainer containers found (label=devcontainer.local_folder)\n")
        return

    lines = [
        "name\tstatus\tuser\tports",
    ]
    for cid in ids:
        info = _docker_json([DOCKER, "inspect", cid])
        if not info:
            continue
        entry = info[0]
        name = entry.get("Name", "").lstrip("/")
        state = entry.get("State", {}).get("Status", "unknown")
        user = entry.get("Config", {}).get("User") or "n/a"
        ports = render_ports(entry.get("NetworkSettings", {}).get("Ports") or {})
        lines.append(f"{name}\t{state}\t{user}\t{ports}")

    sys.stdout.write("# Devcontainer containers (docker label=devcontainer.local_folder)\n")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
