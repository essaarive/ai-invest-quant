from datetime import datetime

from ai_invest_quant.utils.run_id import create_run_directory


def test_create_run_directory_uses_timestamp_format(tmp_path):
    run_dir = create_run_directory(tmp_path, now=datetime(2026, 5, 31, 3, 15, 30))

    assert run_dir == tmp_path / "runs" / "20260531_031530"
    assert run_dir.exists()


def test_create_run_directory_adds_suffix_on_collision(tmp_path):
    first = create_run_directory(tmp_path, now=datetime(2026, 5, 31, 3, 15, 30))
    second = create_run_directory(tmp_path, now=datetime(2026, 5, 31, 3, 15, 30))

    assert first.name == "20260531_031530"
    assert second.name == "20260531_031530_001"
