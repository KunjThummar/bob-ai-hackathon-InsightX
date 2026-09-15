import StatusBadge from "./StatusBadge";

export default function MaintenancePlan({ plan = { high: [], medium: [], low: [] } }) {
  const sections = [
    { key: "high", label: "HIGH PRIORITY", badge: "high", items: plan.high || [] },
    { key: "medium", label: "MEDIUM PRIORITY", badge: "medium", items: plan.medium || [] },
    { key: "low", label: "LOW PRIORITY", badge: "low", items: plan.low || [] },
  ];

  return (
    <div>
      {sections.map((section) => (
        <div key={section.key} className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">
            <span>{section.label}</span>
            <span className="muted">{section.items.length} assets</span>
          </div>
          {section.items.length === 0 ? (
            <div className="empty-state">No assets in this priority band.</div>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: "80px" }}>Asset</th>
                    <th className="num" style={{ width: "90px" }}>Priority</th>
                    <th className="num" style={{ width: "80px" }}>RUL</th>
                    <th className="num" style={{ width: "80px" }}>Anomaly</th>
                    <th className="num" style={{ width: "90px" }}>Readiness</th>
                    <th>Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {section.items.map((a) => (
                    <tr key={a.asset_id}>
                      <td>{a.asset_id}</td>
                      <td className="num">
                        <StatusBadge status={a.maintenance_priority} />
                        {a.maintenance_priority_score?.toFixed(1)}
                      </td>
                      <td className="num">{a.predicted_rul_cycles?.toFixed(1) ?? "—"}</td>
                      <td className="num">{a.anomaly_severity?.toFixed(1) ?? "—"}</td>
                      <td className="num">{a.mission_readiness?.toFixed(1) ?? "—"}</td>
                      <td style={{ maxWidth: 300, whiteSpace: "normal", wordWrap: "break-word" }}>
                        {a.recommendation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}