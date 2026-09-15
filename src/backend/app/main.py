import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Make the app package importable when running as a script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .routes.health import router as health_router  # noqa: E402
from .routes.fleet import router as fleet_router  # noqa: E402
from .routes.assets import router as assets_router  # noqa: E402
from .routes.maintenance import router as maintenance_router  # noqa: E402
from .routes.custom_prediction import router as custom_prediction_router  # noqa: E402
from .routes.copilot import router as copilot_router  # noqa: E402

app = FastAPI(
    title="Mission Readiness & Predictive Maintenance Copilot",
    version="1.0.0",
)

# --------------------------------------------------------------------------- #
# CORS — allow the React frontend (and Swagger-friendly local hosts).
# --------------------------------------------------------------------------- #
_env_origins = os.environ.get("CORS_ORIGINS", "")
_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
if not _origins:
    _origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Exception handling — clean error messages instead of crashes.
# --------------------------------------------------------------------------- #
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
app.include_router(health_router)
app.include_router(fleet_router)
app.include_router(assets_router)
app.include_router(maintenance_router)
app.include_router(custom_prediction_router)
app.include_router(copilot_router)


# --------------------------------------------------------------------------- #
# Startup — pre-warm the model cache and dataset snapshot.
# --------------------------------------------------------------------------- #
@app.on_event("startup")
def _warmup():
    try:
        from .services.prediction_service import load_models

        load_models()
    except Exception as exc:
        print(f"[startup] Model warm-up failed (endpoints will return 503): {exc}")

    try:
        from .services.dataset_service import get_fleet_snapshot

        get_fleet_snapshot()
    except Exception as exc:
        print(f"[startup] Dataset warm-up failed (endpoints will return 503): {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)