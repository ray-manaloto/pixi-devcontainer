import os
import shutil
import subprocess

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def main() -> None:
    console.rule("[bold blue]Hybrid Dev Setup")
    alias = Prompt.ask("Project Alias", default="epyc")
    ip = Prompt.ask("Remote IP")
    user = Prompt.ask("Remote User", default="ubuntu")

    config_path = os.path.expanduser("~/.ssh/config")
    entry = f"\nHost {alias}\n    HostName {ip}\n    User {user}\n    ForwardAgent yes\n"

    if Confirm.ask(f"Add {alias} to ~/.ssh/config?"):
        with open(config_path, "a", encoding="utf-8") as f:
            f.write(entry)

    if shutil.which("mutagen") and Confirm.ask("Start Sync?"):
        subprocess.run(["mutagen", "sync", "terminate", "cpp-hybrid"], stderr=subprocess.DEVNULL)  # noqa: S607
        cmd = [
            "mutagen",
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
        subprocess.run(cmd)  # noqa: S603


if __name__ == "__main__":
    main()
