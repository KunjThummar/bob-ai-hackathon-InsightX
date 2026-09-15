"""
Dataset service — orchestrates the full inference pipeline over the actual
dataset and caches the fleet-wide snapshot.

Flow per asset (mirrors the notebook cells 8-11):

    engineered features (latest row)
        → prediction_service.score_asset()          # RUL + anomaly scores
        → readiness_service.assess_readiness()      # readiness + status
        → maintenance_service.assess_maintenance()  # priority + recommendation
        → evidence_service.get_sensor_changes()   # sensor evidence

Both dataset-mode and custom-prediction-mode share the *same*
feature_service and prediction_service, so results are never duplicated.
"""

import os
from functools import lru_cache

import numpy as np
import pandas as pd

from .feature_service import CORE_SENSORS, engineer_features
from .prediction_service import score_asset
from .readiness_service import assess_readiness
from .maintenance_service import assess_maintenance
from .evidence_service import get_sensor_changes, SENSORS_FOR_EXPLANATION

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "actual_dataset.csv")


def _normalise_asset_id(asset_id) -> int:
    """Convert a path-style asset ID to the integer ID used in the CSV."""
    try:
        return int(str(asset_id).strip())
    except (TypeError, ValueError) as exc:
        raise KeyError(f"Asset '{asset_id}' not found in dataset.") from exc


@lru_cache(maxsize=1)
def load_raw_dataset() -> pd.DataFrame:
    """Load the raw CSV (cached)."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset not found at {DATA_PATH}. "
            "Run 'python backend/scripts/download_dataset.py' first."
        )
    df = pd.read_csv(DATA_PATH)
    df = df.sort_values(["asset_id", "cycle"]).reset_index(drop=True)
    return df


@lru_cache(maxsize=1)
def get_featured_dataset() -> pd.DataFrame:
    """Engineered dataset (cached).  All rolling/trend features computed here."""
    raw = load_raw_dataset()
    return engineer_features(raw)


def build_asset_report(asset_id, featured_df: pd.DataFrame | None = None,
                       raw_df: pd.DataFrame | None = None) -> dict:
    """Build a complete health report for a single asset, using the latest
    cycle as the current state."""
    if featured_df is None:
        featured = get_featured_dataset()
        featured_df = featured[featured["asset_id"] == asset_id].copy()
    if raw_df is None:
        raw = load_raw_dataset()
        raw_df = raw[raw["asset_id"] == asset_id].copy()

    if len(featured_df) == 0:
        raise KeyError(f"Asset '{asset_id}' not found in dataset.")

    ml_scores = score_asset(featured_df)

    rul_score = ml_scores["rul_score"]
    anomaly_severity = ml_scores["anomaly_severity"]
    anomaly_health = ml_scores["anomaly_health"]

    readiness_result = assess_readiness(rul_score, anomaly_health)
    maintenance_result = assess_maintenance(
        rul_score=rul_score,
        anomaly_severity=anomaly_severity,
        mission_readiness=readiness_result["mission_readiness"],
        predicted_rul=ml_scores["predicted_rul_cycles"],
    )

    sensor_evidence = get_sensor_changes(
        raw_df, sensors=SENSORS_FOR_EXPLANATION, top_n=5
    )

    unit_id = int(featured_df["unit_id"].iloc[0])
    source = str(featured_df["source"].iloc[0])

    report = {
        "asset_id": int(asset_id),
        "unit_id": unit_id,
        "source": source,
        "current_cycle": ml_scores["current_cycle"],
        "predicted_rul_cycles": ml_scores["predicted_rul_cycles"],
        "rul_score": rul_score,
        "anomaly_score": ml_scores["anomaly_score"],
        "anomaly_severity": anomaly_severity,
        "anomaly_health": anomaly_health,
        "mission_readiness": readiness_result["mission_readiness"],
        "status": readiness_result["status"],
        "maintenance_priority_score": maintenance_result["maintenance_priority_score"],
        "maintenance_priority": maintenance_result["maintenance_priority"],
        "recommendation": maintenance_result["recommendation"],
        "sensor_evidence": sensor_evidence,
    }
    return report


@lru_cache(maxsize=1)
def get_fleet_snapshot() -> list[dict]:
    """Compute (and cache) a health report for every asset in the dataset."""
    featured = get_featured_dataset()
    raw = load_raw_dataset()

    reports = []
    for asset_id in featured["asset_id"].unique():
        feat_asset = featured[featured["asset_id"] == asset_id].copy()
        raw_asset = raw[raw["asset_id"] == asset_id].copy()
        reports.append(build_asset_report(asset_id, feat_asset, raw_asset))

    reports.sort(key=lambda r: r["maintenance_priority_score"], reverse=True)
    return reports


def get_asset_ids() -> list[int]:
    """Return all asset IDs in the dataset."""
    df = load_raw_dataset()
    return sorted(df["asset_id"].unique().tolist())


def get_asset_report(asset_id) -> dict:
    """Return the full report (including telemetry history) for one asset."""
    normalised = _normalise_asset_id(asset_id)
    report = build_asset_report(normalised)
    raw = load_raw_dataset()
    raw_asset = raw[raw["asset_id"] == normalised].sort_values("cycle")
    telemetry_cols = ["cycle"] + CORE_SENSORS + ["RUL"]
    telemetry = raw_asset[telemetry_cols].tail(10).to_dict(orient="records")
    for row in telemetry:
        for k, v in row.items():
            if hasattr(v, "item"):
                row[k] = v.item()
    report["telemetry_history"] = telemetry
    return report


def get_fleet_summary() -> dict:
    """Aggregate counts across the whole fleet."""
    fleet = get_fleet_snapshot()
    total = len(fleet)
    ready = sum(1 for r in fleet if r["status"] == "READY")
    caution = sum(1 for r in fleet if r["status"] == "CAUTION")
    critical = sum(1 for r in fleet if r["status"] == "CRITICAL")
    high_priority = sum(1 for r in fleet if r["maintenance_priority"] == "HIGH")
    return {
        "total_assets": total,
        "ready": ready,
        "caution": caution,
        "critical": critical,
        "high_priority": high_priority,
    }


def get_maintenance_plan() -> dict:
    """Fleet-wide maintenance plan grouped by priority level."""
    fleet = get_fleet_snapshot()
    plan = {"high": [], "medium": [], "low": []}
    key_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
    for r in fleet:
        key = key_map[r["maintenance_priority"]]
        plan[key].append(r)
    return plan