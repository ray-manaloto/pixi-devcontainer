Here is the **Reference Architecture v3.0**.

It integrates **all latest requirements**:

1. **Astral-Native:** Uses uv (speed), ruff, ty, and vulture.  
2. **Pure Python:** Replaces shell scripts with typed Python logic in scripts/.  
3. **Modern Docker:** Uses **Bake** for the matrix, **Attestations** (SBOMs), **Cache Mounts** (10x speed), and fixes the ENTRYPOINT variable expansion issue.  
4. **Hybrid Storage:** Stores Docker images in GHCR and portable pixi-packs in S3.

### ---

**📂 1\. Directory Structure**

Plaintext

.  
├── .github/workflows/ci.yml      \# CI Orchestrator  
├── docker/  
│   ├── Dockerfile                \# Optimized Builder (Cache \+ Symlinks)  
│   ├── docker-bake.hcl           \# Matrix Definition (2x2 \+ Attestations)  
│   └── entrypoint.py             \# Runtime Logic (Pure Python)  
├── scripts/  
│   ├── \_\_init\_\_.py  
│   ├── build.py                  \# Build Driver (Hash \+ Bake \+ S3)  
│   ├── validate.py               \# Quality Gate (Ruff \+ Ty \+ Infra)  
│   └── tests/  
│       └── test\_container.py     \# Infrastructure Validation  
├── pixi.toml                     \# Project Manifest  
├── pixi.lock                     \# Lockfile (Source of Truth)  
└── pyproject.toml                \# Tool Configuration

### ---

**⚙️ 2\. Pixi Configuration (pixi.toml)**

**Key Features:**

* resolve-dependencies-with-uv: Enables instant dependency solving.  
* **Environments:** Maps stable to GCC14 and experimental to GCC15.  
* **Automation:** Isolated environment for your CI tools.

Ini, TOML

\[project\]  
name \= "cpp-matrix"  
version \= "2025.1.0"  
platforms \= \["linux-64", "osx-arm64"\]

\[pypi-options\]  
\# 🚀 Enable uv for instant dependency resolution  
resolve-dependencies-with-uv \= true

\[dependencies\]  
cmake \= "3.28.\*"  
ninja \= "1.12.\*"  
python \= "3.11.\*" \# Runtime Python for Entrypoint  
sccache \= "\*"     \# Distributed Compilation Cache

\# \--- Feature: Automation (CI Tools) \---  
\[feature.automation.dependencies\]  
\# Python SDKs  
boto3 \= "\*"            \# AWS S3  
docker-py \= "\*"        \# Docker Engine  
rich \= "\*"             \# UI

\# Quality Suite  
ruff \= "\*"             \# Lint/Format/Security/Complexity  
vulture \= "\*"          \# Dead Code  
deptry \= "\*"           \# Dependency Audit  
pytest \= "\*"  
pytest-testinfra \= "\*" \# Container Validation

\# Binary Linters  
hadolint \= "\*"         \# Dockerfile Linter  
actionlint \= "\*"       \# GHA Linter  
typos \= "\*"            \# Spell Checker

\[feature.automation.pypi-dependencies\]  
ty \= "\*"               \# Astral Type Checker

\# \--- Feature: Compilers \---  
\[feature.gcc14.dependencies\]  
gcc \= "14.\*"  
gxx \= "14.\*"

\[feature.gcc15.dependencies\]  
gcc \= "15.\*"  
gxx \= "15.\*"

\[feature.llvm21.dependencies\]  
\# Placeholder: LLVM 21 is not out yet; mapping to 19 for functionality  
clang \= "19.\*"   
clangxx \= "19.\*"  
lld \= "19.\*"

\# \--- Environments (The Matrix) \---  
\[environments\]  
automation \= \["automation"\]  
stable \= \["gcc14", "llvm21"\]  
experimental \= \["gcc15", "llvm21"\]

\[tasks\]  
validate \= { cmd \= "python \-m scripts.validate", env \= { PYTHONUNBUFFERED \= "1" } }  
build \= { cmd \= "python \-m scripts.build", env \= { PYTHONUNBUFFERED \= "1" } }

### ---

**🛠️ 3\. Strict Tool Config (pyproject.toml)**

This replaces 5+ configuration files.

Ini, TOML

\[tool.ruff\]  
line-length \= 100  
target-version \= "py311"

\[tool.ruff.lint\]  
\# F=Pyflakes, E=Style, I=Isort, UP=Modernize, B=Bugbear, S=Bandit, C90=Complexity  
select \= \["F", "E", "I", "UP", "B", "S", "C90"\]

