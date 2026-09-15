import Loading from "./Loading";
import ErrorMessage from "./ErrorMessage";
import StatusBadge from "./StatusBadge";
import SensorEvidence from "./SensorEvidence";

export default function PredictionResult({ result, loading, error }) {
  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (!result) return <div className="empty-state">Enter telemetry and click Run Prediction.</div>;

  return (
    <div className="result-card">
      <h3>Custom Prediction — Generated from User-Provided Telemetry</h3>
      <div className="result-grid">
        <div className="result-cell">
          <div className="rc-label">Mission Readiness</div>
          <div className="rc-value">{result.mission_readiness?.toFixed(1) ?? "—"}</div>
        </div>
        <div className="result-cell">
          <div className="rc-label">Status</div>
          <div className="rc-value"><StatusBadge status={result.status} /></div>
        </div>
        <div className="result-cell">
          <div className="rc-label">Predicted RUL</div>
          <div className="rc-value">{result.predicted_rul_cycles?.toFixed(1) ?? "—"} cycles</div>
        </div>
        <div className="result-cell">
          <div className="rc-label">RUL Score</div>
          <div className="rc-value">{result.rul_score?.toFixed(1) ?? "—"}</div>
        </div>
        <div className="result-cell">
          <div className="rc-label">Anomaly Severity</div>
          <div className="rc-value">{result.anomaly_severity?.toFixed(1) ?? "—"}</div>
        </div>
        <div className="result-cell">
          <div className="rc-label">Maintenance Priority</div>
          <div className="rc-value">
            <StatusBadge status={result.maintenance_priority} />
            {result.maintenance_priority_score?.toFixed(1)}
          </div>
        </div>
      </div>
      <div style={{ marginBottom: 12 }}>
        <strong>Recommendation:</strong> {result.recommendation}
      </div>
      <SensorEvidence evidence={result.sensor_evidence} />
    </div>
  );
}