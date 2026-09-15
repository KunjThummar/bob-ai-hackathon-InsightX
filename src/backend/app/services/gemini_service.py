"""
Gemini Copilot — explanation layer ONLY.

Gemini receives the structured ML health report and explains the existing
result in natural language.  It MUST NOT:
  - predict RUL
  - calculate anomaly scores
  - modify ML values
  - override READY/CAUTION/CRITICAL
  - invent sensor values or component failures
  - claim an asset is safe to operate
"""

import os

from pydantic import BaseModel

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


class CopilotResult(BaseModel):
    available: bool
    source: str  # "gemini" | "fallback"
    explanation: str
    message: str | None = None


def _build_prompt(report: dict) -> str:
    evidence_lines = ""
    for item in report.get("sensor_evidence", []):
        evidence_lines += (
            f"- {item['sensor']}: {item['direction']} by {item['change_percent']}% recently\n"
        )

    return f"""You are an AI maintenance decision-support copilot.

Analyze the following equipment health assessment produced by an ML pipeline.

IMPORTANT RULES:
- Use ONLY the supplied information.
- Do NOT invent component failures.
- Do NOT invent sensor values.
- Do NOT change the predicted RUL.
- Do NOT override the ML classification.
- Sensor changes are evidence of an evolving operating pattern,
  NOT proof of a specific component failure.
- Do NOT provide unsafe operational instructions.
- Do NOT claim the asset is safe to operate.
- Keep the explanation concise and professional.

ASSET HEALTH DATA
-----------------
Asset ID: {report['asset_id']}
Current Cycle: {report['current_cycle']}

Predicted RUL: {report['predicted_rul_cycles']} cycles
RUL Score: {report['rul_score']}/100

Anomaly Severity: {report['anomaly_severity']}/100

Mission Readiness: {report['mission_readiness']}/100
Status: {report['status']}

Maintenance Priority: {report['maintenance_priority']}
Maintenance Priority Score: {report['maintenance_priority_score']}/100

Recommended Action:
{report['recommendation']}

Telemetry Evidence:
{evidence_lines}

Respond using exactly these sections:

ASSESSMENT:
Explain the current health state in 2-3 sentences.

KEY EVIDENCE:
Give 3-5 concise bullet points based only on the supplied data.

RECOMMENDED ACTION:
Explain the recommended maintenance action in one concise paragraph.
"""


def _fallback_explanation(report: dict) -> str:
    """Deterministic explanation built from the ML results when Gemini is
    unavailable.  It repeats the computed values and does not invent anything."""
    evidence_lines = ""
    for item in report.get("sensor_evidence", []):
        evidence_lines += (
            f"- {item['sensor']}: {item['direction']} by {item['change_percent']}% recently\n"
        )

    return f"""ASSESSMENT:
Asset {report['asset_id']} is classified as {report['status']} with a mission-readiness
score of {report['mission_readiness']}/100. The model estimates approximately
{report['predicted_rul_cycles']} cycles of remaining useful life and an anomaly
severity of {report['anomaly_severity']}/100.

KEY EVIDENCE:
- Predicted RUL: {report['predicted_rul_cycles']} cycles (RUL score {report['rul_score']}/100)
- Anomaly severity: {report['anomaly_severity']}/100
- Mission readiness: {report['mission_readiness']}/100
- Maintenance priority: {report['maintenance_priority']} (score {report['maintenance_priority_score']}/100)
{evidence_lines}
RECOMMENDED ACTION:
{report['recommendation']}"""


def explain(report: dict) -> CopilotResult:
    """Generate a natural-language explanation of the ML health report.

    If Gemini is unavailable (no API key, network error, etc.), a deterministic
    fallback explanation built from the ML results is returned instead.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return CopilotResult(
            available=False,
            source="fallback",
            message="GEMINI_API_KEY not set; using deterministic fallback explanation.",
            explanation=_fallback_explanation(report),
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=_build_prompt(report),
        )
        text = getattr(response, "text", "") or ""
        if not text:
            raise RuntimeError("Empty response from Gemini.")
        return CopilotResult(
            available=True,
            source="gemini",
            explanation=text,
        )
    except Exception as exc:
        return CopilotResult(
            available=False,
            source="fallback",
            message=f"Gemini unavailable ({type(exc).__name__}); using deterministic fallback explanation.",
            explanation=_fallback_explanation(report),
        )