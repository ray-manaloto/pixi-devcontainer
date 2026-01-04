"""Initialize container with optional AI agents and hydrated environment."""

import json
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def install_agents() -> None:
    """Install optional AI agent CLIs if available."""
    console.print("🤖 Installing AI Agents...")
    if not shutil.which("claude"):
        # Install Claude Code (Official)
        try:
            subprocess.run(
                ["bash", "-lc", "curl -fsSL https://claude.ai/install.sh | bash"],  # noqa: S607
                check=True,
            )
        except subprocess.CalledProcessError:
            console.print("[yellow]Claude install skipped (Network?)[/yellow]")

    # Install Gemini/OpenCode via Bun (Fast)
    subprocess.run(["bun", "install", "--global", "@google/gemini-cli", "opencode"], check=False)  # noqa: S607


def hydrate_env() -> None:
    """Hydrate shell env from pixi_env.json if present."""
    env_file = Path("/app/pixi_env.json")
    zshrc = Path("~/.zshrc").expanduser()

    if env_file.exists():
        data = json.loads(env_file.read_text(encoding="utf-8"))

        with zshrc.open("a", encoding="utf-8") as f:
            f.write("\n# --- Pixi Hydration ---\n")
            for k, v in data.items():
                if k in ["PATH", "HOME", "HOSTNAME"]:
                    continue
                f.write(f'export {k}="{v}"\n')


def main() -> None:
    """Install agents and hydrate the shell environment."""
    install_agents()
    hydrate_env()
    console.print("[green]✅ Container Initialized![/green]")


if __name__ == "__main__":
    main()
