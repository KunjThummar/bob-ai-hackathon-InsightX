import { useEffect, useState } from "react";
import { api } from "../services/api";
import MaintenancePlan from "../components/MaintenancePlan";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function Maintenance() {
  const [plan, setPlan] = useState({ high: [], medium: [], low: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.getMaintenance()
      .then((d) => { if (mounted) { setPlan(d); setLoading(false); } })
      .catch((e) => { if (mounted) { setError(e.message); setLoading(false); } });
    return () => { mounted = false; };
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;

  const total = plan.high.length + plan.medium.length + plan.low.length;

  return (
    <div>
      <div style={{ marginBottom: 22 }}>
        <h2 className="page-title">Maintenance Plan</h2>
        <p className="page-subtitle">
          Fleet-wide prioritised maintenance ranking — {total} assets total
        </p>
      </div>
      <MaintenancePlan plan={plan} />
    </div>
  );
}