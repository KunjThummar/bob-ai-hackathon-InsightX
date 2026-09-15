"""
Reusable feature-engineering pipeline for the Mission Readiness Copilot.

This module is the SINGLE SOURCE OF TRUTH for every constant and function
related to feature engineering.  Both dataset inference and custom
prediction import from here so that the two paths can never drift apart.

Derived directly from the notebook (mission_readiness_copilot.ipynb) so that:
  - the same sensors are retained / dropped
  - the same 10-cycle rolling window is used
  - the same mean / std / trend definitions are applied
  - the same column ordering is produced for model input
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants — copied directly from the notebook cells 4 & 5
# ---------------------------------------------------------------------------

# Six sensors that have only one unique value in FD001 and are dropped.
CONSTANT_SENSORS = ["T2", "P2", "epr", "farB", "Nf_dmd", "PCNfR_dmd"]

# Fifteen core telemetry channels retained for feature engineering.
CORE_SENSORS = [
    "T24", "T30", "T50", "P15", "P30",
    "Nf", "Nc", "Ps30", "phi", "NRf", "NRc",
    "BPR", "W31", "W32", "htBleed",
]

# Rolling-window size used throughout (notebook cell 5: window=10).
ROLLING_WINDOW = 10

# Columns that carry identity / label / metadata — never used as ML features.
# Extended from the notebook's excluded_columns to include our added
# 'source' and 'asset_id' helper columns.
IDENTITY_COLUMNS = ["unit_id", "asset_id", "source", "dataset", "split"]

# RUL target column
RUL_COLUMN = "RUL"

# Cycle column — included in RUL features but excluded from anomaly features.
CYCLE_COLUMN = "cycle"

# Full exclusion set (everything except cycle — used for anomaly features)
_ALL_EXCLUDED = IDENTITY_COLUMNS + [RUL_COLUMN]
# RUL feature exclusion: excludes unit_id etc. but KEEPS cycle
RUL_EXCLUDED = IDENTITY_COLUMNS + [RUL_COLUMN]
# Anomaly feature exclusion: excludes unit_id etc. AND cycle
ANOMALY_EXCLUDED = IDENTITY_COLUMNS + [CYCLE_COLUMN, RUL_COLUMN]


def drop_constant_sensors(df: pd.DataFrame) -> pd.DataFrame:
    """Remove the constant/uninformative sensors (notebook cell 4)."""
    cols_to_drop = [c for c in CONSTANT_SENSORS if c in df.columns]
    return df.drop(columns=cols_to_drop)


def _calculate_slope(values: np.ndarray) -> float:
    """Linear trend/slope of a short window of values (notebook cell 5)."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    return float(np.polyfit(x, values, 1)[0])


def create_rolling_features(
    df: pd.DataFrame, sensors: list[str], window: int = ROLLING_WINDOW
) -> pd.DataFrame:
    """Rolling mean / std of each sensor per asset (chronological order)."""
    df = df.copy()
    df = df.sort_values(["asset_id", "cycle"])

    for sensor in sensors:
        df[f"{sensor}_mean"] = (
            df.groupby("asset_id")[sensor]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )
        df[f"{sensor}_std"] = (
            df.groupby("asset_id")[sensor]
            .transform(lambda x: x.rolling(window, min_periods=1).std())
            .fillna(0)
        )

    return df


def add_trend_features(
    df: pd.DataFrame, sensors: list[str], window: int = ROLLING_WINDOW
) -> pd.DataFrame:
    """Rolling slope of each sensor per asset (chronological order)."""
    df = df.copy()
    df = df.sort_values(["asset_id", "cycle"])

    for sensor in sensors:
        df[f"{sensor}_trend"] = (
            df.groupby("asset_id")[sensor]
            .transform(
                lambda x: x.rolling(window, min_periods=2).apply(
                    _calculate_slope, raw=True
                )
            )
            .fillna(0)
        )

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full feature-engineering pipeline applied to a raw telemetry DataFrame.

    Steps (mirroring the notebook):
      1. Drop constant sensors.
      2. Rolling mean + std (window = 10).
      3. Rolling trend / slope (window = 10).

    The returned DataFrame retains the original sensor columns PLUS all
    engineered columns, sorted by asset_id then cycle.
    """
    df = df.copy()
    df = drop_constant_sensors(df)
    df = create_rolling_features(df, CORE_SENSORS, window=ROLLING_WINDOW)
    df = add_trend_features(df, CORE_SENSORS, window=ROLLING_WINDOW)
    return df


def get_rul_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Feature columns fed to the RUL Random Forest.

    Excludes identity / label / metadata columns but KEEPS 'cycle'
    (the notebook's RUL feature_columns includes cycle).
    """
    return [c for c in df.columns if c not in RUL_EXCLUDED]


def get_anomaly_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Feature columns fed to the anomaly Isolation Forest.

    Excludes identity / label / metadata columns AND 'cycle'
    (the notebook's anomaly_features excludes cycle).
    """
    return [c for c in df.columns if c not in ANOMALY_EXCLUDED]
