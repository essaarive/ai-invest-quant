import pytest

from ai_invest_quant.risk.risk_manager import RiskManager


def test_valid_parameters_initialize():
    risk_manager = RiskManager()

    assert risk_manager.mode == "normal"
    assert risk_manager.peak_equity == 0.0
    assert risk_manager.current_drawdown == 0.0


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_max_position_weight_out_of_range_raises_error(value):
    with pytest.raises(ValueError, match="max_position_weight.*>= 0.*<= 1"):
        RiskManager(max_position_weight=value)


def test_defensive_exposure_cannot_exceed_normal_exposure():
    with pytest.raises(ValueError, match="defensive_max_exposure.*<= normal_max_exposure"):
        RiskManager(normal_max_exposure=0.5, defensive_max_exposure=0.6)


def test_recovery_drawdown_must_be_greater_than_defensive_drawdown():
    with pytest.raises(ValueError, match="recovery_drawdown.*> defensive_drawdown"):
        RiskManager(defensive_drawdown=-0.12, recovery_drawdown=-0.13)


def test_peak_equity_updates_on_new_high():
    risk_manager = RiskManager()

    risk_manager.update_state(1000)
    risk_manager.update_state(1200)

    assert risk_manager.peak_equity == 1200
    assert risk_manager.current_drawdown == 0.0


def test_drawdown_switches_to_defensive_and_recovers_to_normal():
    risk_manager = RiskManager()

    risk_manager.update_state(1000)
    risk_manager.update_state(870)

    assert risk_manager.mode == "defensive"
    assert risk_manager.current_drawdown == -0.13

    risk_manager.update_state(950)

    assert risk_manager.mode == "normal"
    assert risk_manager.current_drawdown == pytest.approx(-0.05)


@pytest.mark.parametrize("equity", [0, -1])
def test_equity_must_be_positive(equity):
    risk_manager = RiskManager()

    with pytest.raises(ValueError, match="equity must be > 0"):
        risk_manager.update_state(equity)


def test_single_position_weight_is_clipped_to_thirty_percent():
    risk_manager = RiskManager()

    result = risk_manager.apply_limits({"ETF_A": 0.5})

    assert result == {"ETF_A": 0.3}


def test_normal_mode_total_exposure_is_scaled_to_eighty_percent():
    risk_manager = RiskManager()

    result = risk_manager.apply_limits({"ETF_A": 0.4, "ETF_B": 0.4, "ETF_C": 0.4})

    assert sum(result.values()) == pytest.approx(0.8)
    assert result["ETF_A"] == pytest.approx(0.8 / 3)


def test_defensive_mode_total_exposure_is_scaled_to_thirty_percent():
    risk_manager = RiskManager()
    risk_manager.mode = "defensive"

    result = risk_manager.apply_limits({"ETF_A": 0.3, "ETF_B": 0.3, "ETF_C": 0.3})

    assert sum(result.values()) == pytest.approx(0.3)
    assert result["ETF_A"] == pytest.approx(0.1)


@pytest.mark.parametrize("weight", [-0.1, 1.1])
def test_invalid_target_weight_raises_error(weight):
    risk_manager = RiskManager()

    with pytest.raises(ValueError, match="target weight.*>= 0.*<= 1"):
        risk_manager.apply_limits({"ETF_A": weight})


def test_cash_is_ignored_and_output_exposure_respects_current_mode():
    risk_manager = RiskManager()

    result = risk_manager.apply_limits({"CASH": 1.0, "ETF_A": 0.5, "ETF_B": 0.5, "ETF_C": 0.5})

    assert "CASH" not in result
    assert sum(result.values()) == pytest.approx(risk_manager.normal_max_exposure)
