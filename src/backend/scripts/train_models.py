"""
Train and save all ML artefacts for the Mission Readiness Copilot.

This script reproduces, end-to-end, the training logic from
``mission_readiness_copilot.ipynb`` (cells 1-11):

  1. Load the actual FD001 dataset (backend/app/data/actual_dataset.csv).
  2. Drop the six constant sensors.
  3. Build the 10-cycle rolling mean / std and trend features.
  4. Split engines 80 / 20 (random_state=42) — same as the notebook.
  5. Train the Random Forest RUL regressor.
  6. Train RobustScaler + Isolation Forest on the healthy baseline (RUL >= 100).
  7. Calibrate the anomaly threshold (5th percentile of healthy scores).
  8. Report validation metrics (MAE, RMSE, R²).
  9. Save models + metadata.json.

Run once:  python backend/scripts/train_models.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

# Make the app package importable.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

from services.feature_service import (  # noqa: E402
    CORE_SENSORS,
    CONSTANT_SENSORS,
    ROLLING_WINDOW,
    engineer_features,
    get_anomaly_feature_columns,
    get_rul_feature_columns,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "app", "data", "actual_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "app", "models")

# --- Notebook cell 11: recommendation thresholds (mirrored for metadata) ---
RUL_HIGH = 20
ANOMALY_HIGH = 75
RUL_MEDIUM = 60
ANOMALY_MEDIUM = 40


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 2. Load dataset (notebook cell 2)
    # ------------------------------------------------------------------ #
    print("Loading dataset ...")
    df = pd.read_csv(DATA_PATH)
    # Training uses only the 'train' source (the notebook trains on train_df).
    train_df = df[df["source"] == "train"].copy()
    print(f"Train rows: {len(train_df)}  |  unique units: {train_df['unit_id'].nunique()}")

    # ------------------------------------------------------------------ #
    # 3-4. Feature engineering (notebook cells 4-5)
    # ------------------------------------------------------------------ #
    print("Engineering features ...")
    train_features = engineer_features(train_df)
    print(f"Feature columns (total): {len(train_features.columns)}")

    # ------------------------------------------------------------------ #
    # 5. Train / validation split by engine (notebook cell 4 / 5)
    # ------------------------------------------------------------------ #
    engine_ids = train_features["unit_id"].unique()
    train_engines, val_engines = train_test_split(
        engine_ids, test_size=0.20, random_state=42
    )
    model_train = train_features[
        train_features["unit_id"].isin(train_engines)
    ].copy()
    model_val = train_features[
        train_features["unit_id"].isin(val_engines)
    ].copy()
    print(f"Training engines: {len(train_engines)} | Validation engines: {len(val_engines)}")

    # ------------------------------------------------------------------ #
    # 6. RUL model — Random Forest (notebook cell 6)
    # ------------------------------------------------------------------ #
    rul_feature_columns = get_rul_feature_columns(model_train)
    anomaly_feature_columns = get_anomaly_feature_columns(train_features)

    X_train = model_train[rul_feature_columns]
    y_train = model_train["RUL"]
    X_val = model_val[rul_feature_columns]
    y_val = model_val["RUL"]

    print("Training RUL model (RandomForestRegressor) ...")
    rul_model = RandomForestRegressor(
        n_estimators=150,
        max_depth=20,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    rul_model.fit(X_train, y_train)
    print("RUL model training complete.")

    y_pred = rul_model.predict(X_val)
    y_pred = np.maximum(y_pred, 0)  # RUL cannot be negative (notebook cell 6)

    mae = mean_absolute_error(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    r2 = r2_score(y_val, y_pred)
    print(f"Validation  MAE={mae:.2f}  RMSE={rmse:.2f}  R²={r2:.4f}")

    # ------------------------------------------------------------------ #
    # 7-8. Anomaly model — RobustScaler + IsolationForest (notebook cell 7)
    # ------------------------------------------------------------------ #
    X_anomaly_val = model_val[anomaly_feature_columns].copy()

    # Healthy baseline: RUL >= 100 (notebook cell 7).
    healthy_mask = train_features["RUL"] >= 100
    X_healthy = train_features.loc[healthy_mask, anomaly_feature_columns]
    print(f"Healthy training samples: {len(X_healthy)}")

    scaler = RobustScaler()
    X_healthy_scaled = scaler.fit_transform(X_healthy)

    anomaly_model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    anomaly_model.fit(X_healthy_scaled)
    print("Anomaly detector trained.")

    # Calibrate threshold: 5th percentile of healthy scores (notebook cell 7).
    healthy_scores = anomaly_model.decision_function(X_healthy_scaled)
    anomaly_threshold = float(np.percentile(healthy_scores, 5))
    healthy_min = float(healthy_scores.min())
    healthy_max = float(healthy_scores.max())
    print(f"Anomaly threshold: {anomaly_threshold:.4f}")
    print(f"Healthy score range: [{healthy_min:.4f}, {healthy_max:.4f}]")

    # ------------------------------------------------------------------ #
    # 9. Save artefacts
    # ------------------------------------------------------------------ #
    import joblib

    joblib.dump(rul_model, os.path.join(MODELS_DIR, "rul_model.pkl"))
    joblib.dump(anomaly_model, os.path.join(MODELS_DIR, "anomaly_model.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "anomaly_scaler.pkl"))

    metadata = {
        "core_sensors": CORE_SENSORS,
        "constant_sensors": CONSTANT_SENSORS,
        "rolling_window": ROLLING_WINDOW,
        "rul_feature_columns": rul_feature_columns,
        "anomaly_feature_columns": anomaly_feature_columns,
        "healthy_min": healthy_min,
        "healthy_max": healthy_max,
        "anomaly_threshold": anomaly_threshold,
        "healthy_rul_threshold": 100,
        "anomaly_percentile": 5,
        "rul_reference": 150,
        "readiness_thresholds": {"ready": 80, "caution": 50, "critical": 0},
        "priority_thresholds": {"high": 80, "medium": 50, "low": 0},
        "recommendation_thresholds": {
            "rul_high": RUL_HIGH,
            "anomaly_high": ANOMALY_HIGH,
            "rul_medium": RUL_MEDIUM,
            "anomaly_medium": ANOMALY_MEDIUM,
        },
        "readiness_weights": {"rul": 0.6, "anomaly": 0.4},
        "priority_weights": {
            "rul_concern": 0.5,
            "anomaly_concern": 0.3,
            "readiness_concern": 0.2,
        },
        "validation_metrics": {
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "r2": round(float(r2), 4),
        },
        "model_params": {
            "rul_model": {
                "type": "RandomForestRegressor",
                "n_estimators": 150,
                "max_depth": 20,
                "min_samples_leaf": 2,
                "random_state": 42,
            },
            "anomaly_model": {
                "type": "IsolationForest",
                "n_estimators": 200,
                "contamination": 0.05,
                "random_state": 42,
            },
            "scaler": "RobustScaler",
        },
        "training_summary": {
            "n_train_engines": int(len(train_engines)),
            "n_val_engines": int(len(val_engines)),
            "n_healthy_samples": int(len(X_healthy)),
            "total_train_rows": int(len(train_features)),
        },
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved models to {MODELS_DIR}/")
    print("  - rul_model.pkl")
    print("  - anomaly_model.pkl")
    print("  - anomaly_scaler.pkl")
    print("  - metadata.json")


if __name__ == "__main__":
    main()
