"""
Maintenance priority & recommendation layer.

Priority formula (notebook cell 9):

  Priority = clip(
      0.5 * (100 - RUL_Score)
    + 0.3 * Anomaly_Severity
    + 0.2 * (100 - Mission_Readiness),
    0, 100
  )

Priority levels:
  >= 80  -> HIGH
  >= 50  -> MEDIUM
  <  50  -> LOW

Recommendation rules (notebook cell 11):
  RUL < 20 OR anomaly_severity >= 75  -> HIGH  + "Prioritize maintenance ..."
  RUL < 60 OR anomaly_severity >= 40  -> MEDIUM + "Schedule maintenance ..."
  otherwise                          -> LOW    + "Continue routine monitoring ..."
"""

import numpy as np

# Weights for the maintenance-priority blend.
RUL_CONCERN_WEIGHT = 0.5
ANOMALY_CONCERN_WEIGHT = 0.3
READINESS_CONCERN_WEIGHT = 0.2

# Priority level thresholds.
HIGH_PRIORITY_THRESHOLD = 80
MEDIUM_PRIORITY_THRESHOLD = 50

# Recommendation rule thresholds (notebook cell 11).
RUL_HIGH_THRESHOLD = 20
ANOMALY_HIGH_THRESHOLD = 75
RUL_MEDIUM_THRESHOLD = 60
ANOMALY_MEDIUM_THRESHOLD = 40


def compute_maintenance_priority(
    rul_score: float, anomaly_severity: float, mission_readiness: float
) -> float:
    """Compute the 0-100 maintenance-priority score (notebook cell 9)."""
    score = (
        RUL_CONCERN_WEIGHT * (100 - rul_score)
        + ANOMALY_CONCERN_WEIGHT * anomaly_severity
        + READINESS_CONCERN_WEIGHT * (100 - mission_readiness)
    )
    return float(np.clip(score, 0, 100))


def priority_level(score: float) -> str:
    """Bucket a priority score into HIGH / MEDIUM / LOW."""
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "HIGH"
    elif score >= MEDIUM_PRIORITY_THRESHOLD:
        return "MEDIUM"
    else:
        return "LOW"


def generate_recommendation(
    predicted_rul: float, anomaly_severity: float, readiness: float
) -> tuple[str, str]:
    """
    Rule-based recommendation (notebook cell 11).

    Returns (priority_label, recommendation_text).  The priority label here
    is derived from RUL / anomaly thresholds (the notebook's rule-based
    priority), which may differ from the score-based priority_level above.
    For the dashboard we report the score-based level for consistency; this
    is retained to reproduce the notebook's recommendation text exactly.
    """
    if predicted_rul < RUL_HIGH_THRESHOLD or anomaly_severity >= ANOMALY_HIGH_THRESHOLD:
        priority = "HIGH"
        action = "Prioritize maintenance inspection and engineering review."
    elif predicted_rul < RUL_MEDIUM_THRESHOLD or anomaly_severity >= ANOMALY_MEDIUM_THRESHOLD:
        priority = "MEDIUM"
        action = "Schedule maintenance inspection and continue monitoring telemetry."
    else:
        priority = "LOW"
        action = "Continue routine monitoring and scheduled maintenance."
    return priority, action


def assess_maintenance(
    rul_score: float,
    anomaly_severity: float,
    mission_readiness: float,
    predicted_rul: float,
) -> dict:
    """Return priority score, level, and recommendation in one call."""
    priority_score = compute_maintenance_priority(
        rul_score, anomaly_severity, mission_readiness
    )
    level = priority_level(priority_score)
    _, recommendation = generate_recommendation(
        predicted_rul, anomaly_severity, mission_readiness
    )
    return {
        "maintenance_priority_score": round(priority_score, 2),
        "maintenance_priority": level,
        "recommendation": recommendation,
    }
