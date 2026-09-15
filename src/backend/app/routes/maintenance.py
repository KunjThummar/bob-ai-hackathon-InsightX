from fastapi import APIRouter, HTTPException

from ..services.dataset_service import get_maintenance_plan

router = APIRouter()


@router.get("/api/maintenance")
async def maintenance():
    """Fleet-wide prioritised maintenance plan grouped by priority level."""
    try:
        return get_maintenance_plan()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))