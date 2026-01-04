#!/usr/bin/env python3
"""Entrypoint: load pixi env file if present, then exec the requested command."""

import json
import os
import sys
from pathlib import Path


def main() -> None:
    """Load pixi env JSON if present and exec the provided command."""
    env_file = Path("/app/pixi_env.json")
    if env_file.exists():
        with env_file.open() as file:
            os.environ.update(json.load(file))

    args = sys.argv[1:] or ["/bin/bash"]
    try:
        os.execvpe(args[0], args, os.environ)  # noqa: S606
    except FileNotFoundError as exc:
        sys.exit(f"Error: Command '{args[0]}' not found. ({exc})")


if __name__ == "__main__":
    main()
