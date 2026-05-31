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


def test_github_actions_ci_workflow_exists_and_runs_quality_checks():
    workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

    assert workflow.exists()

    text = workflow.read_text(encoding="utf-8")
    assert "name: CI" in text
    assert 'python-version: "3.10"' in text or "python-version: 3.10" in text
    assert "ruff check ." in text
    assert "python -m pytest" in text or "python3 -m pytest" in text


def test_readme_and_docs_document_github_actions_ci():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    status = (PROJECT_ROOT / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "GitHub Actions" in readme or "CI" in readme
    assert "GitHub Actions" in status
    assert "GitHub Actions" in roadmap
