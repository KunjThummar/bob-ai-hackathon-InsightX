import { useEffect, useState } from "react";
import { Bot } from "lucide-react";
import { api } from "../services/api";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

const SOURCE_LABEL = {
  gemini: "Gemini AI",
  fallback: "Deterministic fallback",
};

export default function Copilot() {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [assetLoading, setAssetLoading] = useState(true);
  const [assetError, setAssetError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.getAssets()
      .then((d) => { if (mounted) { setAssets(d); setAssetLoading(false); } })
      .catch((e) => { if (mounted) { setAssetError(e.message); setAssetLoading(false); } });
    return () => { mounted = false; };
  }, []);

  const handleExplain = async () => {
    if (!selectedAsset) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.getCopilotExplanation(selectedAsset);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (assetLoading) return <Loading />;
  if (assetError) return <ErrorMessage message={assetError} />;

  return (
    <div>
      <div style={{ marginBottom: 22 }}>
        <h2 className="page-title">Copilot Explanation</h2>
        <p className="page-subtitle">
          Select an asset to receive a natural-language AI explanation of its ML health assessment.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="card-title">
          Select Asset
          <span className="muted">{assets.length} assets available</span>
        </div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div className="field" style={{ flex: 1, minWidth: 280 }}>
            <label>Asset</label>
            <select
              value={selectedAsset}
              onChange={(e) => setSelectedAsset(e.target.value)}
              disabled={!assets.length}
            >
              <option value="">— Choose an asset —</option>
              {assets.map((a) => (
                <option key={a.asset_id} value={a.asset_id}>
                  {a.asset_id} (unit {a.unit_id}, {a.status}, priority {a.maintenance_priority})
                </option>
              ))}
            </select>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleExplain}
            disabled={!selectedAsset || loading}
          >
            {loading ? (
              <>
                <span className="spinner" />
                Generating…
              </>
            ) : (
              <>
                <Bot size={16} strokeWidth={2} />
                Generate Explanation
              </>
            )}
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {result && (
        <div className="page-enter">
          {/* ML Health Summary */}
          <div className="card" style={{ marginBottom: 18 }}>
            <div className="card-title">
              <span>ML Health Summary</span>
              <span className="muted">Asset {result.asset_id}</span>
            </div>
            <div className="result-grid">
              <div className="result-cell" style={{ borderTop: "3px solid var(--accent)" }}>
                <div className="rc-label">Status</div>
                <div className="rc-value" style={{ fontSize: 16 }}>{result.ml_results.status}</div>
              </div>
              <div className="result-cell" style={{ borderTop: "3px solid #059669" }}>
                <div className="rc-label">Mission Readiness</div>
                <div className="rc-value">{result.ml_results.mission_readiness?.toFixed(1)}</div>
              </div>
              <div className="result-cell" style={{ borderTop: "3px solid #6366F1" }}>
                <div className="rc-label">Predicted RUL</div>
                <div className="rc-value">{result.ml_results.predicted_rul_cycles?.toFixed(1)} <span style={{ fontSize: 13, fontWeight: 400, color: "var(--text-muted)" }}>cycles</span></div>
              </div>
              <div className="result-cell" style={{ borderTop: "3px solid #D97706" }}>
                <div className="rc-label">Anomaly Severity</div>
                <div className="rc-value">{result.ml_results.anomaly_severity?.toFixed(1)}</div>
              </div>
              <div className="result-cell" style={{ borderTop: "3px solid #DC2626" }}>
                <div className="rc-label">Maintenance Priority</div>
                <div className="rc-value" style={{ fontSize: 16 }}>{result.ml_results.maintenance_priority}</div>
              </div>
            </div>
            <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid rgba(180,200,220,0.3)" }}>
              <div style={{ fontSize: 11.5, color: "var(--text-muted)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                Recommendation
              </div>
              <div style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--text)" }}>
                {result.ml_results.recommendation}
              </div>
            </div>
          </div>

          {/* Copilot Explanation Bubble */}
          <div className="copilot-section">
            <div className="card">
              <div className="card-title">
                <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
                  <Bot size={16} strokeWidth={2} color="#3B82F6" />
                  Copilot Explanation
                </span>
                <span className="muted">
                  {SOURCE_LABEL[result.source] ?? result.source}
                  {result.message && ` — ${result.message}`}
                </span>
              </div>
              <div className="copilot-box">{result.explanation}</div>
              <div className="copilot-note">
                ℹ️ This explanation is generated from the ML model outputs above. It does not modify or override the model's predictions.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}