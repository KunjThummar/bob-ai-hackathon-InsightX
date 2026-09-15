export default function MetricCard({ label, value, sub, color }) {
  return (
    <div
      className="metric-card"
      style={color ? { borderLeft: `4px solid ${color}` } : undefined}
    >
      <div className="label">{label}</div>
      <div className="value" style={color ? { color } : undefined}>{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}