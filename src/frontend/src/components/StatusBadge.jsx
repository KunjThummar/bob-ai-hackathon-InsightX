export default function StatusBadge({ status }) {
  const map = {
    READY: "badge-ready",
    CAUTION: "badge-caution",
    CRITICAL: "badge-critical",
    HIGH: "badge-high",
    MEDIUM: "badge-medium",
    LOW: "badge-low",
  };
  return <span className={`badge ${map[status] || ""}`}>{status}</span>;
}