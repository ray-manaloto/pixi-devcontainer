"""Generate docs/validation-matrix.md from the current validation list."""

from pathlib import Path

ROWS = [
    ("Ruff format/check", "Local + CI", "lint-ruff-format, lint-ruff"),
    ("Ty type check", "Local + CI", "lint-ty"),
    ("Vulture", "Local + CI", "lint-vulture"),
    ("Pylint duplicate-code", "Local + CI", "lint-pylint-dup"),
    ("Mypy", "Local + CI", "lint-mypy"),
    ("Semgrep", "Local + CI", "lint-semgrep (dockerized)"),
    ("Shellcheck", "Local + CI", "lint-shellcheck"),
    ("Hadolint", "Local + CI", "lint-hadolint + hadolint action"),
    ("Actionlint", "Local + CI", "lint-actionlint"),
    ("Checkov", "Local + CI", "lint-checkov"),
    ("uv pip check", "Local + CI", "lint-uv"),
    ("Pyrefly", "Local + CI", "lint-pyrefly"),
    ("Taplo", "Local + CI", "lint-taplo"),
    ("Yamllint", "Local + CI", "lint-yamllint"),
    ("Typos", "Local + CI", "lint-typos"),
    ("Devcontainer schema", "Local + CI", "lint-jsonschema"),
    ("Zizmor", "Local + CI", "lint-zizmor"),
    ("Pytest + coverage", "Local + CI", "tests"),
    ("Docker bake plan", "Local + CI", "docker-bake-print"),
    ("Buildx info/SBOM/provenance", "CI only", "build job"),
    ("GHCR status/OCI metadata", "CI only", "build job summaries"),
]


def main() -> None:
    lines = [
        "# Validation Matrix",
        "",
        "Source of truth for what runs locally via pixi and in GitHub Actions.",
        "",
        "| Validation | Where | How |",
        "|---|---|---|",
    ]
    for name, where, how in ROWS:
        lines.append(f"| {name} | {where} | {how} |")

    Path("docs/validation-matrix.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
