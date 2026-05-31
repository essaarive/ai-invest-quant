"""Run directory naming helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def create_run_directory(base_output_dir: str | Path, now: datetime | None = None) -> Path:
    """Create a unique timestamped run directory under base_output_dir/runs."""
    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    runs_root = Path(base_output_dir) / "runs"
    candidate = runs_root / timestamp
    suffix = 1
    while candidate.exists():
        candidate = runs_root / f"{timestamp}_{suffix:03d}"
        suffix += 1

    candidate.mkdir(parents=True, exist_ok=False)
    return candidate