\[tool.ruff.lint.mccabe\]  
max-complexity \= 10  \# 🧠 Enforce simple logic

\[tool.ty\]  
check-untyped-defs \= true  
disallow-any-generics \= true

\[tool.vulture\]  
min\_confidence \= 80  
paths \= \["scripts", "docker"\]

### ---

**🐳 4\. Universal Dockerfile (docker/Dockerfile)**

**Modern Features:**

1. **RUN \--mount=type=cache**: Caches uv and pixi downloads (10x faster).  
2. **Symlinked Entrypoint**: Solves the bug where ENTRYPOINT cannot resolve ARG variables.  
3. **Pixi Pack**: Generates a tarball for your remote EPYC server.

Dockerfile

\# syntax=docker/dockerfile:1  
ARG BASE\_IMAGE  
FROM ${BASE\_IMAGE}

WORKDIR /app

\# 1\. Install Dependencies  
COPY pixi.toml pixi.lock ./

ARG PIXI\_ENV  
\# ⚡️ CACHE MOUNT: Persist downloads to host  
RUN \--mount=type\=cache,target=/root/.cache/pixi \\  
    \--mount=type\=cache,target=/root/.cache/uv \\  
    pixi install \--frozen \--environment ${PIXI\_ENV}

\# 2\. Freeze Environment (Pythonic Activation)  
\# Dump env vars to JSON to bypass slow shell activation scripts  
RUN pixi run \-e ${PIXI\_ENV} python \-c "import os, json; print(json.dumps(dict(os.environ)))" \> /app/pixi\_env.json

\# 3\. Create Stable Entrypoint Link  
\# Docker ENTRYPOINT instructions cannot expand ARGs.   
\# We symlink the dynamic path to a static one (/app/python\_runtime).  
RUN ln \-sf /app/.pixi/envs/${PIXI\_ENV}/bin/python /app/python\_runtime

\# 4\. Generate Portable Pack (S3 Artifact for Remote Server)  
RUN pixi global install pixi-pack && \\  
    pixi-pack pack \-e ${PIXI\_ENV} \--platform linux-64 \-o /app/environment.tar.gz

COPY docker/entrypoint.py /app/entrypoint.py

\# Execute entrypoint using the symlinked python  
ENTRYPOINT \["/app/python\_runtime", "/app/entrypoint.py"\]  
CMD \["/bin/bash"\]

### ---

**🧱 5\. Docker Bake Matrix (docker-bake.hcl)**

**New Features:**

* **Attestations**: Automatically attaches **SBOM** and **Provenance** (SLSA) to images.

Terraform

variable "REGISTRY" { default \= "ghcr.io/my-org/cpp" }  
variable "CONFIG\_HASH" { default \= "local" }  
\# Injected by build.py  
variable "DIGEST\_FOCAL" { default \= "latest" }  
variable "DIGEST\_JAMMY" { default \= "latest" }

group "default" { targets \= \["build"\] }

target "base" {  
  dockerfile \= "docker/Dockerfile"  
  platforms \= \["linux/amd64"\]  
  \# ⚡️ GHA Layer Caching  
  cache-from \= \["type=gha"\]  
  cache-to   \= \["type=gha,mode=max"\]  
    
  \# 🔒 Supply Chain Security: Attestations  
  attest \= \[  
    "type=provenance,mode=max",  
    "type=sbom"  
  \]  
}

target "build" {  
  inherits \= \["base"\]  
    
  matrix \= {  
    \# 2 OSs x 2 Compilers \= 4 Images  
    os \= \["focal", "jammy"\]           \# Ubuntu 20.04, 22.04  
    env \= \["stable", "experimental"\]  \# gcc14, gcc15  
  }

  name \= "${os}-${env}"  
    
  args \= {  
    \# Dynamically select base image digest (Security)  
    BASE\_IMAGE \= "ghcr.io/prefix-dev/pixi:${os}@" \+ ("${os}" \== "focal" ? "${DIGEST\_FOCAL}" : "${DIGEST\_JAMMY}")  
    PIXI\_ENV   \= "${env}"  
  }

  tags \= \[  
    "${REGISTRY}:${os}-${env}-${CONFIG\_HASH}",  
    "${REGISTRY}:${os}-${env}-latest"  
  \]  
}

### ---

**🏎️ 6\. The Build Driver (scripts/build.py)**

Handles Hashing, Baking, and S3 Uploads.

Python

import os  
import hashlib  
import subprocess  
import boto3  
from rich.console import Console

