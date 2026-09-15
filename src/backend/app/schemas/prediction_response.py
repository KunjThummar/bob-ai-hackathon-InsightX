from typing import Literal

from pydantic import BaseModel, Field


class SensorEvidenceItem(BaseModel):
    sensor: str
    previous_mean: float
    recent_mean: float
    change_percent: float
    direction: Literal["increased", "decreased", "unchanged"]
    absolute_change_percent: float


class AssetHealthReport(BaseModel):
    asset_id: str | int
    unit_id: int | None = None
    source: str | None = None
    current_cycle: int
    predicted_rul_cycles: float
    rul_score: float
    anomaly_score: float
    anomaly_severity: float
    anomaly_health: float
    mission_readiness: float
    status: Literal["READY", "CAUTION", "CRITICAL"]
    maintenance_priority_score: float
    maintenance_priority: Literal["HIGH", "MEDIUM", "LOW"]
    recommendation: str
    sensor_evidence: list[SensorEvidenceItem]


class FleetSummary(BaseModel):
    total_assets: int
    ready: int
    caution: int
    critical: int
    high_priority: int


class FleetResponse(BaseModel):
    summary: FleetSummary
    assets: list[AssetHealthReport]


class MaintenancePlanResponse(BaseModel):
    high: list[AssetHealthReport]
    medium: list[AssetHealthReport]
    low: list[AssetHealthReport]


class CopilotResponse(BaseModel):
    asset_id: str
    available: bool
    source: Literal["gemini", "fallback"]
    ml_results: AssetHealthReport
    explanation: str
    message: str | None = None
