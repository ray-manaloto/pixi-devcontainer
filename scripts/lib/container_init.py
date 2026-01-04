import json
import os
import shutil
import subprocess

from rich.console import Console

console = Console()


def install_agents() -> None:
    console.print("🤖 Installing AI Agents...")
    if not shutil.which("claude"):
        # Install Claude Code (Official)
        try:
            subprocess.run("curl -fsSL https://claude.ai/install.sh | bash", shell=True, check=True)  # noqa: S602,S607
        except subprocess.CalledProcessError:
            console.print("[yellow]Claude install skipped (Network?)[/yellow]")

    # Install Gemini/OpenCode via Bun (Fast)
    subprocess.run(["bun", "install", "--global", "@google/gemini-cli", "opencode"], check=False)  # noqa: S607


def hydrate_env() -> None:
    env_file = "/app/pixi_env.json"
    zshrc = os.path.expanduser("~/.zshrc")

    if os.path.exists(env_file):
        with open(env_file) as f:
            data = json.load(f)

        with open(zshrc, "a", encoding="utf-8") as f:
            f.write("\n# --- Pixi Hydration ---\n")
            for k, v in data.items():
                if k in ["PATH", "HOME", "HOSTNAME"]:
                    continue
                f.write(f'export {k}="{v}"\n')


def main() -> None:
    install_agents()
    hydrate_env()
    console.print("[green]✅ Container Initialized![/green]")


if __name__ == "__main__":
    main()
