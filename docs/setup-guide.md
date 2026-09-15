# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10+
- Node.js 18+ and npm 9+
- A Google AI Studio account with a **Gemini API key** (for the Copilot explanation feature)

> No Docker, database, or IBM Cloud account required. The application runs fully locally.

---

## Project Structure

```
code/
├── backend/               # FastAPI Python backend
│   ├── app/
│   │   ├── main.py        # FastAPI entry point
│   │   ├── routes/        # API endpoint handlers
│   │   ├── services/      # ML inference, Gemini, dataset logic
│   │   ├── schemas/       # Pydantic models
│   │   ├── models/        # Saved .pkl model files (pre-trained)
│   │   └── data/          # actual_dataset.csv (NASA C-MAPSS FD001)
│   ├── scripts/
│   │   ├── download_dataset.py   # Downloads dataset from HuggingFace
│   │   └── train_models.py       # Trains RUL + anomaly models
│   ├── requirements.txt
│   └── .env
└── frontend/              # React + Vite frontend
    ├── src/
    │   ├── pages/         # Dashboard, Fleet, Maintenance, etc.
    │   ├── components/    # Reusable UI components
    │   └── services/api.js
    ├── package.json
    └── .env
```

---

## Environment Variables

### Backend — `backend/.env`

Create `backend/.env` with the following content:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (get from [aistudio.google.com](https://aistudio.google.com)) | Yes (Copilot feature) |
| `GEMINI_MODEL` | Gemini model to use | No (default: `gemini-2.5-flash`) |
| `CORS_ORIGINS` | Allowed frontend origins | No (default shown above) |

> If `GEMINI_API_KEY` is missing or invalid, the Copilot page will return a deterministic fallback explanation instead of an error — the rest of the app works fully without it.

### Frontend — `frontend/.env`

Create `frontend/.env` with:

```env
VITE_API_URL=http://localhost:8000
```

| Variable | Description | Required |
|---|---|---|
| `VITE_API_URL` | Backend API base URL | No (defaults to `http://localhost:8000`) |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Dataset + Model setup

> **Skip this step if `backend/app/models/` already contains `.pkl` files and `backend/app/data/actual_dataset.csv` exists** — the models are pre-trained and committed.

```bash
# (Inside backend/ with venv active)

# Download NASA C-MAPSS FD001 dataset from HuggingFace
python scripts/download_dataset.py

# Train RUL (Random Forest) + Anomaly (Isolation Forest) models
# Creates: app/models/rul_model.pkl, anomaly_model.pkl, anomaly_scaler.pkl, metadata.json
python scripts/train_models.py
```

Training takes approximately **2–5 minutes** depending on hardware.

### 4. Frontend setup

```bash
cd ../frontend

# Install Node dependencies
npm install
```

---

## Running the Application

Open **two separate terminals**:

**Terminal 1 — Backend:**

```bash
cd backend
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

| Service | URL |
|---|---|
| **Frontend (App)** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/api/health |

---

## Quick Demo

Once both servers are running, open **http://localhost:5173** and navigate to:

| Page | Route | What to do |
|---|---|---|
| Dashboard | `/` | View fleet KPI cards, readiness distribution chart, top 5 risk assets |
| Fleet | `/fleet` | Search/filter/sort all 200 assets; click any row for a detailed report |
| Maintenance | `/maintenance` | View the full HIGH/MEDIUM/LOW priority maintenance plan |
| Custom Prediction | `/custom-prediction` | Edit the pre-filled 10-cycle telemetry and click **Run Prediction** |
| Copilot | `/copilot` | Select any asset → **Generate Explanation** to get a Gemini AI health summary |

---

## Running Tests

```bash
cd backend
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pytest tests/ -v
```

> If no `tests/` directory exists, verify the API is healthy by visiting `http://localhost:8000/api/health` — it should return `{"status": "ok"}`.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| **Blank white page in browser** | Open DevTools Console (F12) and check for JS errors. Ensure `npm run dev` is running and `VITE_API_URL` in `frontend/.env` is correct. |
| **`ModuleNotFoundError` on backend start** | Run `pip install -r requirements.txt` again with the venv active. |
| **`uvicorn: command not found`** | Use `.venv\Scripts\uvicorn` (Windows) or ensure venv is activated. |
| **Backend starts but shows `model files not found`** | Run `python scripts/train_models.py` inside `backend/` with the venv active. |
| **`CORS` error in browser console** | Ensure `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`. |
| **Copilot returns "deterministic fallback"** | Set a valid `GEMINI_API_KEY` in `backend/.env`. Get one at [aistudio.google.com](https://aistudio.google.com) (free tier available). |
| **`dataset not found` error on backend start** | Run `python scripts/download_dataset.py` inside `backend/` — requires internet access. |
| **Port 8000 already in use** | Kill the existing process or change `--port` in the uvicorn command and update `VITE_API_URL` accordingly. |
| **`npm: command not found`** | Install Node.js 18+ from [nodejs.org](https://nodejs.org). |
| **venv was created at a different path (broken)** | Delete `backend/.venv/`, re-run `python -m venv .venv` and `pip install -r requirements.txt`. |
