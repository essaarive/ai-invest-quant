import json

import pytest

from ai_invest_quant.config.experiment_config import (
    DEFAULT_EXPERIMENT_CONFIG,
    load_experiment_config,
    save_experiment_config,
    validate_experiment_config,
)


def test_default_demo_config_file_loads():
    config = load_experiment_config("configs/demo_config.json")

    assert config["csv_path"] == "data/samples/sample_etf_prices.csv"
    assert config["output_dir"] == "outputs/dashboard_demo"
    assert config["use_risk_manager"] is True


def test_save_and_load_experiment_config_round_trip(tmp_path):
    path = tmp_path / "experiment.json"
    config = DEFAULT_EXPERIMENT_CONFIG | {"output_dir": str(tmp_path / "outputs")}

    saved = save_experiment_config(config, path)
    loaded = load_experiment_config(path)

    assert path.exists()
    assert loaded == saved


def test_missing_required_field_raises_error():
    config = dict(DEFAULT_EXPERIMENT_CONFIG)
    config.pop("top_n")

    with pytest.raises(ValueError, match="Missing required experiment config fields: top_n"):
        validate_experiment_config(config)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("initial_cash", 0, "initial_cash must be > 0"),
        ("rebalance_interval", 0, "rebalance_interval must be > 0"),
        ("top_n", 0, "top_n must be > 0"),
        ("target_exposure", 1.1, "target_exposure must be >= 0 and <= 1"),
        ("fee_rate", -0.1, "fee_rate must be >= 0"),
        ("slippage", -0.1, "slippage must be >= 0"),
    ],
)
def test_invalid_config_values_raise_error(field, value, message):
    config = dict(DEFAULT_EXPERIMENT_CONFIG)
    config[field] = value

    with pytest.raises(ValueError, match=message):
        validate_experiment_config(config)


def test_load_non_object_json_raises_error(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="Experiment config must be a JSON object"):
        load_experiment_config(path)
