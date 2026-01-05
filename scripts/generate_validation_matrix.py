"""Generate docs/validation-matrix.md from the current validation list."""

import os
from pathlib import Path
from typing import Union

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

DEFAULT_OUTPUT = Path("docs/validation-matrix.md")


def render_validation_matrix() -> str:
    """Return the validation matrix markdown content."""
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

    return "\n".join(lines) + "\n"


def write_validation_matrix(
    path: Union[Path, str] = DEFAULT_OUTPUT,
) -> None:
    """Write the validation matrix markdown to the given path."""
    Path(path).write_text(render_validation_matrix(), encoding="utf-8")


def main() -> None:
    """Write the validation matrix markdown to docs/validation-matrix.md."""
    output = os.environ.get("VALIDATION_MATRIX_PATH", DEFAULT_OUTPUT)
    write_validation_matrix(output)


if __name__ == "__main__":
    main()
