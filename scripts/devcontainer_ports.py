"""Enumerate devcontainer permutations and suggest SSH ports."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def parse_matrix(file_path: Path) -> tuple[list[str], list[str]]:
    """Parse os/env matrix from docker-bake.hcl with a lightweight regex."""
    text = file_path.read_text(encoding="utf-8")
    os_match = re.search(r"os\s*=\s*\[([^\]]+)\]", text)
    env_match = re.search(r"env\s*=\s*\[([^\]]+)\]", text)
    os_values = (
        [part.strip().strip('"') for part in os_match.group(1).split(",") if part.strip()]
        if os_match
        else []
    )
    env_values = (
        [part.strip().strip('"') for part in env_match.group(1).split(",") if part.strip()]
        if env_match
        else []
    )
    return os_values, env_values


def main() -> None:
    """Emit devcontainer permutations with suggested SSH ports."""
    bake_file = Path("docker/docker-bake.hcl")
    if not bake_file.exists():
        msg = "docker/docker-bake.hcl not found"
        raise SystemExit(msg)

    os_values, env_values = parse_matrix(bake_file)
    if not os_values or not env_values:
        msg = "Could not parse os/env matrix from docker/docker-bake.hcl"
        raise SystemExit(msg)

    base_port = 2222
    lines = []
    port = base_port
    for os_name in os_values:
        for env_name in env_values:
            target = f"{os_name}-{env_name}"
            lines.append(f"{target}\tssh_port={port}")
            port += 1

    sys.stdout.write("# Devcontainer permutations and SSH port suggestions (mac host)\n")
    sys.stdout.write(f"# Count: {len(lines)}, base port: {base_port}\n")
    for line in lines:
        sys.stdout.write(f"{line}\n")


if __name__ == "__main__":
    main()
