import StatusBadge from "./StatusBadge";

export default function SensorEvidence({ evidence = [] }) {
  if (!evidence.length) return <div className="empty-state">No significant sensor changes detected.</div>;
  return (
    <div className="evidence-list">
      {evidence.map((item, idx) => (
        <div key={idx} className="evidence-item">
          <span className="sensor-name">{item.sensor}</span>
          <span className="sensor-change">
            {item.direction} by {item.change_percent?.toFixed(3)}%
            <StatusBadge status={item.direction === "increased" ? "CAUTION" : item.direction === "decreased" ? "LOW" : "READY"} />
          </span>
        </div>
      ))}
    </div>
  );
}