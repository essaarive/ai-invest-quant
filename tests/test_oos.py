import pandas as pd
import pytest

from ai_invest_quant.performance.oos import calculate_oos_summary, split_nav_in_out_sample


def nav_df(rows: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=rows),
            "equity": [1000.0 + index * 10 for index in range(rows)],
            "nav": [1.0 + index * 0.01 for index in range(rows)],
        }
    )


def test_split_nav_in_out_sample_splits_by_ratio():
    split = split_nav_in_out_sample(nav_df(10), out_of_sample_ratio=0.3)

    assert len(split["in_sample_nav"]) == 7
    assert len(split["out_of_sample_nav"]) == 3
    assert split["split_date"] == pd.Timestamp("2024-01-08")


def test_split_nav_ratio_zero_disables_out_of_sample():
    split = split_nav_in_out_sample(nav_df(5), out_of_sample_ratio=0)

    assert len(split["in_sample_nav"]) == 5
    assert split["out_of_sample_nav"].empty
    assert split["split_date"] is None


@pytest.mark.parametrize("ratio", [-0.1, 1.0, "bad"])
def test_split_nav_invalid_ratio_raises_error(ratio):
    with pytest.raises(ValueError, match="out_of_sample_ratio must be >= 0 and < 1"):
        split_nav_in_out_sample(nav_df(10), out_of_sample_ratio=ratio)


def test_split_nav_too_few_rows_raises_error():
    with pytest.raises(ValueError, match="too few rows"):
        split_nav_in_out_sample(nav_df(1), out_of_sample_ratio=0.3)


def test_calculate_oos_summary_returns_in_and_out_sample_metrics():
    summary = calculate_oos_summary(nav_df(10), out_of_sample_ratio=0.3)

    assert summary["split_date"] == pd.Timestamp("2024-01-08")
    assert "in_sample_total_return" in summary
    assert "in_sample_max_drawdown" in summary
    assert "in_sample_sharpe_ratio" in summary
    assert "out_of_sample_total_return" in summary
    assert "out_of_sample_max_drawdown" in summary
    assert "out_of_sample_sharpe_ratio" in summary
