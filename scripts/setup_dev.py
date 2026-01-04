"""Local hybrid dev convenience helpers."""

import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def main() -> None:
    """Create SSH config entry and optional mutagen sync."""
    console.rule("[bold blue]Hybrid Dev Setup")
    alias = Prompt.ask("Project Alias", default="epyc")
    ip = Prompt.ask("Remote IP")
    user = Prompt.ask("Remote User", default="ubuntu")

    config_path = Path("~/.ssh/config").expanduser()
    entry = f"\nHost {alias}\n    HostName {ip}\n    User {user}\n    ForwardAgent yes\n"

    if Confirm.ask(f"Add {alias} to ~/.ssh/config?"):
        with config_path.open("a", encoding="utf-8") as file:
            file.write(entry)

    mutagen_path = shutil.which("mutagen")
    if mutagen_path and Confirm.ask("Start Sync?"):
        subprocess.run(  # noqa: S603
            [mutagen_path, "sync", "terminate", "cpp-hybrid"],
            check=False,
            stderr=subprocess.DEVNULL,
        )
        cmd = [
            mutagen_path,
            "sync",
            "create",
            "--name",
            "cpp-hybrid",
            "--mode",
            "two-way-safe",
            "--ignore",
            "build/",
            "--ignore",
            ".pixi/",
            ".",
            f"{alias}:/home/{user}/workspace/cpp-project",
        ]
        subprocess.run(cmd, check=False)  # noqa: S603


if __name__ == "__main__":
    main()
