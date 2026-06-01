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
    assert "metadata.json" in text
    assert "load_experiment_config" in text
    assert "save_experiment_config" in text
    assert "load_run_index" in text
    assert "load_historical_run" in text
    assert "Load Config" in text
    assert "Save Config" in text
    assert "Run History" in text
    assert "Language" in text
    assert "English" in text
    assert "中文" in text
    assert "AI 投资量化研究仪表盘" in text
    assert "运行回测" in text
    assert "历史实验记录" in text
    assert "对比历史实验" in text
    assert "参数敏感性分析" in text
    assert "核心绩效指标" in text
    assert "样本外评估" in text
    assert "基准对比" in text
    assert "No run history yet." in text
    assert "Select historical run" in text
    assert "Load Historical Run" in text
    assert "Compare Historical Runs" in text
    assert "Select runs to compare" in text
    assert "Compare Selected Runs" in text
    assert "Metrics Comparison" in text
    assert "Config Comparison" in text
    assert "NAV Comparison" in text
    assert "Missing historical output files" in text
    assert "Use auto run directory" in text
    assert "Actual output directory" in text
    assert "Benchmark symbol" in text
    assert "Strategy vs Benchmark" in text
    assert "benchmark_nav.csv" in text
    assert "Out-of-sample ratio" in text
    assert "Out-of-Sample Evaluation" in text
    assert "Parameter Sensitivity" in text
    assert "Run Parameter Sensitivity" in text
    assert "sensitivity_summary.csv" in text
    assert "Top N values" in text
    assert "Target exposure values" in text
    assert "Rebalance interval values" in text
    assert "Walk-forward Testing" in text
    assert "Run Walk-forward Test" in text
    assert "walk_forward_summary.csv" in text
    assert "Train window days" in text
    assert "Test window days" in text
    assert "Step days" in text
    assert "滚动样本外测试" in text
    assert "运行滚动样本外测试" in text


def test_readme_documents_dashboard_command():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "streamlit run dashboard/app.py" in readme
    assert "CSV upload" in readme
    assert "download output files" in readme
    assert "configs/demo_config.json" in readme
    assert "metadata.json" in readme
    assert "index.csv" in readme
    assert "Load Historical Run" in readme
    assert "Compare Historical Runs" in readme
    assert "Load Config" in readme
    assert "Save Config" in readme
    assert "auto_run_dir" in readme
    assert "benchmark_symbol" in readme or "Benchmark" in readme
    assert "out_of_sample_ratio" in readme
    assert "English / 中文" in readme


def test_streamlit_dependency_is_declared():
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "streamlit" in requirements or "streamlit" in pyproject
