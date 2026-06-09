import pandas as pd
import pytest

from ai_invest_quant.data.quality_report import generate_data_quality_report


def make_clean_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2024-01-01",
                "symbol": "ETF_A",
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.5,
                "volume": 1000,
                "amount": 10500,
            },
            {
                "date": "2024-01-02",
                "symbol": "ETF_A",
                "open": 10.5,
                "high": 11.5,
                "low": 10.0,
                "close": 11.0,
                "volume": 1100,
                "amount": 12100,
            },
            {
                "date": "2024-01-01",
                "symbol": "ETF_B",
                "open": 20.0,
                "high": 21.0,
                "low": 19.0,
                "close": 20.5,
                "volume": 2000,
                "amount": 41000,
            },
        ]
    )


def test_clean_standard_data_generates_report_per_symbol():
    report = generate_data_quality_report(make_clean_prices())

    assert report["symbol"].tolist() == ["ETF_A", "ETF_B"]
    assert len(report) == 2


def test_start_date_and_end_date_are_correct():
    report = generate_data_quality_report(make_clean_prices())
    etf_a = report[report["symbol"] == "ETF_A"].iloc[0]

    assert etf_a["start_date"] == "2024-01-01"
    assert etf_a["end_date"] == "2024-01-02"


def test_duplicate_date_count_is_correct():
    df = make_clean_prices()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    report = generate_data_quality_report(df)
    etf_a = report[report["symbol"] == "ETF_A"].iloc[0]

    assert etf_a["duplicate_date_count"] == 1


def test_missing_close_count_is_correct():
    df = make_clean_prices()
    df.loc[0, "close"] = pd.NA

    report = generate_data_quality_report(df)
    etf_a = report[report["symbol"] == "ETF_A"].iloc[0]

    assert etf_a["missing_close_count"] == 1
    assert etf_a["missing_value_count"] == 1


def test_zero_or_negative_price_count_is_correct():
    df = make_clean_prices()
    df.loc[0, "open"] = 0.0
    df.loc[1, "close"] = -1.0

    report = generate_data_quality_report(df)
    etf_a = report[report["symbol"] == "ETF_A"].iloc[0]

    assert etf_a["zero_or_negative_price_count"] == 2


def test_high_low_error_count_is_correct():
    df = make_clean_prices()
    df.loc[0, "high"] = 8.0

    report = generate_data_quality_report(df)
    etf_a = report[report["symbol"] == "ETF_A"].iloc[0]

    assert etf_a["high_low_error_count"] == 1


def test_negative_volume_and_amount_counts_are_correct():
    df = make_clean_prices()
    df.loc[0, "volume"] = -1
    df.loc[1, "amount"] = -1

    report = generate_data_quality_report(df)
    etf_a = report[report["symbol"] == "ETF_A"].iloc[0]

    assert etf_a["negative_volume_count"] == 1
    assert etf_a["negative_amount_count"] == 1


def test_serious_issues_fail_and_clean_data_passes():
    clean_report = generate_data_quality_report(make_clean_prices())
    assert clean_report.loc[clean_report["symbol"] == "ETF_A", "is_passed"].iloc[0]

    df = make_clean_prices()
    df.loc[0, "close"] = 0.0
    issue_report = generate_data_quality_report(df)

    assert not issue_report.loc[issue_report["symbol"] == "ETF_A", "is_passed"].iloc[0]


def test_issues_contain_readable_descriptions():
    df = make_clean_prices()
    df.loc[0, "close"] = 0.0
    df.loc[1, "volume"] = -1

    report = generate_data_quality_report(df)
    issues = report.loc[report["symbol"] == "ETF_A", "issues"].iloc[0]

    assert "zero or negative price values found" in issues
    assert "negative volume found" in issues


def test_output_path_saves_csv(tmp_path):
    output_path = tmp_path / "reports" / "data_quality_report.csv"

    report = generate_data_quality_report(make_clean_prices(), output_path=output_path)

    assert output_path.exists()
    saved = pd.read_csv(output_path)
    assert saved["symbol"].tolist() == report["symbol"].tolist()


def test_missing_required_column_raises_error():
    df = make_clean_prices().drop(columns=["close"])

    with pytest.raises(ValueError, match="Missing required price columns: close"):
        generate_data_quality_report(df)


def test_empty_dataframe_raises_error():
    with pytest.raises(ValueError, match="price_df cannot be empty"):
        generate_data_quality_report(pd.DataFrame())


def test_input_dataframe_is_not_modified():
    df = make_clean_prices()
    original = df.copy(deep=True)

    generate_data_quality_report(df)

    pd.testing.assert_frame_equal(df, original)
