import { useState, useMemo } from "react";
import StatusBadge from "./StatusBadge";

const DEFAULT_COLS = [
  { key: "asset_id", label: "Asset", width: "100px" },
  { key: "current_cycle", label: "Cycle", className: "num", width: "80px" },
  { key: "predicted_rul_cycles", label: "Pred. RUL", className: "num", width: "100px" },
  { key: "anomaly_severity", label: "Anomaly", className: "num", width: "90px" },
  { key: "mission_readiness", label: "Readiness", className: "num", width: "100px" },
  { key: "status", label: "Status", width: "110px" },
  { key: "maintenance_priority", label: "Priority", width: "110px" },
];

export default function AssetTable({
  assets = [],
  search = "",
  statusFilter = "",
  priorityFilter = "",
  onSearchChange,
  onStatusChange,
  onPriorityChange,
  onSort,
  sortKey = "",
  sortDir = "asc",
}) {
  const [sort, setSort] = useState({ key: sortKey, dir: sortDir });

  const filtered = useMemo(() => {
    let result = assets;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((a) =>
        String(a.asset_id).toLowerCase().includes(q) ||
        String(a.unit_id).toLowerCase().includes(q)
      );
    }
    if (statusFilter) {
      result = result.filter((a) => a.status === statusFilter);
    }
    if (priorityFilter) {
      result = result.filter((a) => a.maintenance_priority === priorityFilter);
    }
    if (sort.key) {
      result = [...result].sort((a, b) => {
        const av = a[sort.key];
        const bv = b[sort.key];
        if (av === bv) return 0;
        const dir = sort.dir === "asc" ? 1 : -1;
        return av < bv ? -dir : dir;
      });
    }
    return result;
  }, [assets, search, statusFilter, priorityFilter, sort]);

  const handleHeaderClick = (key) => {
    if (!onSort) return;
    let dir = "asc";
    if (sort.key === key && sort.dir === "asc") dir = "desc";
    onSort(key, dir);
  };

  const statuses = ["READY", "CAUTION", "CRITICAL"];
  const priorities = ["HIGH", "MEDIUM", "LOW"];

  return (
    <div>
      <div className="toolbar">
        <div className="search">
          <input
            type="text"
            placeholder="Search asset ID or unit ID…"
            value={search}
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
        </div>
        <select className="filter" value={statusFilter} onChange={(e) => onStatusChange?.(e.target.value)}>
          <option value="">All Status</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="filter" value={priorityFilter} onChange={(e) => onPriorityChange?.(e.target.value)}>
          <option value="">All Priority</option>
          {priorities.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              {DEFAULT_COLS.map((col) => (
                <th
                  key={col.key}
                  style={{ width: col.width }}
                  onClick={() => handleHeaderClick(col.key)}
                >
                  {col.label}
                  {sort.key === col.key && (
                    <span style={{ marginLeft: 4 }}>{sort.dir === "asc" ? "▲" : "▼"}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((asset) => (
              <tr key={asset.asset_id}>
                <td>{asset.asset_id}</td>
                <td className="num">{asset.current_cycle}</td>
                <td className="num">{asset.predicted_rul_cycles?.toFixed(1) ?? "—"}</td>
                <td className="num">{asset.anomaly_severity?.toFixed(1) ?? "—"}</td>
                <td className="num">{asset.mission_readiness?.toFixed(1) ?? "—"}</td>
                <td><StatusBadge status={asset.status} /></td>
                <td><StatusBadge status={asset.maintenance_priority} /></td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={DEFAULT_COLS.length} className="empty-state">No assets match the current filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}