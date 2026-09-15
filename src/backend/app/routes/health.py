from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health():
    """Service health check."""
    return {"status": "ok", "service": "mission-readiness-api"}