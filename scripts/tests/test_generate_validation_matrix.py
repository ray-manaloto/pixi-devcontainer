"""Tests for the validation matrix generator."""

from pathlib import Path

from scripts import generate_validation_matrix as gvm


def test_render_validation_matrix_contains_header_and_rows() -> None:
    """Ensure the matrix text contains the header and expected rows."""
    content = gvm.render_validation_matrix()

    assert "# Validation Matrix" in content
    rows = [
        line
        for line in content.splitlines()
        if line.startswith("| ") and "Validation | Where | How" not in line
    ]
    assert len(rows) == len(gvm.ROWS)
    assert "| Ruff format/check | Local + CI | lint-ruff-format, lint-ruff |" in content


def test_write_validation_matrix(tmp_path: Path) -> None:
    """Ensure the file writer persists the rendered content."""
    out_file = tmp_path / "validation-matrix.md"
    gvm.write_validation_matrix(out_file)

    assert out_file.read_text(encoding="utf-8") == gvm.render_validation_matrix()


def test_main_respects_output_env(tmp_path: Path, monkeypatch) -> None:
    """Cover the CLI entrypoint while isolating the output path."""
    target = tmp_path / "custom.md"
    monkeypatch.setenv("VALIDATION_MATRIX_PATH", str(target))

    gvm.main()

    assert target.read_text(encoding="utf-8") == gvm.render_validation_matrix()
