from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetryCycle(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    cycle: int = Field(gt=0)
    T24: float
    T30: float
    T50: float
    P15: float
    P30: float
    Nf: float
    Nc: float
    Ps30: float
    phi: float
    NRf: float
    NRc: float
    BPR: float
    W31: float
    W32: float
    htBleed: float


class CustomPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(min_length=1, max_length=64)
    cycles: list[TelemetryCycle] = Field(min_length=10, max_length=10)

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("asset_id must not be empty")
        if not all(ch.isalnum() or ch in "-_" for ch in value):
            raise ValueError("asset_id may contain only letters, numbers, hyphens, and underscores")
        return value
