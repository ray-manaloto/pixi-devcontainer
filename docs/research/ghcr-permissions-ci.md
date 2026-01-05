Based on the architecture and configuration files analyzed in the
research, here is the advice on aligning your validations and confirming
the Docker hashing strategy.

### 1. Enforcing Platform Consistency (Local vs. CI)

You cannot rely solely on environment variables like PIXI_PLATFORM to
force a macOS (ARM64) machine to execute Linux (AMD64) binaries
natively; the kernel prevents this. Instead, consistency is enforced in
two distinct phases: **Resolution** and **Runtime**.

- Phase 1: Resolution Consistency (The Lockfile)  
  You must configure your pixi.toml to solve for both platforms
  simultaneously. This ensures that even if a developer is on macOS, any
  dependency added must also exist and be resolvable for Linux.  
  Ini, TOML  
  \[project\]  
  platforms = \["linux-64", "osx-arm64"\]  
    
  Pixi guarantees that pixi.lock remains valid for the CI platform
  (linux-64) whenever a macOS developer updates
  dependencies.<sup>1</sup>

- Phase 2: Runtime Consistency (Emulation)  
  To allow macOS developers to "run the full gate," you must use
  containerized emulation. The "Universal Mac-AMD64" strategy identified
  in the research utilizes Docker Desktop's Rosetta 2 support.

  - **Implementation:** In your scripts/build.py or
    .devcontainer/devcontainer.json, you explicitly pass --platform
    linux/amd64 to the Docker execution args.<sup>1</sup>

  - **Result:** The developer runs the exact CI container locally. The
    performance penalty is negligible for compilation/linting due to
    Rosetta, but it guarantees binary parity.

### 2. Canonical Gates and Task Wiring

To avoid "it works on my machine" failures, you should structure your
Pixi tasks into a hierarchy that runs locally and in CI.

- **Recommended Task Hierarchy:**

  - **lint**: Fast, local formatting checks (Ruff, formatting). Run this
    on pre-commit.

  - **validate**: **The Canonical Gate.** This task should aggregate all
    static analysis (Actionlint, Hadolint, Semgrep, Typos). It must run
    locally via pixi run validate and be the first job in your CI
    pipeline.<sup>1</sup>

  - **prepush**: A "meta-task" defined in pixi.toml using depends-on to
    chain lint and validate. Developers run this manually before
    pushing.<sup>3</sup>

- CI-Specific Additions (Push vs. Load):  
  The scripts/build.py driver provided in the research handles this
  logic automatically so you don't need separate tasks.

  - **Local Context:** If the CI env var is absent, it defaults to
    --load (loads image to local Docker daemon).

  - **CI Context:** If CI=true, it defaults to --push (pushes to
    GHCR/ECR).<sup>1</sup>

  - **Documentation:** Document simply: "Run pixi run build. In CI, this
    pushes; locally, it loads."

### 3. Preventing Drift: Native vs. Dockerized Tools

Do **not** use Dockerized tools (e.g., docker run hadolint...) for
linting if you can avoid it. The latency discourages developers from
running them. The research confirms that the conda-forge ecosystem is
sufficiently mature to support native binaries for your required tools
on both linux-64 and osx-arm64.

Drift Prevention Strategy:

Define these tools in the \[feature.automation.dependencies\] section of
pixi.toml. This cryptographically pins the version in pixi.lock,
ensuring CI and Local use the exact same binary version.

| **Tool** | **Source** | **Strategy** |
|----|----|----|
| **Actionlint** | conda-forge | Available on ARM64/AMD64. Pin in pixi.toml.<sup>4</sup> |
| **Hadolint** | conda-forge | Available on ARM64/AMD64. Pin in pixi.toml.<sup>5</sup> |
| **Typos** | conda-forge | Available on ARM64/AMD64. Pin in pixi.toml.<sup>6</sup> |
| **Semgrep** | PyPI | Use Pixi's \[pypi-dependencies\] with uv resolution. Conda versions often lag; PyPI is canonical for Semgrep.<sup>7</sup> |

### 4. Manifest Tweaks for Fail-Fast Validation

To catch missing tools or platform errors locally:

- **System Requirements:** Add a \[system-requirements\] section to
  pixi.toml. If a developer's machine (e.g., outdated macOS or glibc)
  cannot support the build environment, Pixi will fail immediately
  during installation, rather than later during a build.<sup>8</sup>

- **The validate.py Abstraction:** Instead of raw shell commands, map
  the validate task to python -m scripts.validate. This script
  (referenced in the research) should check for the existence of
  required binaries using shutil.which() before execution, providing
  clear "Missing Tool" errors instead of cryptic shell
  failures.<sup>1</sup>

### 5. Confirmation of Docker Hashing Strategy

**YES**, the hash is being properly created with the base image digest.

The analysis of scripts/build.py confirms the following logic is
implemented <sup>1</sup>:

1.  **Remote Inspection:** The script executes docker buildx imagetools
    inspect on the upstream base image (e.g.,
    ghcr.io/prefix-dev/pixi:focal) to retrieve its current sha256
    manifest digest.

2.  **Hash Composition:** This upstream digest is mixed into the local
    config_hash alongside the contents of pixi.lock and docker-bake.hcl.

3.  **Result:** If the base image is updated upstream (e.g., a security
    patch), your build system detects the digest change, generates a new
    configuration hash, and triggers a rebuild, even if your local
    source code hasn't changed.
