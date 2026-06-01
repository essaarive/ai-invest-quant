from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_docs_exist():
    assert (PROJECT_ROOT / "docs" / "PROJECT_STATUS.md").exists()
    assert (PROJECT_ROOT / "docs" / "ARCHITECTURE.md").exists()
    assert (PROJECT_ROOT / "docs" / "ROADMAP.md").exists()
    assert (PROJECT_ROOT / "docs" / "DEMO_GUIDE.md").exists()
    assert (PROJECT_ROOT / "docs" / "DATA_GUIDE.md").exists()


def test_dashboard_screenshot_assets_exist():
    assert (PROJECT_ROOT / "docs" / "assets" / "dashboard_overview.png").exists()
    assert (PROJECT_ROOT / "docs" / "assets" / "run_history.png").exists()
    assert (PROJECT_ROOT / "docs" / "assets" / "comparison_view.png").exists()


def test_project_status_contains_required_content():
    text = (PROJECT_ROOT / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "V0.3.1 Research Workbench" in text
    assert "250 passed" in text
    assert "CLI `run-walk-forward` support" in text
    assert "Not Supported" in text


def test_architecture_contains_required_content():
    text = (PROJECT_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "Data Flow" in text
    assert "Backtest Assumptions" in text
    assert "sensitivity" in text


def test_roadmap_contains_required_content():
    text = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "Short-Term Roadmap" in text
    assert "CLI run-sensitivity" in text
    assert "CLI run-walk-forward" in text
    assert "Walk-forward testing" in text


def test_readme_links_to_project_docs():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/PROJECT_STATUS.md" in text
    assert "docs/ARCHITECTURE.md" in text
    assert "docs/ROADMAP.md" in text
    assert "docs/DATA_GUIDE.md" in text


def test_readme_showcase_sections_exist():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "AI Invest Quant" in text
    assert "V0.3.1 Research Workbench" in text
    assert "250 passed" in text
    assert "run-walk-forward" in text
    assert "Dashboard Preview" in text
    assert "docs/assets/dashboard_overview.png" in text
    assert "docs/assets/run_history.png" in text
    assert "docs/assets/comparison_view.png" in text
    assert "Typical Workflow" in text
    assert "Benchmark" in text
    assert "Out-of-Sample" in text
    assert "What Is Not Supported" in text


def test_demo_guide_contains_dashboard_and_history_comparison():
    text = (PROJECT_ROOT / "docs" / "DEMO_GUIDE.md").read_text(encoding="utf-8")

    assert "Run Dashboard" in text
    assert "Compare Historical Runs" in text
    assert "Run Parameter Sensitivity" in text
    assert "run-sensitivity" in text
    assert "sensitivity_summary.csv" in text
    assert "Run Walk-forward Testing" in text
    assert "run-walk-forward" in text
    assert "walk_forward_summary.csv" in text
    assert "assets/dashboard_overview.png" in text
    assert "assets/run_history.png" in text
    assert "assets/comparison_view.png" in text


def test_data_guide_documents_standard_schema_and_adapter():
    text = (PROJECT_ROOT / "docs" / "DATA_GUIDE.md").read_text(encoding="utf-8")

    assert "date,symbol,open,high,low,close,volume,amount" in text
    assert "standardize_price_csv" in text
