import { useEffect, useState } from "react";
import { api } from "../services/api";
import AssetTable from "../components/AssetTable";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function Fleet() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [sort, setSort] = useState({ key: "", dir: "asc" });

  useEffect(() => {
    let mounted = true;
    api.getAssets()
      .then((d) => { if (mounted) { setAssets(d); setLoading(false); } })
      .catch((e) => { if (mounted) { setError(e.message); setLoading(false); } });
    return () => { mounted = false; };
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div>
      <div style={{ marginBottom: 22 }}>
        <h2 className="page-title">Fleet Overview</h2>
        <p className="page-subtitle">
          {assets.length} assets · Click a row for the detailed health report
        </p>
      </div>
      <AssetTable
        assets={assets}
        search={search}
        statusFilter={statusFilter}
        priorityFilter={priorityFilter}
        onSearchChange={setSearch}
        onStatusChange={setStatusFilter}
        onPriorityChange={setPriorityFilter}
        onSort={setSort}
        sortKey=""
        sortDir="asc"
      />
    </div>
  );
}