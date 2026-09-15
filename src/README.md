# Mission Readiness & Predictive Maintenance Copilot

A complete web application for fleet health monitoring, predictive maintenance, and AI-assisted decision support built from NASA C-MAPSS FD001 turbofan engine simulation data.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend│
│  (Vite + React) │     │  (Python)       │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌───────────┐ ┌──────────────┐
              │ RUL Model│ │Anomaly Mdl│ │  Gemini LLM  │
              │(RandomFst)│ │(IsolationF)│ │ (Explanation)│
              └──────────┘ └───────────┘ └──────────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │   actual_dataset.csv │
                    │  (NASA C-MAPSS FD001)│
                    └──────────────────────┘
```

### Key Components

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18, Vite, React Router, Recharts | Dashboard, fleet view, asset details, maintenance plan, custom prediction, copilot |
| **Backend** | FastAPI, Uvicorn | REST API, ML inference, data pipeline |
| **ML Models** | scikit-learn (RandomForestRegressor, IsolationForest), RobustScaler | RUL prediction, anomaly detection |
| **Data** | Pandas, NumPy | Feature engineering, score computation |
| **AI Copilot** | Google Gemini (google-genai) | Natural-language explanation of ML results |

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download the actual dataset (NASA C-MAPSS FD001)
python scripts/download_dataset.py

# Train models (creates .pkl files in app/models/)
python scripts/train_models.py

# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env with API URL (defaults to http://localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

# Start dev server
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## Dataset

The application uses the **NASA C-MAPSS FD001** dataset from HuggingFace (`SoyVitou/NASA-C-MAPSS-Turbofan-Engine`).

- **Train set**: 100 engines (unit_id 1–100), 20,631 cycles total, each engine runs to failure (RUL→0)
- **Test set**: 100 engines (unit_id 1–100, overlapping IDs), 13,096 cycles, truncated at intermediate life stages
- **Combined**: 200 unique assets (train: 1–100, test: 1001–1100)

> **Note**: The train engines are at end-of-life in the dataset (RUL=0), so they appear as CRITICAL. The test engines provide diverse life stages for a realistic fleet mix.

### Sensor Columns

After removing 6 constant sensors (T2, P2, epr, farB, Nf_dmd, PCNfR_dmd), **15 core sensors** are retained:

```
T24, T30, T50, P15, P30, Nf, Nc, Ps30, phi, NRf, NRc, BPR, W31, W32, htBleed
```

---

## ML Pipeline (Faithful to Notebook)

### Feature Engineering
1. Drop 6 constant sensors
2. 10-cycle rolling **mean** per asset per sensor
3. 10-cycle rolling **std** per asset per sensor (min_periods=1, fillna=0)
4. 10-cycle rolling **trend/slope** per asset per sensor (min_periods=2, fillna=0)

### RUL Model
- **Algorithm**: RandomForestRegressor (n_estimators=150, max_depth=20, min_samples_leaf=2, random_state=42)
- **Features**: cycle, setting_1/2/3, 15 core sensors, 15 rolling means, 15 rolling stds, 15 rolling trends (64 total)
- **Target**: RUL (clipped at ≥0)
- **Validation**: 80/20 split by engine ID (random_state=42)
- **Metrics**: MAE≈24, RMSE≈33, R²≈0.75

### Anomaly Model
- **Healthy baseline**: RUL ≥ 100
- **Scaler**: RobustScaler (fitted on healthy data)
- **Algorithm**: IsolationForest (n_estimators=200, contamination=0.05, random_state=42)
- **Threshold**: 5th percentile of healthy decision scores
- **Severity calibration**: 0–100 from healthy_min/healthy_max

### Scoring Formulas

| Score | Formula |
|-------|---------|
| **RUL Score** | `clip((pred_rul / 150) * 100, 0, 100)` |
| **Anomaly Severity** | `clip((healthy_max - score) / (healthy_max - healthy_min) * 100, 0, 100)` |
| **Anomaly Health** | `100 - Anomaly Severity` |
| **Mission Readiness** | `clip(0.6 * RUL_Score + 0.4 * Anomaly_Health, 0, 100)` |
| **Readiness Category** | ≥80 READY, ≥50 CAUTION, <50 CRITICAL |
| **Maintenance Priority** | `clip(0.5*(100-RUL_Score) + 0.3*Anomaly_Severity + 0.2*(100-Readiness), 0, 100)` |
| **Priority Level** | ≥80 HIGH, ≥50 MEDIUM, <50 LOW |

### Recommendation Rules
- `RUL < 20 OR anomaly_severity ≥ 75` → HIGH + "Prioritize maintenance inspection and engineering review."
- `RUL < 60 OR anomaly_severity ≥ 40` → MEDIUM + "Schedule maintenance inspection and continue monitoring telemetry."
- Otherwise → LOW + "Continue routine monitoring and scheduled maintenance."

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| GET | `/api/fleet` | Fleet summary + all assets' latest health |
| GET | `/api/assets` | All assets (same as fleet assets) |
| GET | `/api/assets/{asset_id}` | Detailed asset report + sensor evidence + telemetry history |
| GET | `/api/maintenance` | Fleet-wide maintenance plan grouped by priority |
| POST | `/api/custom-prediction` | Run ML pipeline on 10-cycle JSON telemetry |
| POST | `/api/custom-prediction/upload` | Run ML pipeline on uploaded CSV telemetry |
| GET | `/api/copilot/{asset_id}` | Gemini explanation for a dataset asset |

### Custom Prediction Input (JSON)

```json
{
  "asset_id": "CUSTOM-001",
  "cycles": [
    {"cycle": 1, "T24": 643.0, "T30": 1585.0, ...},
    ...
    {"cycle": 10, "T24": 643.0, "T30": 1585.0, ...}
  ]
}
```

**Required fields**: `cycle` + all 15 core sensors. Exactly 10 cycles required.

### Custom Prediction CSV Format

```csv
cycle,T24,T30,T50,P15,P30,Nf,Nc,Ps30,phi,NRf,NRc,BPR,W31,W32,htBleed
1,643.0,1585.0,1398.0,21.6,553.0,2388.0,9050.0,47.2,521.7,2388.0,8125.0,8.4,38.8,23.4,392.0
...
```

Minimum 10 rows; first 10 used.

---

## Copilot (Gemini) Explanation

The Gemini layer is **purely explanatory** — it never modifies ML outputs.

- **Model**: `gemini-2.5-flash` (configurable via `GEMINI_MODEL` env var)
- **Input**: Structured ML health report (RUL, anomaly, readiness, priority, sensor evidence, recommendation)
- **Constraints**: Must not invent failures, override classifications, claim safety, or change numbers
- **Fallback**: If API key missing or Gemini unavailable, deterministic fallback explanation is returned

Set `GEMINI_API_KEY` in backend `.env` to enable.

---

## Running End-to-End

1. **Start backend** (terminal 1):
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start frontend** (terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open** `http://localhost:5173`

### Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — fleet metrics, readiness chart, top-risk assets, priority preview |
| `/fleet` | Searchable, filterable, sortable table of all 200 assets |
| `/assets/:assetId` | Detailed health report, sensor evidence, 10-cycle telemetry history |
| `/maintenance` | Prioritised maintenance plan (HIGH/MEDIUM/LOW) |
| `/custom-prediction` | Manual 10-cycle entry + CSV upload for custom telemetry |
| `/copilot` | Asset selector + Gemini/fallback explanation |

---

## Configuration

### Backend `.env`
```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8000
```

---

## Limitations & Honest Presentation

- **C-MAPSS is simulated benchmark data**, not real military fleet telemetry
- RUL model validation: MAE ≈ 24 cycles, RMSE ≈ 33 cycles, R² ≈ 0.75
- Healthy baseline (RUL ≥ 100) is a prototype assumption
- RUL reference (150 cycles) is a configurable normalisation constant
- Readiness weights (0.6/0.4) and thresholds are prototype design choices
- Sensor evidence indicates operating-pattern changes, **not component-level causality**
- System is **decision support only**, not autonomous operational authorization

---

## Development

### Project Structure

```
backend/
  app/
    main.py                 # FastAPI app, CORS, exception handlers
    routes/                 # API endpoints (health, fleet, assets, maintenance, custom, copilot)
    services/               # Core logic (dataset, features, prediction, readiness, maintenance, evidence, gemini)
    schemas/                # Pydantic request/response models
    models/                 # Saved .pkl models + metadata.json
    data/                   # actual_dataset.csv
  scripts/
    download_dataset.py     # Downloads from HuggingFace
    train_models.py         # Trains RUL + anomaly models, saves artefacts
    generate_predictions.py # Computes fleet snapshot (for offline inspection)
  requirements.txt
  .env

frontend/
  src/
    components/             # Reusable UI (Sidebar, MetricCard, AssetTable, etc.)
    pages/                  # Route components (Dashboard, Fleet, AssetDetails, etc.)
    services/api.js         # Centralised fetch wrapper
    App.jsx                 # Router + layout
    main.jsx                # Entry point
    index.css               # Design system (CSS custom properties)
  index.html
  package.json
  vite.config.js
```

### Re-training Models

```bash
cd backend
python scripts/train_models.py
```

This overwrites `app/models/*.pkl` and `metadata.json`.

---

## License

Prototype for IBM Bob AI Hackathon. Not for production use.