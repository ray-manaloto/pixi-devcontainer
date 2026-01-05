This is the Reference Architecture v2026.5 ("Universal Mac-AMD64").It fulfills your requirement to run AMD64 (x86_64) co
ntainers on an Apple Silicon Mac using Docker Desktop's built-in Rosetta 2 emulation. This ensures binary parity with yo
ur remote EPYC server while allowing local development.🍎 Mac AMD64 Emulation StrategyForced Platform: The local DevConta
iner config (.devcontainer/mac-amd64/) explicitly forces "runArgs": ["--platform=linux/amd64"]. This triggers Docker Des
ktop to use Rosetta 2 (which is ~10x faster than QEMU) to run the container.Context Awareness: The setup script validate
s that you are using the desktop-linux context (Docker Desktop) to ensure VM optimizations like virtiofs are active.Buil
d Compatibility: A custom build script detects if you are running locally on a Mac and forces docker buildx bake to load
 only the linux/amd64 image (since multi-arch images cannot be loaded into the local daemon).🚀 Usagemkdir cpp-universal 
&& cd cpp-universalSave the code below as generate_project.py.Run: python3 generate_project.pyInstall: pixi installConfi
gure: pixi run setup-dev (Select "Local Mac" or "Remote EPYC").📄 The Project GeneratorPythonimport osimport statimport p
latformimport subprocessimport jsonfrom pathlib import PathFILES = { # -------------------------------------------------
------------------------ # 1. Pixi Manifest (Bleeding Edge + Dev Tools) # ----------------------------------------------
--------------------------- "pixi.toml": r"""[project]name = "cpp-universal"version = "2026.5.0"platforms = ["linux-64",
 "osx-arm64"]# 🟢 Bleeding Edge Channels for GCC 15 / LLVM 21channels = ["conda-forge", "conda-forge/label/gcc_dev", "con
da-forge/label/llvm_rc"][pypi-options]resolve-dependencies-with-uv = true[dependencies]cmake = "*"ninja = "*"python = "3
.12.*"sccache = "*"bun = "*"# --- Automation Suite (Zero Tolerance) ---[feature.automation.dependencies]docker-py = "*"r
ich = "*"ruff = "*"vulture = "*"deptry = "*"hadolint = "*"actionlint = "*"check-jsonschema = "*"typos = "*"checkov = "*"
pytest = "*"pytest-testinfra = "*"[feature.automation.pypi-dependencies]ty = "*"zizmor = "*"# --- Compilers ---[feature.
gcc15.dependencies]gcc = "15.*"gxx = "15.*"[feature.llvm-head.dependencies]clang = "21.*"clangxx = "21.*"lld = "21.*"lld
b = "21.*"clang-tools = "21.*" # clang-tidy, clang-formatllvm-tools = "21.*" # llvm-mc, objdumpllvm-bolt = "21.*"# --- E
nvironments ---[environments]automation = ["automation"]stable = ["gcc15", "llvm-head"]dev_container = ["stable", "dev",
 "automation"][feature.dev.dependencies]gdb = "*"starship = "*"direnv = "*"opentelemetry-collector = "*"[tasks]validate 
= { cmd = "python -m scripts.validate", env = { PYTHONUNBUFFERED = "1" } }build = { cmd = "python -m scripts.build", env
 = { PYTHONUNBUFFERED = "1" } }setup-dev = { cmd = "python -m scripts.setup_dev", env = { PYTHONUNBUFFERED = "1" } }init
-container = "python -m scripts.lib.container_init"""", # --------------------------------------------------------------
----------- # 2. Docker Infrastructure # ------------------------------------------------------------------------- "dock
er/docker-bake.hcl": r"""variable "REGISTRY" { default = "ghcr.io/my-org/cpp" }variable "CONFIG_HASH" { default = "local
" }group "default" { targets = ["build"] }target "base" { dockerfile = "docker/Dockerfile" # 🟢 Multi-Arch: Builds for bo
th Server (AMD64) and Mac Native (ARM64) # Note: Local Mac Dev will force-pull AMD64 to match Server. platforms = ["linu
x/amd64", "linux/arm64"] cache-from = ["type=gha"] cache-to = ["type=gha,mode=max"] attest = ["type=provenance,mode=max"
, "type=sbom"]}target "build" { inherits = ["base"] matrix = { # 🟢 Ubuntu Matrix os = ["focal", "noble"] env = ["stable"
] } name = "${os}-${env}" args = { BASE_IMAGE = "ghcr.io/prefix-dev/pixi:${os}" PIXI_ENV = "${env}" } tags = ["${REGISTR
Y}:${os}-${env}-${CONFIG_HASH}"]}""", "docker/Dockerfile": r"""# syntax=docker/dockerfile:1ARG BASE_IMAGEFROM ${BASE_IMA
GE}WORKDIR /appCOPY pixi.toml pixi.lock ./ARG PIXI_ENV# ⚡️ Cache MountsRUN --mount=type=cache,target=/root/.cache/pixi \
 --mount=type=cache,target=/root/.cache/uv \ pixi install --frozen --environment ${PIXI_ENV}# ❄️ Freeze Env to JSONRUN p
ixi run -e ${PIXI_ENV} python -c "import os, json; print(json.dumps(dict(os.environ)))" > /app/pixi_env.json# Symlink Py
thon & S3 PackRUN ln -sf /app/.pixi/envs/${PIXI_ENV}/bin/python /app/python_runtimeRUN pixi global install pixi-pack && 
\ pixi-pack pack -e ${PIXI_ENV} --platform linux-64 -o /app/environment.tar.gzCOPY docker/entrypoint.py /app/entrypoint.
pyENTRYPOINT ["/app/python_runtime", "/app/entrypoint.py"]CMD ["/bin/bash"]""", "docker/entrypoint.py": r"""import os, s
ys, jsondef main(): if os.path.exists("/app/pixi_env.json"): with open("/app/pixi_env.json") as f: os.environ.update(jso
n.load(f)) args = sys.argv[1:] or ["/bin/bash"] try: os.execvpe(args[0], args, os.environ) except FileNotFoundError: sys
.exit(f"Error: Command '{args[0]}' not found.")if __name__ == "__main__": main()""", # ---------------------------------
---------------------------------------- # 3. Dev Containers (The Split Strategy) # ------------------------------------
------------------------------------- # Option A: Local Mac (AMD64 Emulated) ".devcontainer/mac-amd64/devcontainer.json"
: r"""{ "name": "Local Mac (AMD64 Emulation)", // 🟢 Target the Noble (Ubuntu 24.04) image "image": "ghcr.io/my-org/cpp:n
oble-stable-latest", "remoteUser": "vscode", "updateRemoteUserUID": true, // 🟢 FORCE PLATFORM: Use Docker Desktop Rosett
a Emulation "runArgs": [ "--platform=linux/amd64", "--cap-add=SYS_PTRACE", "--security-opt", "seccomp=unconfined" // Not
e: --network=host is NOT supported on Mac Docker Desktop ], "features": { "ghcr.io/devcontainers/features/common-utils:2
": { "installZsh": true }, "ghcr.io/devcontainers/features/sshd:1": { "version": "latest" }, "ghcr.io/devcontainers-cont
rib/features/bun:1": { "version": "latest" } }, "postCreateCommand": "pixi run init-container", "customizations": { "vsc
ode": { "extensions": ["ms-vscode.cpptools", "sst.opencode"] } }}""", # Option B: Remote EPYC (Hybrid) ".devcontainer/re
mote-hybrid/devcontainer.json": r"""{ "name": "Remote EPYC Server", "image": "ghcr.io/my-org/cpp:noble-stable-latest", "
remoteUser": "vscode", "updateRemoteUserUID": true, "features": { "ghcr.io/devcontainers/features/common-utils:2": { "in
stallZsh": true }, "ghcr.io/devcontainers/features/sshd:1": { "version": "latest" }, "ghcr.io/devcontainers-contrib/feat
ures/bun:1": { "version": "latest" } }, "runArgs": ["--network=host"], "postCreateCommand": "pixi run init-container"}""
", # ------------------------------------------------------------------------- # 4. Automation Scripts # ---------------
---------------------------------------------------------- "scripts/setup_dev.py": r"""import osimport shutilimport plat
formimport subprocessimport jsonfrom rich.prompt import Prompt, Confirmfrom rich.console import Consolefrom rich.panel i
mport Panelconsole = Console()def check_docker_desktop(): """Validates Docker Desktop Context.""" if platform.system() !
= "Darwin": return try: # Check Context ctx = subprocess.check_output(["docker", "context", "show"], text=True).strip() 
if ctx == "desktop-linux": console.print("[green]✅ Using Docker Desktop (desktop-linux)[/green]") else: console.print(f"
[yellow]⚠️ Current Context: {ctx}. 'desktop-linux' recommended for Mac.[/yellow]") # Check Architecture if platform.mach
ine() == "arm64": console.print("[cyan]🍎 Apple Silicon detected. Configuring AMD64 Emulation...[/cyan]") console.print("
 Ensure [bold]Use Rosetta for x86/amd64 emulation[/bold] is enabled in Docker Settings.") except: console.print("[red]❌ 
Docker CLI not working[/red]")def main(): console.print(Panel.fit("Universal C++ Environment Setup")) check_docker_deskt
op() mode = Prompt.ask("Select Mode", choices=["local", "remote"], default="local") if mode == "local": console.print("[
green]✅ Setup Complete[/green]") console.print("1. Open VS Code") console.print("2. Run 'Reopen in Container'") console.
print("3. Select [bold]Local Mac (AMD64 Emulation)[/bold]") else: alias = Prompt.ask("Remote Alias", default="epyc") ip 
= Prompt.ask("Remote IP") user = Prompt.ask("Remote User", default="ubuntu") cfg = os.path.expanduser("~/.ssh/config") e
ntry = f"\nHost {alias}\n HostName {ip}\n User {user}\n ForwardAgent yes\n" if Confirm.ask(f"Add {alias} to SSH config?"
): with open(cfg, "a") as f: f.write(entry) if shutil.which("mutagen") and Confirm.ask("Start Mutagen Sync?"): subproces
s.run(["mutagen", "sync", "terminate", "cpp-univ"], stderr=subprocess.DEVNULL) subprocess.run(["mutagen", "sync", "creat
e", "--name", "cpp-univ", "--mode", "two-way-safe", "--ignore", "build/", "--ignore", ".pixi/", ".", f"{alias}:/home/{us
er}/workspace/cpp-univ"])if __name__ == "__main__": main()""", "scripts/build.py": r"""import os, hashlib, subprocessfro
m rich.console import Consoleconsole = Console()BASE_IMAGES = { "focal": "ghcr.io/prefix-dev/pixi:focal", "noble": "ghcr
.io/prefix-dev/pixi:noble" }def main(): console.rule("[bold blue]Universal Build") digests = {k: "latest" for k in BASE_
IMAGES} # Add lookup logic if needed hasher = hashlib.sha256() for f in ["pixi.lock", "docker/Dockerfile", "docker/docke
r-bake.hcl"]: if os.path.exists(f): with open(f, "rb") as file: hasher.update(file.read()) config_hash = hasher.hexdiges
t()[:12] if "GITHUB_OUTPUT" in os.environ: with open(os.environ["GITHUB_OUTPUT"], "a") as f: f.write(f"HASH={config_hash
}\n") env = os.environ.copy() env.update({"CONFIG_HASH": config_hash}) # 🟢 CRITICAL FIX for Local Builds: # "docker buil
dx bake --load" fails if multiple platforms are defined. # We must force a single platform when building locally on Mac.
 target = "--push" if os.getenv("CI") else "--load" if target == "--load": print("⚠️ Local Build detected: Forcing linux
/amd64 load (Emulation Mode)") # Overrides the platforms list in docker-bake.hcl to just one subprocess.run(["docker", "
buildx", "bake", "--set", "*.platforms=linux/amd64", target], env=env, check=True) else: # CI pushes both amd64 and arm6
4 subprocess.run(["docker", "buildx", "bake", target], env=env, check=True)if __name__ == "__main__": main()""", "script
s/validate.py": r"""import subprocess, sys, shutilfrom concurrent.futures import ThreadPoolExecutorCHECKS = [ ("Ruff", [
"ruff", "check", "."]), ("Ty", ["ty", "check", "."]), ("Hadolint", ["hadolint", "docker/Dockerfile"]), ("Checkov", ["che
ckov", "-d", "docker", "--quiet", "--compact"]), ("Zizmor", ["zizmor", ".github/workflows"]), ("Schema", ["check-jsonsch
ema", "--schemafile", "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json", ".de
vcontainer/mac-amd64/devcontainer.json"])]def run(c): if not shutil.which(c[1][0]): return (False, c[0], "Missing") r = 
subprocess.run(c[1], capture_output=True, text=True) return (r.returncode==0, c[0], r.stdout+r.stderr)def main(): with T
hreadPoolExecutor() as exe: for ok, name, out in exe.map(run, CHECKS): print(f"{'✅' if ok else '❌'} {name}") if not ok: 
print(out) sys.exit(1)if __name__ == "__main__": main()""", "scripts/lib/container_init.py": r"""import os, json, subpro
cessdef main(): if os.path.exists("/app/pixi_env.json"): with open("/app/pixi_env.json") as f: data = json.load(f) with 
open(os.path.expanduser("~/.zshrc"), "a") as f: f.write("\n# Pixi Hydration\n") for k,v in data.items(): if k not in ["P
ATH", "HOME"]: f.write(f'export {k}="{v}"\n') # Verify Architecture arch = subprocess.check_output(["uname", "-m"]).deco
de().strip() if arch == "x86_64": print("✅ Running in AMD64 (Emulated/Native)") else: print("⚠️ Running in ARM64") subpr
ocess.run(["bun", "install", "--global", "@google/gemini-cli", "opencode"], check=False)if __name__ == "__main__": main(
)""", ".github/workflows/ci.yml": r"""name: Buildon: [push]jobs: build: runs-on: ubuntu-latest steps: - uses: actions/ch
eckout@v4 - uses: prefix-dev/setup-pixi@v0.8.3 with: { environments: automation } - uses: docker/setup-qemu-action@v3 - 
uses: docker/setup-buildx-action@v3 - uses: docker/login-action@v3 with: { registry: ghcr.io, username: ${{ github.actor
 }}, password: ${{ secrets.GITHUB_TOKEN }} } - run: pixi run -e automation build""", "scripts/__init__.py": "", "scripts
/lib/__init__.py": "", "scripts/tests/__init__.py": "", "scripts/tests/test_placeholder.py": "def test_ok(): assert True
", "pyproject.toml": r"""[tool.ruff]target-version = "py312"[tool.ty]check-untyped-defs = true[tool.vulture]exclude = ["
scripts/tests"][tool.deptry]ignore_obsolete = ["pytest", "pytest-testinfra", "rich", "docker", "check-jsonschema"]"""}de
f generate_project(): root = Path("cpp-universal") root.mkdir(exist_ok=True) for filename, content in FILES.items(): fil
epath = root / filename filepath.parent.mkdir(parents=True, exist_ok=True) with open(filepath, "w", encoding="utf-8") as
 f: f.write(content.strip() + "\n") print(f"📄 Created {filepath}") for script in (root / "scripts").glob("**/*.py"): os.
chmod(script, os.stat(script).st_mode | stat.S_IEXEC) print("\n✅ Project Generated! Run 'pixi install' inside.")if __nam
e__ == "__main__": generate_project()
