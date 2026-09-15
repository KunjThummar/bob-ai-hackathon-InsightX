# 🚀 InsightX — Mission Readiness & Predictive Maintenance Copilot

> AI-powered fleet health monitoring dashboard built for the IBM Bob AI Hackathon.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | InsightX |
| **Track** | AI |
| **Team Lead** | Daksh Vekariya — 24IT107@charusat.edu.in |
| **Members** | Kunj Thummar (24ce128@charusat.edu.in), Jayrajsinh Barad (24ce006@charusat.edu.in), Harsh Thesiya (24it099@charusat.edu.in) |

---

## 🎯 Problem Statement

Defence and industrial fleets lack real-time, data-driven visibility into asset health. Maintenance engineers currently rely on fixed schedules and manual log reviews, causing unplanned failures, excessive downtime, and wasted maintenance budgets — with no early warning until a component is already critically degraded.

---

## 💡 Solution

InsightX ingests turbofan engine telemetry (NASA C-MAPSS FD001), applies a Random Forest RUL predictor and Isolation Forest anomaly detector, and surfaces a per-asset **Mission Readiness score (0–100)** with priority-ranked maintenance actions. A Google Gemini-powered **AI Copilot** then translates ML outputs into natural-language health summaries that non-expert users can act on immediately.

---

## ✨ Key Features

- **Mission Readiness Score:** Real-time 0–100 composite health score (`0.6 × RUL_Score + 0.4 × Anomaly_Health`) for all 200 fleet assets, categorised as READY / CAUTION / CRITICAL
- **Predictive RUL Estimation:** Random Forest model trained on NASA C-MAPSS FD001 with 10-cycle rolling feature engineering (MAE ≈ 24 cycles, R² ≈ 0.75)
- **Anomaly Detection:** Isolation Forest with severity calibration and per-sensor evidence highlighting to show exactly which sensors are abnormal
- **Priority Maintenance Plan:** Fleet-wide HIGH / MEDIUM / LOW maintenance queue with per-asset recommendations and priority scores
- **AI Copilot:** Google Gemini generates natural-language health summaries — explanatory only, never overrides ML outputs

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, JavaScript (React/JSX) |
| **Frameworks** | FastAPI, React 18, Vite, React Router, Recharts |
| **IBM Technologies** | IBM Bob AI Hackathon Platform |
| **ML / AI** | scikit-learn (RandomForestRegressor, IsolationForest, RobustScaler), Google Gemini (google-genai) |
| **Data** | pandas, NumPy, NASA C-MAPSS FD001 (via HuggingFace) |
| **Other** | Uvicorn, GitHub Actions |

---

## 📁 Repository Structure

```
bob-ai-hackathon-InsightX/
├── src/                        # All source code
│   ├── backend/                # FastAPI + ML (Python)
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI entry point
│   │   │   ├── routes/         # API endpoint handlers
│   │   │   ├── services/       # ML inference, Gemini, dataset logic
│   │   │   ├── models/         # Pre-trained .pkl model files
│   │   │   └── data/           # NASA C-MAPSS FD001 CSV
│   │   └── scripts/            # Dataset download + model training
│   └── frontend/               # React 18 + Vite dashboard
│       └── src/
│           ├── pages/          # Dashboard, Fleet, Maintenance, Copilot, etc.
│           └── components/     # Reusable UI components
├── docs/                       # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                       # Demo artifacts
│   ├── screenshots/
│   └── demo-video-link.txt
├── presentation/               # Slide deck
└── submission.yaml             # Structured submission metadata
```

---

## ⚡ How to Run

> Full step-by-step instructions with troubleshooting in [`docs/setup-guide.md`](docs/setup-guide.md)

```bash
# 1. Clone the repo
git clone https://github.com/KunjThummar/bob-ai-hackathon-InsightX.git
cd bob-ai-hackathon-InsightX/src

# 2. Backend — create venv and install dependencies
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# 3. Dataset + Models (skip if .pkl files already exist in backend/app/models/)
python scripts/download_dataset.py
python scripts/train_models.py

# 4. Create backend/.env
# GEMINI_API_KEY=your_key_here      (optional — Copilot works without it)
# GEMINI_MODEL=gemini-2.5-flash
# CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# 5. Frontend
cd ../frontend
npm install

# 6. Run both servers (two terminals)
# Terminal 1 — Backend:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend:
npm run dev
```

| Service | URL |
|---|---|
| **App (Frontend)** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **Swagger / API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/api/health |

### Pages

| Route | Description |
|---|---|
| `/` | Dashboard — fleet KPI cards, readiness chart, top-risk assets |
| `/fleet` | Searchable, filterable, sortable table of all 200 assets |
| `/assets/:id` | Detailed health report, sensor evidence, 10-cycle telemetry history |
| `/maintenance` | Priority-ranked maintenance plan (HIGH / MEDIUM / LOW) |
| `/custom-prediction` | Manual 10-cycle telemetry entry + CSV upload |
| `/copilot` | Asset selector + Gemini AI health explanation |

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- **Simulated data:** NASA C-MAPSS FD001 is a benchmark dataset, not real military or industrial fleet telemetry
- **Model accuracy:** RUL model validation shows MAE ≈ 24 cycles and R² ≈ 0.75 — prototype grade, not production certified
- **Prototype thresholds:** Readiness weights (0.6/0.4) and category thresholds are design choices that need domain-expert validation
- **No authentication:** All API routes are open — the system is decision support only, not authorised for operational use
- **Train engines appear CRITICAL:** C-MAPSS train set engines run to failure (RUL = 0) by dataset design, so they always show CRITICAL status

---

## 🏅 What We're Most Proud Of

The **end-to-end ML pipeline** faithfully reproduces the NASA C-MAPSS notebook methodology: rolling feature engineering across 15 sensors, a well-calibrated IsolationForest anomaly detector with severity scoring, and a composite Mission Readiness formula that blends RUL and anomaly health into a single actionable metric.

The **Gemini Copilot layer** is designed to be genuinely useful without being dishonest — it generates natural-language explanations from ML outputs but is strictly constrained to never invent failures, change classifications, or override numbers. This keeps the system auditable and trustworthy.

---
