from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_app_exists_and_contains_required_streamlit_content():
    app_path = PROJECT_ROOT / "dashboard" / "app.py"

    assert app_path.exists()

    text = app_path.read_text(encoding="utf-8")
    assert "import streamlit as st" in text
    assert "run_etf_rotation_demo" in text
    assert "AI Invest Quant Dashboard" in text
    assert "st.file_uploader" in text
    assert "st.download_button" in text
    assert "Upload ETF price CSV" in text
    assert "Download Outputs" in text
    assert "load_experiment_config" in text
    assert "save_experiment_config" in text
    assert "Load Config" in text
    assert "Save Config" in text


def test_readme_documents_dashboard_command():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "streamlit run dashboard/app.py" in readme
    assert "CSV upload" in readme
    assert "download output files" in readme
    assert "configs/demo_config.json" in readme
    assert "Load Config" in readme
    assert "Save Config" in readme


def test_streamlit_dependency_is_declared():
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "streamlit" in requirements or "streamlit" in pyproject
