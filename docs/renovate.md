# Renovate configuration

We run Renovate every 6 hours to keep dependencies fresh. Config: `renovate.json`.

Managers enabled
- GitHub Actions: keeps workflow actions pinned and updated (automerge patch/minor).
- pep621 (pyproject.toml): updates PyPI/uv dependencies.
- Regex manager for `pixi.toml`: updates conda/pixi dependencies (datasource/versioning = conda).

Notes
- Schedule: `every 6 hours`.
- Labels: `deps`.
- Automerge: enabled for minor/patch GitHub Actions; pixi/conda automerge disabled by default (adjust via packageRules).
- If adding new deps to pixi/pyproject, no extra config needed; regex manager matches `depName = "version"` lines in pixi.toml.
