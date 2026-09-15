"""
Generate fleet-wide predictions from the actual dataset.

Applies the EXACT same pipeline as the notebook (cells 8-12):
  1. Load the actual dataset.
  2. Engineer features (rolling mean / std / trend, window = 10).
  3. Run the saved RUL Random Forest model.
  4. Run the saved Isolation Forest anomaly model.
  5. Compute anomaly severity / health.
  6. Compute RUL score.
  7. Compute mission readiness + READY / CAUTION / CRITICAL.
  8. Compute maintenance priority + HIGH / MEDIUM / LOW.
  9. Generate sensor evidence.
  10. Generate the fleet-wide prioritised maintenance ranking.

Run once after training:  python backend/scripts/generate_predictions.py
"""

import json
import os
import sys

# Make the app package importable.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

from services.dataset_service import get_fleet_snapshot, get_fleet_summary, get_maintenance_plan  # noqa: E402


OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data"
)


def main():
    print("Generating fleet-wide predictions from the actual dataset ...")
    summary = get_fleet_summary()
    fleet = get_fleet_snapshot()
    plan = get_maintenance_plan()

    print("\n=== Fleet Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\n=== Top 10 highest-priority assets ===")
    for r in fleet[:10]:
        print(
            f"  {r['asset_id']:>8}  cycle={r['current_cycle']:>4}  "
            f"RUL={r['predicted_rul_cycles']:>7.2f}  "
            f"readiness={r['mission_readiness']:>6.2f}  "
            f"status={r['status']:<8}  "
            f"priority={r['maintenance_priority_score']:>6.2f}  "
            f"level={r['maintenance_priority']}"
        )

    print("\n=== Maintenance plan counts ===")
    for level in ["high", "medium", "low"]:
        print(f"  {level.upper()}: {len(plan[level])} assets")

    # Save for offline reference (the API still computes from the live cache).
    output = {
        "summary": summary,
        "fleet": fleet,
        "maintenance_plan": {
            "high": plan["high"],
            "medium": plan["medium"],
            "low": plan["low"],
        },
    }
    out_path = os.path.join(OUTPUT_DIR, "fleet_predictions.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved fleet predictions to {out_path}")

    # Also dump a per-engine full telemetry score file.
    engine_out = os.path.join(OUTPUT_DIR, "engine_scores.csv")
    rows = []
    for r in fleet:
        rows.append({
            "asset_id": r["asset_id"],
            "unit_id": r["unit_id"],
            "source": r["source"],
            "current_cycle": r["current_cycle"],
            "predicted_rul_cycles": r["predicted_rul_cycles"],
            "rul_score": r["rul_score"],
            "anomaly_severity": r["anomaly_severity"],
            "anomaly_health": r["anomaly_health"],
            "mission_readiness": r["mission_readiness"],
            "status": r["status"],
            "maintenance_priority_score": r["maintenance_priority_score"],
            "maintenance_priority": r["maintenance_priority"],
        })
    pd.DataFrame(rows).to_csv(engine_out, index=False)
    print(f"Saved engine scores to {engine_out}")
    print("\nDone.")


if __name__ == "__main__":
    import pandas as pd  # needed for the CSV dump
    main()
