Deep Research Prompts for pixi-devcontainer
===========================================

Goal
-----
Minimize rebuilds and maximize reproducibility of the devcontainer images while keeping rich CI artifacts. Please provide concrete, code-level recommendations with filenames and line numbers.

Context
--------
- Repo: github.com/ray-manaloto/pixi-devcontainer
- Current stack: buildx bake (docker/docker-bake.hcl) with GHA cache, Dockerfile with cache mounts, CI in .github/workflows/ci.yml, build orchestration in scripts/build.py.
- Tags: `${REGISTRY}:${os}-${env}-${CONFIG_HASH}` and `${REGISTRY}:${os}-${env}-latest`
- Platforms: amd64 only (intentionally)
- Artifacts: bake-plan.json, build.log, OCI tarballs (when loaded), ghcr-status.json/md, oci-metadata.json, pixi metadata, coverage/tests.

Questions
----------
1) Bake caching & hash reuse (docker/docker-bake.hcl)
   - How should we set `cache-to/cache-from` (type=gha) for maximum reuse? Recommend exact `scope`/`mode` and if per-target overrides are needed. Cite file/lines to change.
   - Should we add/modify `labels`, `secrets`, or `args` to improve cache hits? Any ordering changes?
   - Best practice for handling base image digests so config hash/tag reuse is accurate across runs?

2) Dockerfile cache friendliness (docker/Dockerfile)
   - Any changes to instruction ordering, ARG defaults, or cache mounts to reduce invalidation when only metadata changes?
   - Are there better ways to persist pixi/uv caches or to avoid re-running pixi-pack when unchanged?

3) CI workflow adjustments (.github/workflows/ci.yml)
   - Builder configuration: should we set a persistent buildx builder name/driver options to improve cache reuse?
   - Should we add a post-push `--load` or `imagetools` export to produce artifacts (OCI tars) without re-running a full build?
   - Any workflow-level caching or `cache-from` hints we should add to avoid cold caches on every push?
   - Recommend exact steps to summarize bake targets/build info (if additional tables/logs would help).

4) Build orchestration (scripts/build.py)
   - How to compute/persist config hashes (currently based on pixi.toml/lock/Dockerfile/bake.hcl and base digests) so tags map to identical content across runs?
   - When pushing, should we still load locally for artifacts, or is there a better export mechanism? Provide exact code changes/flags.
   - How to handle artifact uploads without re-running the build (e.g., use build output refs/imagetools)?

5) Registry-side patterns
   - Any recommendations for registry cache hints or manifest reuse to avoid redundant rebuilds?

Please respond with concrete edits: file paths + line numbers, exact bake flags or cache scopes, and any new steps to add/remove. The objective is fewer rebuilds, deterministic tags, and richer but efficient artifact generation. 

Follow-up for pixi validation parity
------------------------------------
Please also advise on aligning pixi-based validations between local and CI:
- How to enforce platform consistency (e.g., PIXI_PLATFORM=linux-64) while allowing macOS developers to run the full gate.
- Which pixi tasks should be the canonical gates (lint, tests, prepush) and any CI-specific additions (push vs load) that should be documented.
- How to avoid CI/local drift for tools like actionlint/hadolint/semgrep/typos (e.g., dockerized tools, env vars).
- Any recommended pixi task wiring or manifest tweaks to ensure failures (e.g., missing tools, platform solves) are caught locally before GHA.
