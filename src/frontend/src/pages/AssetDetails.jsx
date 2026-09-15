import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../services/api";
import StatusBadge from "../components/StatusBadge";
import SensorEvidence from "../components/SensorEvidence";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function AssetDetails() {
  const { assetId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.getAsset(assetId)
      .then((d) => { if (mounted) { setData(d); setLoading(false); } })
      .catch((e) => { if (mounted) { setError(e.message); setLoading(false); } });
    return () => { mounted = false; };
  }, [assetId]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="Asset not found." />;

  return (
    <div>
      <div style={{ marginBottom: 22 }}>
        <Link to="/fleet" className="btn btn-ghost" style={{ marginBottom: 12, textDecoration: "none" }}>
          ← Back to Fleet
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
          <h2 className="page-title" style={{ margin: 0 }}>Asset {data.asset_id}</h2>
          <StatusBadge status={data.status} />
        </div>
        <p className="page-subtitle" style={{ marginTop: 6 }}>
          Unit ID: {data.unit_id} · Source: {data.source} · Current Cycle: {data.current_cycle}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 18 }}>
        <div className="result-card">
          <h3>Mission Readiness</h3>
          <div className="result-grid">
            <div className="result-cell" style={{ borderTop: "3px solid #059669" }}>
              <div className="rc-label">Mission Readiness</div>
              <div className="rc-value">{data.mission_readiness?.toFixed(1) ?? "—"}</div>
            </div>
            <div className="result-cell" style={{ borderTop: "3px solid var(--accent)" }}>
              <div className="rc-label">Status</div>
              <div className="rc-value" style={{ fontSize: 15 }}><StatusBadge status={data.status} /></div>
            </div>
            <div className="result-cell" style={{ borderTop: "3px solid #6366F1" }}>
              <div className="rc-label">Predicted RUL</div>
              <div className="rc-value">{data.predicted_rul_cycles?.toFixed(1) ?? "—"} <span style={{ fontSize: 13, fontWeight: 400, color: "var(--text-muted)" }}>cycles</span></div>
            </div>
            <div className="result-cell">
              <div className="rc-label">RUL Score</div>
              <div className="rc-value">{data.rul_score?.toFixed(1) ?? "—"}</div>
            </div>
            <div className="result-cell" style={{ borderTop: "3px solid #D97706" }}>
              <div className="rc-label">Anomaly Severity</div>
              <div className="rc-value">{data.anomaly_severity?.toFixed(1) ?? "—"}</div>
            </div>
            <div className="result-cell">
              <div className="rc-label">Anomaly Health</div>
              <div className="rc-value">{data.anomaly_health?.toFixed(1) ?? "—"}</div>
            </div>
          </div>
        </div>

        <div className="result-card">
          <h3>Maintenance Priority</h3>
          <div className="result-grid">
            <div className="result-cell" style={{ borderTop: "3px solid #DC2626" }}>
              <div className="rc-label">Priority Score</div>
              <div className="rc-value">{data.maintenance_priority_score?.toFixed(1) ?? "—"}</div>
            </div>
            <div className="result-cell" style={{ borderTop: "3px solid var(--accent)" }}>
              <div className="rc-label">Priority Level</div>
              <div className="rc-value" style={{ fontSize: 15 }}><StatusBadge status={data.maintenance_priority} /></div>
            </div>
            <div className="result-cell">
              <div className="rc-label">Anomaly Score</div>
              <div className="rc-value">{data.anomaly_score?.toFixed(4) ?? "—"}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="card-title">Recommendation</div>
        <p style={{ margin: 0, lineHeight: 1.7, fontSize: 13.5 }}>{data.recommendation}</p>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="card-title">
          Sensor Evidence
          <span className="muted">Top 5 changes</span>
        </div>
        <SensorEvidence evidence={data.sensor_evidence} />
      </div>

      <div className="card">
        <div className="card-title">
          Telemetry History
          <span className="muted">Last 10 cycles</span>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Cycle</th>
                <th className="num">T24</th>
                <th className="num">T30</th>
                <th className="num">T50</th>
                <th className="num">P15</th>
                <th className="num">P30</th>
                <th className="num">Nf</th>
                <th className="num">Nc</th>
                <th className="num">Ps30</th>
                <th className="num">phi</th>
                <th className="num">NRf</th>
                <th className="num">NRc</th>
                <th className="num">BPR</th>
                <th className="num">W31</th>
                <th className="num">W32</th>
                <th className="num">htBleed</th>
                <th className="num">RUL</th>
              </tr>
            </thead>
            <tbody>
              {data.telemetry_history?.slice().reverse().map((row, i) => (
                <tr key={i}>
                  <td>{row.cycle}</td>
                  <td className="num">{row.T24?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.T30?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.T50?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.P15?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.P30?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.Nf?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.Nc?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.Ps30?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.phi?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.NRf?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.NRc?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.BPR?.toFixed(3) ?? "—"}</td>
                  <td className="num">{row.W31?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.W32?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.htBleed?.toFixed(1) ?? "—"}</td>
                  <td className="num">{row.RUL ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}