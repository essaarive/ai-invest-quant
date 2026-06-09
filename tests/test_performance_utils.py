import pandas as pd
import pytest

from ai_invest_quant.performance.utils import prepare_nav_dataframe


def test_date_and_equity_generate_nav():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "equity": [1000.0, 1100.0],
        }
    )

    result = prepare_nav_dataframe(df)

    assert result["nav"].tolist() == [1.0, 1.1]


def test_existing_nav_is_preserved_and_validated():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "equity": [1000.0, 1200.0],
            "nav": [1.0, 1.2],
        }
    )

    result = prepare_nav_dataframe(df)

    assert result["nav"].tolist() == [1.0, 1.2]


def test_date_is_sorted():
    df = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01"],
            "equity": [1100.0, 1000.0],
        }
    )

    result = prepare_nav_dataframe(df)

    assert result["date"].tolist() == [
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
    ]
    assert result["nav"].tolist() == [1.0, 1.1]


def test_input_dataframe_is_not_modified():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "equity": [1000.0],
        }
    )
    original = df.copy(deep=True)

    prepare_nav_dataframe(df)

    pd.testing.assert_frame_equal(df, original)


def test_missing_date_raises_error():
    df = pd.DataFrame({"equity": [1000.0]})

    with pytest.raises(ValueError, match="Missing required nav columns: date"):
        prepare_nav_dataframe(df)


def test_missing_equity_raises_error():
    df = pd.DataFrame({"date": ["2024-01-01"]})

    with pytest.raises(ValueError, match="Missing required nav columns: equity"):
        prepare_nav_dataframe(df)


@pytest.mark.parametrize("equity", [0.0, -1.0])
def test_equity_must_be_positive(equity):
    df = pd.DataFrame({"date": ["2024-01-01"], "equity": [equity]})

    with pytest.raises(ValueError, match="equity values must be > 0"):
        prepare_nav_dataframe(df)


@pytest.mark.parametrize("nav", [0.0, -1.0])
def test_nav_must_be_positive(nav):
    df = pd.DataFrame({"date": ["2024-01-01"], "equity": [1000.0], "nav": [nav]})

    with pytest.raises(ValueError, match="nav values must be > 0"):
        prepare_nav_dataframe(df)


def test_equity_cannot_be_empty():
    df = pd.DataFrame({"date": ["2024-01-01"], "equity": [pd.NA]})

    with pytest.raises(ValueError, match="equity values cannot be empty"):
        prepare_nav_dataframe(df)


def test_nav_cannot_be_empty():
    df = pd.DataFrame({"date": ["2024-01-01"], "equity": [1000.0], "nav": [pd.NA]})

    with pytest.raises(ValueError, match="nav values cannot be empty"):
        prepare_nav_dataframe(df)


def test_return_contains_date_equity_and_nav():
    df = pd.DataFrame({"date": ["2024-01-01"], "equity": [1000.0]})

    result = prepare_nav_dataframe(df)

    assert {"date", "equity", "nav"}.issubset(result.columns)
