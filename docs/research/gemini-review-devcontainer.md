Gemini research summary — devcontainer/CI hardening
===================================================

Scope
- Goal: prebuilt devcontainer images (Ubuntu 24.04, GCC 15, LLVM 21) with strict quality gates and reproducible builds.
- Reviewed common pitfalls and prescribed fixes; we have already applied these patterns in this repo.

Key issues identified
- Local rebuilds: devcontainer.json rebuilding the Dockerfile instead of pulling the CI-built image.
- Entrypoint override: VS Code server overrides ENTRYPOINT, dropping Pixi environment activation and PATH changes.
- Missing cache strategy: repeated downloads of compilers and dependencies.

Fixes implemented
- Prebuilt image consumption: devcontainer.json points to GHCR `noble-stable-latest`; bake tags include `-latest` so the devcontainer pulls the CI artifact.
- Env hydration: build writes `/app/pixi_env.json`; entrypoint restores env vars so PATH and activation survive VS Code overrides.
- Caching: Dockerfile uses cache mounts; bake uses `cache-from`/`cache-to` GHA.
- Build/attestations: buildx bake with provenance + SBOM attestations; artifacts include bake plan, build log, OCI tars, GHCR status.
- Quality gates: actionlint, hadolint (dockerized), semgrep, checkov, zizmor, typos, yamllint, taplo, mypy/ruff/ty, etc.; coverage enforced; pixi metadata, coverage, and JUnit uploaded.

Operational guidance
- Local gate: run `pixi run -e automation prepush` before pushing (lint + tests + docker bake --print + clean tree).
- CI: uses linux/amd64 platform for pixi solves; hadolint via docker image to avoid platform package gaps.
- Devcontainer: uses prebuilt GHCR image; hydration script restores env vars on container start.

Notes
- Multi-arch support is ready in bake but currently limited to amd64 per requirement.
- The research doc’s generator code isn’t used directly; we adopted the patterns and hardened them here.
