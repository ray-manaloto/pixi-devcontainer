# Pixi tasks and local gate

Run tasks with `pixi run -e automation <task>`. The local pre-push gate is `prepush`, which runs all linters/tests and prints the docker bake plan.

## Core gates
- `prepush`: depends on `validate` + `docker-bake-print`; full local gate before push.
- `validate`: depends on `git-clean`, `lint`, `tests`; runs all linters and tests.
- `lint`: meta task that depends on every `lint-*` task listed below.
- `tests`: `pytest --cov=scripts scripts/tests`.
- `build`: `python -m scripts.build` (push in CI, load locally).

## Linters / analyzers (all part of `lint`)
- `lint-ruff-format`: `ruff format --check .`
- `lint-ruff`: `ruff check .`
- `lint-ty`: `ty check --python .pixi/envs/automation/bin/python scripts --exclude scripts/tests/test_container.py`
- `lint-vulture`: `vulture scripts docker`
- `lint-pylint-dup`: duplicate-code check via `pylint`
- `lint-mypy`: `mypy scripts --ignore-missing-imports --implicit-reexport`
- `lint-semgrep`: semgrep (dockerized); set `RUN_SEMGREP=0` to skip, requires Docker.
- `lint-shellcheck`: shellcheck all tracked `*.sh` (skips if none)
- `lint-hadolint`: hadolint via `docker run hadolint/hadolint` on `docker/Dockerfile`
- `lint-actionlint`: actionlint
- `lint-checkov`: `checkov -d docker --quiet --compact`
- `lint-uv`: `uv pip check --project .`
- `lint-pyrefly`: `pyrefly check … scripts/*.py scripts/lib/*.py`
- `lint-taplo`: `taplo format --check pixi.toml pyproject.toml`
- `lint-yamllint`: `yamllint .github .devcontainer`
- `lint-typos`: `typos .`
- `lint-jsonschema`: devcontainer schema check
- `lint-zizmor`: `zizmor .github/workflows`

## Utility tasks
- `docker-bake-print`: `docker buildx bake -f docker/docker-bake.hcl --print`
- `git-clean`: fails if the working tree is dirty (used by `validate`)
- `setup-dev`: `python -m scripts.setup_dev`
- `init-container`: `python -m scripts.lib.container_init`
- `ci-store-run`: `python -m scripts.gha_monitor --store`
- `ci-watch`: `python -m scripts.gha_monitor --watch`
- `renovate-dispatch`: depends on `prepush`, then runs `gh workflow run renovate.yml` to trigger Renovate after local validation
- `renovate-status`: `gh run list --workflow renovate.yml --limit 5 …` (shows last 5 Renovate runs)
- `validate-renovate`: actionlint + yamllint (minimal gate for renovate workflow)
- `devcontainer-ports`: enumerate devcontainer permutations and suggest SSH ports
