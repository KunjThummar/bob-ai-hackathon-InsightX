"""
Prediction service — runs the saved ML models and converts their raw
outputs into interpretable 0-100 scores.

Implements the exact score-conversion formulas from the notebook
(cells 8 & 11 of mission_readiness_copilot.ipynb):

  RUL Score        = clip((predicted_RUL / 150) * 100, 0, 100)
  Anomaly Severity = clip((healthy_max - score) / (healthy_max - healthy_min) * 100, 0, 100)
  Anomaly Health   = 100 - Anomaly Severity

The underlying Random Forest and Isolation Forest models are trained once by
``scripts/train_models.py`` and loaded here — never retrained per request.
"""

import json
import os

import joblib
import numpy as np
import pandas as pd

from .feature_service import (
    CORE_SENSORS,
    ROLLING_WINDOW,
    engineer_features,
    get_anomaly_feature_columns,
    get_rul_feature_columns,
)

_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"
)

# RUL normalisation reference (notebook: "150 cycles chosen as a practical
# fully-healthy ceiling").
RUL_REFERENCE = 150

# Module-level cache for loaded artefacts.
_MODEL_CACHE: dict | None = None


def load_models() -> dict:
    """Load (and cache) all saved model artefacts and metadata."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    rul_model_path = os.path.join(_MODELS_DIR, "rul_model.pkl")
    anomaly_model_path = os.path.join(_MODELS_DIR, "anomaly_model.pkl")
    scaler_path = os.path.join(_MODELS_DIR, "anomaly_scaler.pkl")
    metadata_path = os.path.join(_MODELS_DIR, "metadata.json")

    for p in [rul_model_path, anomaly_model_path, scaler_path, metadata_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(
                f"Required model artefact not found: {p}. "
                "Run 'python backend/scripts/train_models.py' first."
            )

    artifacts = {
        "rul_model": joblib.load(rul_model_path),
        "anomaly_model": joblib.load(anomaly_model_path),
        "anomaly_scaler": joblib.load(scaler_path),
        "metadata": json.load(open(metadata_path)),
    }
    _MODEL_CACHE = artifacts
    return artifacts


def _get_rul_input(df: pd.DataFrame, rul_feature_columns: list[str]) -> pd.DataFrame:
    """Select and order columns for the RUL model (keeps feature names)."""
    return df[rul_feature_columns]


def _get_anomaly_input(df: pd.DataFrame, anomaly_feature_columns: list[str]) -> pd.DataFrame:
    """Select and order columns for the anomaly model (keeps feature names)."""
    return df[anomaly_feature_columns]


def predict_rul(rul_model, feature_df: pd.DataFrame, feature_columns: list[str]) -> float:
    """Run the Random Forest RUL model and clamp to non-negative."""
    X = _get_rul_input(feature_df, feature_columns)
    prediction = rul_model.predict(X)
    return float(np.maximum(prediction[0], 0))


def compute_anomaly_score(
    anomaly_model, scaler, feature_df: pd.DataFrame, anomaly_feature_columns: list[str]
) -> tuple[float, np.ndarray]:
    """
    Return (anomaly_score, raw_decision_values) for the last row of *feature_df*.

    The Isolation Forest ``decision_function`` returns *higher = more normal*.
    """
    X = _get_anomaly_input(feature_df, anomaly_feature_columns)
    X_scaled = scaler.transform(X)
    scores = anomaly_model.decision_function(X_scaled)
    return float(scores[-1]), scores


def compute_rul_score(predicted_rul: float, reference: float = RUL_REFERENCE) -> float:
    """Normalise predicted RUL cycles to a 0-100 score (notebook cell 8)."""
    return float(np.clip((predicted_rul / reference) * 100, 0, 100))


def compute_anomaly_severity(
    anomaly_score: float, healthy_min: float, healthy_max: float
) -> tuple[float, float]:
    """
    Convert the raw Isolation Forest decision score into a 0-100 anomaly
    severity and the inverted anomaly-health score (notebook cell 8).
    """
    health_denom = healthy_max - healthy_min
    if health_denom == 0:
        severity = 0.0
    else:
        severity = float(
            np.clip(
                (healthy_max - anomaly_score) / health_denom * 100,
                0,
                100,
            )
        )
    health = float(np.clip(100 - severity, 0, 100))
    return severity, health


def score_asset(feature_df: pd.DataFrame) -> dict:
    """
    Given a feature-engineered DataFrame for a *single* asset (all of its
    rows, sorted by cycle), return every ML-derived score for the latest row.

    This function is identical for dataset-mode and custom-prediction-mode
    — both call it with a single-asset feature DataFrame.
    """
    artifacts = load_models()
    meta = artifacts["metadata"]

    rul_cols = meta["rul_feature_columns"]
    anomaly_cols = meta["anomaly_feature_columns"]

    # Use the LAST row as the current / latest state.
    latest_row = feature_df.tail(1).copy()

    predicted_rul = predict_rul(artifacts["rul_model"], latest_row, rul_cols)
    anomaly_score, _ = compute_anomaly_score(
        artifacts["anomaly_model"],
        artifacts["anomaly_scaler"],
        latest_row,
        anomaly_cols,
    )

    rul_score = compute_rul_score(predicted_rul, meta.get("rul_reference", RUL_REFERENCE))
    anomaly_severity, anomaly_health = compute_anomaly_severity(
        anomaly_score,
        meta["healthy_min"],
        meta["healthy_max"],
    )

    return {
        "predicted_rul_cycles": round(predicted_rul, 2),
        "rul_score": round(rul_score, 2),
        "anomaly_score": round(anomaly_score, 4),
        "anomaly_severity": round(anomaly_severity, 2),
        "anomaly_health": round(anomaly_health, 2),
        "current_cycle": int(latest_row["cycle"].iloc[0]),
    }
