import { useState } from "react";
import { api } from "../services/api";
import CustomInputTable from "../components/CustomInputTable";
import PredictionResult from "../components/PredictionResult";
import ErrorMessage from "../components/ErrorMessage";

const DEFAULT_CYCLES = Array.from({ length: 10 }, (_, i) => ({
  cycle: i + 1,
  T24: 643.0, T30: 1585.0, T50: 1398.0, P15: 21.6,
  P30: 553.0, Nf: 2388.0, Nc: 9050.0, Ps30: 47.2, phi: 521.7,
  NRf: 2388.0, NRc: 8125.0, BPR: 8.4, W31: 38.8, W32: 23.4, htBleed: 392.0,
}));

export default function CustomPrediction() {
  const [cycles, setCycles] = useState(DEFAULT_CYCLES);
  const [assetId, setAssetId] = useState("CUSTOM-001");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.customPrediction({ asset_id: assetId, cycles });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    setUploadLoading(true);
    setUploadError(null);
    setResult(null);
    try {
      const data = await api.customPredictionUpload(file, assetId);
      setResult(data);
    } catch (e) {
      setUploadError(e.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleClear = () => {
    setCycles(DEFAULT_CYCLES);
    setAssetId("CUSTOM-001");
    setResult(null);
    setError(null);
    setUploadError(null);
  };

  return (
    <div>
      <div style={{ marginBottom: 22 }}>
        <h2 className="page-title">Custom Prediction</h2>
        <p className="page-subtitle">
          Enter 10 consecutive telemetry cycles or upload a CSV file to run the ML pipeline on your data.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="card-title">
          Option 1: Manual Entry
          <span className="muted">10 cycles required</span>
        </div>
        <CustomInputTable
          cycles={cycles}
          onChange={setCycles}
          assetId={assetId}
          onAssetIdChange={setAssetId}
        />
        <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={handlePredict} disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" />
                Running…
              </>
            ) : "Run Prediction"}
          </button>
          <button className="btn btn-ghost" onClick={handleClear} disabled={loading}>
            Clear
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="card-title">
          Option 2: CSV Upload
          <span className="muted">≥10 rows required</span>
        </div>
        <p style={{ margin: "0 0 14px", fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6 }}>
          CSV must contain columns: <code style={{ fontSize: 12, background: "rgba(0,0,0,0.05)", padding: "1px 5px", borderRadius: 4 }}>cycle, T24, T30, T50, P15, P30, Nf, Nc, Ps30, phi, NRf, NRc, BPR, W31, W32, htBleed</code>.
          At least 10 rows required. The first 10 rows will be used.
        </p>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileUpload(file);
          }}
          style={{ marginBottom: 12, display: "block", fontSize: 13, color: "var(--text-muted)" }}
        />
        <button
          className="btn btn-primary"
          disabled={uploadLoading}
          onClick={() => document.querySelector('input[type="file"]')?.click()}
        >
          {uploadLoading ? (
            <>
              <span className="spinner" />
              Uploading…
            </>
          ) : "Upload & Predict"}
        </button>
      </div>

      {(error || uploadError) && <ErrorMessage message={error || uploadError} />}
      <PredictionResult result={result} loading={loading || uploadLoading} error={error || uploadError} />
    </div>
  );
}