console \= Console()  
S3\_BUCKET \= os.getenv("S3\_BUCKET", "my-artifacts")  
BASE\_IMAGES \= {  
    "focal": "ghcr.io/prefix-dev/pixi:focal",  
    "jammy": "ghcr.io/prefix-dev/pixi:jammy"  
}

def get\_remote\_digest(image: str) \-\> str:  
    """Fetch upstream digest to ensure security updates trigger rebuilds."""  
    try:  
        cmd \= \["docker", "buildx", "imagetools", "inspect", image, "--format", "{{.Manifest.Digest}}"\]  
        return subprocess.check\_output(cmd, text=True).strip()  
    except subprocess.CalledProcessError:  
        return "latest"

def calculate\_hash(digests: dict) \-\> str:  
    hasher \= hashlib.sha256()  
    \# Hash Config Files  
    for f in \["pixi.lock", "pixi.toml", "docker/Dockerfile", "docker-bake.hcl"\]:  
        with open(f, "rb") as file:  
            hasher.update(file.read())  
    \# Hash Upstream Digests  
    for k, v in digests.items():  
        hasher.update(f"{k}:{v}".encode())  
    return hasher.hexdigest()\[:12\]

def upload\_artifacts(config\_hash: str, os\_name: str, env: str, tag: str):  
    """Uploads Docker Image \+ Pixi Pack to S3."""  
    s3 \= boto3.client("s3")  
      
    \# 1\. Save & Upload Docker Image (Archive)  
    img\_file \= f"{os\_name}\-{env}.tar"  
    subprocess.run(\["docker", "save", "-o", img\_file, tag\], check=True)  
    s3.upload\_file(img\_file, S3\_BUCKET, f"images/{config\_hash}/{img\_file}")  
    os.remove(img\_file)  
      
    \# 2\. Extract & Upload Pixi Pack (For Remote Server)  
    pack\_file \= "environment.tar.gz"  
    \# Create temp container to extract file  
    cid \= subprocess.check\_output(\["docker", "create", tag\]).decode().strip()  
    subprocess.run(\["docker", "cp", f"{cid}:/app/environment.tar.gz", pack\_file\], check=True)  
    subprocess.run(\["docker", "rm", "-v", cid\], check=True)  
      
    s3.upload\_file(pack\_file, S3\_BUCKET, f"packs/{config\_hash}/{os\_name}\-{env}.tar.gz")  
    os.remove(pack\_file)

def main():  
    console.rule("\[bold blue\]Starting Build")  
      
    \# 1\. Calc Hash  
    digests \= {k: get\_remote\_digest(v) for k, v in BASE\_IMAGES.items()}  
    config\_hash \= calculate\_hash(digests)  
    console.print(f"🔑 Hash: {config\_hash}")  
      
    if "GITHUB\_OUTPUT" in os.environ:  
        with open(os.environ\["GITHUB\_OUTPUT"\], "a") as f:  
            f.write(f"HASH={config\_hash}\\n")

    \# 2\. Bake  
    env \= os.environ.copy()  
    env.update({  
        "CONFIG\_HASH": config\_hash,  
        "DIGEST\_FOCAL": digests\["focal"\],  
        "DIGEST\_JAMMY": digests\["jammy"\]  
    })  
      
    target \= "--push" if os.getenv("CI") else "--load"  
    subprocess.run(\["docker", "buildx", "bake", target\], env=env, check=True)

    \# 3\. S3 (CI Only)  
    if os.getenv("CI"):  
        for os\_n in \["focal", "jammy"\]:  
            for env\_n in \["stable", "experimental"\]:  
                tag \= f"{os.getenv('REGISTRY', 'ghcr.io/my-org/cpp')}:{os\_n}\-{env\_n}\-{config\_hash}"  
                upload\_artifacts(config\_hash, os\_n, env\_n, tag)

if \_\_name\_\_ \== "\_\_main\_\_":  
    main()

### ---

**🚦 7\. Runtime Entrypoint (docker/entrypoint.py)**

Python

import os  
import sys  
import json

def main():  
    \# Load frozen environment variables  
    env\_file \= "/app/pixi\_env.json"  
    if os.path.exists(env\_file):  
        with open(env\_file) as f:  
            os.environ.update(json.load(f))  
      
    \# Replace process with command  
    args \= sys.argv\[1:\] or \["/bin/bash"\]  
    try:  
        os.execvpe(args\[0\], args, os.environ)  
    except FileNotFoundError:  
        sys.exit(f"Error: Command '{args\[0\]}' not found.")

if \_\_name\_\_ \== "\_\_main\_\_":  
    main()  
