"""
Sensor-evidence service — identifies which telemetry channels changed the
most for an asset by comparing its most-recent operating window against a
prior baseline (notebook cell 10: ``get_sensor_changes``).

These changes are *evidence of an evolving operating pattern*, not proof of
any particular component failure (see DOCX section 8.5).
"""

import numpy as np
import pandas as pd

from .feature_service import CORE_SENSORS

# Sensors used for the evidence comparison (same list as the notebook).
SENSORS_FOR_EXPLANATION = CORE_SENSORS

# Default windows (notebook cell 10).
DEFAULT_RECENT_WINDOW = 20
DEFAULT_PREVIOUS_WINDOW = 20


def _resolve_windows(n_rows: int, recent_window: int, previous_window: int) -> tuple[int, int]:
    """
    If the asset history is shorter than recent+previous, shrink both windows
    so we always have a non-empty comparison.  Full-length assets keep the
    notebook defaults exactly.
    """
    total = recent_window + previous_window
    if n_rows >= total:
        return recent_window, previous_window
    if n_rows < 2:
        return n_rows, 0
    # Split what we have roughly in half.
    recent = max(1, n_rows // 2)
    previous = n_rows - recent
    return recent, previous


def get_sensor_changes(
    asset_history: pd.DataFrame,
    sensors: list[str] | None = None,
    recent_window: int = DEFAULT_RECENT_WINDOW,
    previous_window: int = DEFAULT_PREVIOUS_WINDOW,
    top_n: int = 5,
) -> list[dict]:
    """
    Compare an asset's most-recent readings vs. its own prior baseline.

    Parameters
    ----------
    asset_history
        Full chronological telemetry for *one* asset, sorted by cycle.
        Raw sensor columns (T24, T30, ...) must be present.
    top_n
        Number of largest changes to return.

    Returns
    -------
    List of dicts sorted by absolute change (descending), each with keys:
        sensor, previous_mean, recent_mean, change_percent, direction,
        absolute_change_percent
    """
    if sensors is None:
        sensors = SENSORS_FOR_EXPLANATION

    asset_history = asset_history.sort_values("cycle").reset_index(drop=True)

    recent_w, previous_w = _resolve_windows(
        len(asset_history), recent_window, previous_window
    )

    recent = asset_history.tail(recent_w)
    # Guard against empty previous window (very short histories).
    if previous_w > 0:
        previous = asset_history.iloc[-(recent_w + previous_w): -recent_w] if len(asset_history) > recent_w else asset_history.iloc[:-recent_w]
    else:
        previous = pd.DataFrame(columns=asset_history.columns)

    changes = []
    for sensor in sensors:
        if sensor not in asset_history.columns:
            continue

        previous_mean = float(previous[sensor].mean()) if len(previous) else 0.0
        recent_mean = float(recent[sensor].mean()) if len(recent) else 0.0

        denom = abs(previous_mean)
        if denom == 0:
            percent_change = 0.0
        else:
            percent_change = ((recent_mean - previous_mean) / denom) * 100

        direction = "increased" if percent_change > 0 else (
            "decreased" if percent_change < 0 else "unchanged"
        )

        changes.append({
            "sensor": sensor,
            "previous_mean": round(previous_mean, 3),
            "recent_mean": round(recent_mean, 3),
            "change_percent": round(abs(percent_change), 3),
            "direction": direction,
            "absolute_change_percent": round(abs(percent_change), 3),
        })

    changes.sort(key=lambda x: x["absolute_change_percent"], reverse=True)
    return changes[:top_n]
