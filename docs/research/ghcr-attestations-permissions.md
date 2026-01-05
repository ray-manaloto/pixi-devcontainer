Based on the research into your specific architecture and GHCR's
security model, here is the detailed advisory.

### 1. GHCR Permissions & "HEAD 403" Prevention

The "HEAD 403 Forbidden" error during docker buildx bake --push with
attestations is a common friction point between BuildKit's provenance
checks and GHCR's permission scopes.

**The Fix:** You **do not** need a PAT. GITHUB_TOKEN is sufficient if
configured correctly.

#### A. Repository & Org Settings

1.  **Package Creation:**

    - **First Push:** The GITHUB_TOKEN cannot create a *public* package
      in an organization context by default if your organization
      enforces "Private by default" for new packages.

    - **Pre-creation (Recommended):** Manually create the package
      placeholder or push the first image using a PAT to establish the
      namespace ghcr.io/ray-manaloto/pixi-devcontainer.

    - **Link Repository:** Go to the Package Settings -\> **Manage
      Actions access** -\> **Add repository**. Ensure your repo has
      Write or Admin access. *This is the \#1 cause of 403s.*

2.  Workflow Permissions (YAML)  
    You must explicitly grant these scopes in your workflow file.
    packages: write alone is often insufficient for modern attestations
    (SBOM/Provenance).  
    YAML  
    permissions:  
    contents: read  
    packages: write  
    attestations: write  
    id-token: write \# Required for OIDC token generation for sigstore
    signing

#### B. The "HEAD 403" Quirk & Buildx Flags

The 403 often happens when BuildKit attempts to check if a provenance
blob exists using a HEAD request.

- **Mitigation 1 (Configuration):** In docker-bake.hcl, ensure you
  aren't accidentally trying to attach attestations to the local target.
  Attestations only work reliably with the image driver pushing directly
  to a registry.

- **Mitigation 2 (Flags):** If you experience flakes, disable the
  default provenance generation for the *local* validation stage, or set
  it to mode=min for CI to reduce API calls.  
  **Recommended docker-bake.hcl tweak for stability:**  
  Terraform  
  target "default" {  
  \#...  
  attest = \[  
  \# Use min mode to reduce metadata overhead unless max is strictly
  required  
  "type=provenance,mode=min",  
  "type=sbom"  
  \]  
  }

### 2. Validation Tooling: Pinning & Fallbacks

**Verdict:** Use **conda-forge** for native binaries (Actionlint,
Hadolint, Typos) and **PyPI** for Semgrep.

- **Rationale:** The conda-forge ecosystem provides native binaries for
  osx-arm64 (Apple Silicon) and linux-64 for the tools below. This
  avoids the slowness of Docker and the complexity of Python venvs for
  Go/Haskell tools.

| **Tool** | **Source** | **Platform Support** | **Strategy** |
|----|----|----|----|
| **Actionlint** | conda-forge | ✅ Linux, ✅ macOS (ARM/Intel) | Pin in pixi.toml \[dependencies\] |
| **Hadolint** | conda-forge | ✅ Linux, ✅ macOS (ARM/Intel) | Pin in pixi.toml \[dependencies\] |
| **Typos** | conda-forge | ✅ Linux, ✅ macOS (ARM/Intel) | Pin in pixi.toml \[dependencies\] |
| **Semgrep** | PyPI | ✅ Linux, ✅ macOS (ARM/Intel) | Use \[pypi-dependencies\] |

- **Fallback Strategy:** Do not use "optional skips" or fallback to
  Docker. If a tool is missing on a supported platform (unlikely for
  these), the pixi lock process will fail, alerting you immediately.
  This is a feature, not a bug—it prevents CI/Local drift.

### 3. Fail-Fast System Requirements

Yes, add \[system-requirements\] to pixi.toml. This prevents developers
with outdated OS versions from attempting builds that will inevitably
fail due to libc/linker mismatches.

**Add this to pixi.toml:**

> Ini, TOML

\[system-requirements\]  
\# Enforce a modern glibc (e.g., Ubuntu 20.04+) to match your base
image  
linux = "5.4"  
libc = { family = "glibc", version = "2.31" }  
  
\# Fail fast on old Intel Macs or unupdated Apple Silicon  
macos = "13.0"

### 4. Pre-flight Checks in scripts/validate.py

Before running the heavy validation logic, your script should perform a
"sanity check" of the environment.

**Recommended scripts/validate.py Snippet:**

> Python

import shutil  
import sys  
import subprocess  
  
REQUIRED_TOOLS = \["actionlint", "hadolint", "typos", "semgrep",
"docker"\]  
  
def preflight_checks():  
missing =  
for tool in REQUIRED_TOOLS:  
if not shutil.which(tool):  
missing.append(tool)  
  
if missing:  
print(f"❌ Critical tools missing from PATH: {', '.join(missing)}")  
print(" Did you run 'pixi install'? Try 'pixi run setup-dev'")  
sys.exit(1)  
  
\# Fast Docker Daemon Check  
try:  
subprocess.run(  
,  
check=True, capture_output=True  
)  
except (subprocess.CalledProcessError, FileNotFoundError):  
print("❌ Docker daemon is not running or not reachable.")  
sys.exit(1)  
  
if \_\_name\_\_ == "\_\_main\_\_":  
preflight_checks()  
\#... rest of validation logic...

### 5. Summary of Recommended CI/Bake Flags

To reduce flakes when pushing to GHCR from GHA:

1.  **Retry Logic:** BuildKit has internal retries, but network flakes
    happen.

2.  **Git Context:** Use git context, not local context, to ensure
    reproducible metadata.

**Updated scripts/build.py Command Construction:**

> Python

cmd =
