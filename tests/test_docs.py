from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_docs_exist():
    assert (PROJECT_ROOT / "docs" / "PROJECT_STATUS.md").exists()
    assert (PROJECT_ROOT / "docs" / "ARCHITECTURE.md").exists()
    assert (PROJECT_ROOT / "docs" / "ROADMAP.md").exists()


def test_project_status_contains_required_content():
    text = (PROJECT_ROOT / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "V0.2 Research MVP" in text
    assert "205 passed" in text
    assert "Not Supported" in text


def test_architecture_contains_required_content():
    text = (PROJECT_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "Data Flow" in text
    assert "Backtest Assumptions" in text


def test_roadmap_contains_required_content():
    text = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "Short-Term Roadmap" in text


def test_readme_links_to_project_docs():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/PROJECT_STATUS.md" in text
