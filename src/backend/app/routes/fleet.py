from fastapi import APIRouter, HTTPException

from ..schemas.prediction_response import FleetResponse
from ..services.dataset_service import get_fleet_summary, get_fleet_snapshot

router = APIRouter()


@router.get("/api/fleet")
async def fleet():
    """Fleet-wide summary + per-asset health snapshot (latest cycle)."""
    try:
        summary = get_fleet_summary()
        assets = get_fleet_snapshot()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"summary": summary, "assets": assets}