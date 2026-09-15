// Centralised API client for the Mission Readiness Copilot frontend.
// All HTTP requests go through this module — no fetch() scattered in UI.

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  };
  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new Error("Backend is unavailable. Please check that the API server is running.");
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body && body.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore body parse failure
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  // 204 No Content or empty body
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  getHealth() {
    return request("/api/health");
  },
  getFleet() {
    return request("/api/fleet");
  },
  getAssets() {
    return request("/api/assets");
  },
  getAsset(assetId) {
    return request(`/api/assets/${encodeURIComponent(assetId)}`);
  },
  getMaintenance() {
    return request("/api/maintenance");
  },
  customPrediction(data) {
    return request("/api/custom-prediction", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  customPredictionUpload(file, assetId) {
    const form = new FormData();
    if (assetId) form.append("asset_id", assetId);
    form.append("file", file);
    return request("/api/custom-prediction/upload", {
      method: "POST",
      headers: {}, // let the browser set the multipart boundary
      body: form,
    });
  },
  getCopilotExplanation(assetId) {
    return request(`/api/copilot/${encodeURIComponent(assetId)}`);
  },
};

export default api;