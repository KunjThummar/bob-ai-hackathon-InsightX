from fastapi import APIRouter, HTTPException

from ..schemas.prediction_response import CopilotResponse
from ..services.dataset_service import get_asset_report
from ..services.gemini_service import explain

router = APIRouter()


@router.get("/api/copilot/{asset_id}")
async def copilot(asset_id: str):
    """Generate a Gemini explanation for a dataset asset's ML results."""
    try:
        report = get_asset_report(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = explain(report)
    return CopilotResponse(
        asset_id=str(report["asset_id"]),
        available=result.available,
        source=result.source,
        ml_results=report,
        explanation=result.explanation,
        message=result.message,
    )