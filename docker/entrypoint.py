#!/usr/bin/env python3
import json
import os
import sys


def main() -> None:
    env_file = "/app/pixi_env.json"
    if os.path.exists(env_file):
        with open(env_file) as f:
            os.environ.update(json.load(f))

    args = sys.argv[1:] or ["/bin/bash"]
    try:
        os.execvpe(args[0], args, os.environ)
    except FileNotFoundError:
        sys.exit(f"Error: Command '{args[0]}' not found.")


if __name__ == "__main__":
    main()
