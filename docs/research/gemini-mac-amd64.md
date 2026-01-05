Gemini research summary — Mac running amd64 devcontainer
========================================================

Goal
- Run the Linux/amd64 devcontainer on Apple Silicon via Docker Desktop (Rosetta) while keeping parity with the CI-built image.

Recommendations (aligned with repo)
- Force platform: devcontainer uses `--platform=linux/amd64` and `DOCKER_DEFAULT_PLATFORM=linux/amd64`; Docker Desktop handles Rosetta emulation.
- Consume prebuilt image: devcontainer.json points to GHCR `noble-stable-latest`, avoiding local rebuilds.
- Hydrate env: build writes `/app/pixi_env.json`; entrypoint restores env vars so activation persists under VS Code.
- Bake/cache: buildx bake with cache-to/from GHA; cache mounts in Dockerfile to speed Pixi/uv downloads.
- Platform scope: keep builds amd64-only for now (per requirement); multi-arch can be enabled later if needed.

Developer steps on Mac
1) Install Docker Desktop with Rosetta support enabled for amd64 emulation.
2) `pixi run -e automation prepush` before pushing (lint/tests + bake --print).
3) Open the repo in VS Code and “Reopen in Container”; it will pull the GHCR amd64 image and hydrate env vars automatically.
