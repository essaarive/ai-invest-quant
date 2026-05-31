from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_contains_ruff_dependency_and_config():
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"ruff"' in text
    assert "[tool.ruff]" in text
    assert "line-length = 100" in text
    assert 'target-version = "py310"' in text
    assert 'select = ["E", "F", "I", "B"]' in text


def test_readme_documents_ruff_commands():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "ruff check ." in text
    assert "ruff format ." in text


def test_docs_document_ruff_quality_checks():
    status = (PROJECT_ROOT / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "ruff check" in status
    assert "ruff format" in status
    assert "Ruff" in roadmap or "formatting" in roadmap
