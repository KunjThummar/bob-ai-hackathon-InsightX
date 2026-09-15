import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import MetricCard from "../components/MetricCard";
import ReadinessCard from "../components/ReadinessCard";
import StatusBadge from "../components/StatusBadge";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.getFleet()
      .then((d) => { if (mounted) setData(d); })
      .catch((e) => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No data returned." />;

  const { summary, assets } = data;
  const topRisk = assets.slice(0, 5);

  return (
    <div>
      <div className="metrics-grid">
        <MetricCard label="Total Assets"   value={summary.total_assets}  color="#1D4ED8" />
        <MetricCard label="Ready"          value={summary.ready}         sub="Healthy"     color="#059669" />
        <MetricCard label="Caution"        value={summary.caution}       sub="Monitor"     color="#D97706" />
        <MetricCard label="Critical"       value={summary.critical}      sub="Urgent"      color="#DC2626" />
        <MetricCard label="High Priority"  value={summary.high_priority} sub="Needs action" color="#DC2626" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 18 }}>
        <ReadinessCard assets={assets} />
        <div className="card">
          <div className="card-title">
            Highest-Risk Assets
            <span className="muted">Top 5</span>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th className="num">RUL</th>
                  <th className="num">Anomaly</th>
                  <th className="num">Readiness</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {topRisk.map((a) => (
                  <tr key={a.asset_id}>
                    <td>
                      <Link
                        to={`/assets/${a.asset_id}`}
                        style={{ color: "var(--accent)", fontWeight: 500, textDecoration: "none" }}
                      >
                        {a.asset_id}
                      </Link>
                    </td>
                    <td className="num">{a.predicted_rul_cycles?.toFixed(1) ?? "—"}</td>
                    <td className="num">{a.anomaly_severity?.toFixed(1) ?? "—"}</td>
                    <td className="num">{a.mission_readiness?.toFixed(1) ?? "—"}</td>
                    <td><StatusBadge status={a.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          Maintenance Priority Preview
          <span className="muted">{assets.length} assets total</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
          <div className="result-cell" style={{ borderTop: "3px solid #DC2626" }}>
            <div className="rc-label">High</div>
            <div className="rc-value" style={{ color: "#DC2626" }}>
              {assets.filter((a) => a.maintenance_priority === "HIGH").length}
              <span style={{ fontSize: 14, fontWeight: 400, color: "var(--text-muted)", marginLeft: 5 }}>assets</span>
            </div>
          </div>
          <div className="result-cell" style={{ borderTop: "3px solid #D97706" }}>
            <div className="rc-label">Medium</div>
            <div className="rc-value" style={{ color: "#D97706" }}>
              {assets.filter((a) => a.maintenance_priority === "MEDIUM").length}
              <span style={{ fontSize: 14, fontWeight: 400, color: "var(--text-muted)", marginLeft: 5 }}>assets</span>
            </div>
          </div>
          <div className="result-cell" style={{ borderTop: "3px solid #059669" }}>
            <div className="rc-label">Low</div>
            <div className="rc-value" style={{ color: "#059669" }}>
              {assets.filter((a) => a.maintenance_priority === "LOW").length}
              <span style={{ fontSize: 14, fontWeight: 400, color: "var(--text-muted)", marginLeft: 5 }}>assets</span>
            </div>
          </div>
        </div>
        <Link to="/maintenance" className="btn btn-primary" style={{ textDecoration: "none" }}>
          View Full Maintenance Plan →
        </Link>
      </div>
    </div>
  );
}