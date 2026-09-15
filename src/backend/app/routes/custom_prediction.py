import io
import re

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import ValidationError

from ..schemas.custom_prediction import CustomPredictionRequest
from ..schemas.prediction_response import AssetHealthReport
from ..services.dataset_service import load_raw_dataset
from ..services.evidence_service import get_sensor_changes, SENSORS_FOR_EXPLANATION
from ..services.feature_service import CORE_SENSORS, engineer_features
from ..services.maintenance_service import assess_maintenance
from ..services.prediction_service import load_models, score_asset
from ..services.readiness_service import assess_readiness

router = APIRouter()

REQUIRED_COLUMNS = ["cycle"] + CORE_SENSORS
MIN_CYCLES = 10


def _default_setting_values() -> dict:
    """Derive sensible defaults for the operating-setting columns from the
    actual training dataset (not invented)."""
    try:
        raw = load_raw_dataset()
        train = raw[raw["source"] == "train"]
        return {
            "setting_1": float(train["setting_1"].mean()),
            "setting_2": float(train["setting_2"].mean()),
            "setting_3": float(train["setting_3"].mode().iloc[0]),
        }
    except Exception:
        return {"setting_1": 0.0, "setting_2": 0.0, "setting_3": 100.0}


def _score_custom(asset_id: str, cycles_df: pd.DataFrame) -> dict:
    """Run the SAME pipeline as dataset-mode on a single custom asset."""
    defaults = _default_setting_values()

    cycles_df = cycles_df.copy()
    cycles_df["asset_id"] = asset_id
    cycles_df["setting_1"] = defaults["setting_1"]
    cycles_df["setting_2"] = defaults["setting_2"]
    cycles_df["setting_3"] = defaults["setting_3"]
    cycles_df["dataset"] = "FD001"
    cycles_df["split"] = "custom"
    cycles_df["source"] = "custom"
    cycles_df["unit_id"] = 0
    cycles_df = cycles_df.sort_values("cycle").reset_index(drop=True)

    featured = engineer_features(cycles_df)
    ml_scores = score_asset(featured)

    readiness_result = assess_readiness(ml_scores["rul_score"], ml_scores["anomaly_health"])
    maintenance_result = assess_maintenance(
        rul_score=ml_scores["rul_score"],
        anomaly_severity=ml_scores["anomaly_severity"],
        mission_readiness=readiness_result["mission_readiness"],
        predicted_rul=ml_scores["predicted_rul_cycles"],
    )

    sensor_evidence = get_sensor_changes(
        cycles_df, sensors=SENSORS_FOR_EXPLANATION, top_n=5
    )

    return {
        "asset_id": asset_id,
        "current_cycle": ml_scores["current_cycle"],
        "predicted_rul_cycles": ml_scores["predicted_rul_cycles"],
        "rul_score": ml_scores["rul_score"],
        "anomaly_score": ml_scores["anomaly_score"],
        "anomaly_severity": ml_scores["anomaly_severity"],
        "anomaly_health": ml_scores["anomaly_health"],
        "mission_readiness": readiness_result["mission_readiness"],
        "status": readiness_result["status"],
        "maintenance_priority_score": maintenance_result["maintenance_priority_score"],
        "maintenance_priority": maintenance_result["maintenance_priority"],
        "recommendation": maintenance_result["recommendation"],
        "sensor_evidence": sensor_evidence,
    }


@router.post("/api/custom-prediction")
async def custom_prediction(request: CustomPredictionRequest):
    """Run the ML pipeline on user-provided 10-cycle telemetry."""
    try:
        load_models()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    cycles_df = pd.DataFrame([c.model_dump() for c in request.cycles])
    return _score_custom(request.asset_id, cycles_df)


@router.post("/api/custom-prediction/upload")
async def custom_prediction_upload(
    asset_id: str | None = None,
    file: UploadFile = None,
):
    """Run the ML pipeline on telemetry uploaded as CSV."""
    try:
        load_models()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if file is None:
        raise HTTPException(status_code=400, detail="No CSV file provided.")

    if asset_id is None:
        asset_id = "CUSTOM-CSV"
    asset_id = asset_id.strip()
    if not asset_id:
        raise HTTPException(status_code=400, detail="asset_id must not be empty")
    if not re.match(r"^[A-Za-z0-9_-]{1,64}$", asset_id):
        raise HTTPException(
            status_code=400,
            detail="asset_id may contain only letters, numbers, hyphens, and underscores",
        )

    contents = await file.read()
    try:
        cycles_df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")

    missing = [c for c in REQUIRED_COLUMNS if c not in cycles_df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}",
        )

    for col in REQUIRED_COLUMNS:
        cycles_df[col] = pd.to_numeric(cycles_df[col], errors="coerce")
    if cycles_df[REQUIRED_COLUMNS].isnull().any().any():
        raise HTTPException(
            status_code=400,
            detail="CSV contains non-numeric or missing values in required columns.",
        )

    if len(cycles_df) < MIN_CYCLES:
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain at least {MIN_CYCLES} cycles (got {len(cycles_df)}).",
        )

    return _score_custom(asset_id, cycles_df)