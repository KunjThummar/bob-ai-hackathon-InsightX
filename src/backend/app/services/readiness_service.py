"""
Mission-readiness scoring — combines RUL Score and Anomaly Health into a
single 0-100 Mission Readiness Index and bucket it into READY / CAUTION /
CRITICAL.

Formula (notebook cell 8):

  Mission Readiness = clip(0.6 * RUL_Score + 0.4 * Anomaly_Health, 0, 100)

Thresholds (notebook cell 8):

  >= 80  -> READY
  >= 50  -> CAUTION
  <  50  -> CRITICAL
"""

import numpy as np

# Health-normalised reference used for the RUL Score (notebook cell 8).
RUL_REFERENCE = 150

# Weights in the blended readiness index.
RUL_WEIGHT = 0.6
ANOMALY_WEIGHT = 0.4

# Readiness category thresholds.
READY_THRESHOLD = 80
CAUTION_THRESHOLD = 50


def compute_mission_readiness(rul_score: float, anomaly_health: float) -> float:
    """Blend RUL Score and Anomaly Health into a 0-100 readiness score."""
    score = RUL_WEIGHT * rul_score + ANOMALY_WEIGHT * anomaly_health
    return float(np.clip(score, 0, 100))


def readiness_category(readiness: float) -> str:
    """Bucket a readiness score into READY / CAUTION / CRITICAL."""
    if readiness >= READY_THRESHOLD:
        return "READY"
    elif readiness >= CAUTION_THRESHOLD:
        return "CAUTION"
    else:
        return "CRITICAL"


def assess_readiness(rul_score: float, anomaly_health: float) -> dict:
    """Return mission_readiness score + category in one call."""
    readiness = compute_mission_readiness(rul_score, anomaly_health)
    return {
        "mission_readiness": round(readiness, 2),
        "status": readiness_category(readiness),
    }
