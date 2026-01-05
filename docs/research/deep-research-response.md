Deep Research Agent Recommendations (Summary)
=============================================

Source: `/Users/rmanaloto/Downloads/Please read deep-research-prompts.md in github.co....docx`

Key prescriptions
-----------------
- Cache scoping (docker/docker-bake.hcl):
  - Add per-target GHA cache scopes, e.g. `cache-from = ["type=gha,scope=build-${os}-${env}"]` and `cache-to = ["type=gha,mode=max,scope=build-${os}-${env}"]` to prevent matrix jobs from overwriting each other’s cache (focal vs noble).
- Native artifact export (Dockerfile + bake):
  - Add an `export` stage `FROM scratch AS export` that copies `environment.tar.gz`.
  - Add a bake target `artifacts` that outputs `type=local,dest=./dist/${os}-${env}` so pixi-pack tarballs are streamed directly during build (no docker cp).
- BuildKit garbage collection (ci.yml):
  - Configure buildx driver options (via `docker/setup-buildx-action`) to use `image=moby/buildkit:latest`, `network=host`, and BUlLDKIT envs like `BUILDKIT_STEP_LOG_MAX_SIZE` / `BUILDKIT_STEP_LOG_MAX_SPEED` for aggressive GC to avoid disk exhaustion.
- Local vs push logic (scripts/build.py):
  - Detect local (Docker Desktop) and force `--load` + `--set *.platforms=linux/amd64`, skipping the artifacts target locally to avoid multi-arch load issues.
  - In CI use `--push` for multi-arch and rely on the export target for artifacts instead of docker cp/save.
- Tagging/hash:
  - Keep config hash derived from manifests + base digests; tags include hash and `-latest`. Ensure artifact export uses the same build so tags map to identical content.

Suggested implementation spots
------------------------------
- `docker/docker-bake.hcl`: add scoped cache-from/cache-to per target; add `artifacts` target with `output = ["type=local,dest=./dist/${os}-${env}"]`; set `target = "runtime"` for images and `target = "export"` for artifacts.
- `docker/Dockerfile`: add `FROM scratch AS export` copying `/app/environment.tar.gz`; split into `builder`, `export`, and `runtime` stages; keep cache mounts with `sharing=locked`.
- `.github/workflows/ci.yml`: set buildx driver opts (moby/buildkit:latest, network=host, BUILDKIT_* limits); consider running only `image` target locally and `image + artifacts` in CI.
- `scripts/build.py`: detect CI vs local; in CI use `--push` and include `artifacts` target; locally use `--load` and `--set *.platforms=linux/amd64`, skipping artifacts; keep config hash emission.

Next steps (plan)
-----------------
- Update bake file with scoped caches and artifacts target.
- Refactor Dockerfile into builder/export/runtime stages.
- Adjust CI buildx setup with GC-friendly driver options.
- Simplify build.py to pick targets/flags per CI vs local (push vs load) and rely on export target for artifacts.
- Verify caches warm across matrix (focal/noble) and that artifacts appear in `./dist/` during CI.
