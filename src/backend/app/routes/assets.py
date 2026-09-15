from fastapi import APIRouter, HTTPException

from ..services.dataset_service import get_fleet_snapshot, get_asset_report

router = APIRouter()


@router.get("/api/assets")
async def list_assets():
    """All assets in the dataset with their latest health result."""
    try:
        return get_fleet_snapshot()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/api/assets/{asset_id}")
async def asset(asset_id: str):
    """Detailed health report for a single asset, including sensor evidence
    and a compact telemetry history."""
    try:
        return get_asset_report(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))