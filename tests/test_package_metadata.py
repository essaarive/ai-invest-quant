from pathlib import Path

import ai_invest_quant
import ai_invest_quant.cli as cli

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_package_import_and_version():
    assert ai_invest_quant.__version__ == "0.3.1"


def test_cli_import_and_main_callable():
    assert callable(cli.main)


def test_pyproject_metadata_exists_and_contains_project_name_and_script():
    pyproject = PROJECT_ROOT / "pyproject.toml"

    assert pyproject.exists()

    text = pyproject.read_text(encoding="utf-8")
    assert 'name = "ai-invest-quant"' in text
    assert 'version = "0.3.1"' in text
    assert 'ai-invest-quant = "ai_invest_quant.cli:main"' in text


def test_gitignore_exists_keeps_sample_data_and_ignores_outputs():
    gitignore = PROJECT_ROOT / ".gitignore"

    assert gitignore.exists()

    lines = {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert "outputs/" in lines
    assert "data/samples/sample_etf_prices.csv" not in lines
