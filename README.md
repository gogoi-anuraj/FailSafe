# FAILSAFE — Early Student Failure Detection & Intervention System

> An AI-powered web platform that helps faculty identify at-risk students early, understand the root causes of their struggles, and take targeted action before it's too late.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Backend API](#backend-api)
- [Frontend](#frontend)
- [Local Setup](#local-setup)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Dataset](#dataset)
- [Live Demo](#live-demo)

---

## Overview

In educational institutions, student failure often goes undetected until end-of-semester results — leaving no room for meaningful intervention. Faculty lack a proactive, data-driven tool to identify at-risk students early and understand the root causes behind their struggles.

**FAILSAFE** addresses this by providing a web-based system where faculty can:

- Upload student data (individually or as a CSV batch)
- Get a **failure risk score** (0–100%) powered by an XGBoost ML model
- Understand **why** a student is flagged via SHAP (Explainable AI)
- Receive a **personalized intervention plan** written by Groq's LLaMA 3 LLM
- Track student risk trends over the semester on a dashboard

---

## Features

### Machine Learning
- **XGBoost Classifier** trained on the UCI Student Performance Dataset
- **Threshold tuning** — optimized for Recall to minimize missed at-risk students
- **SHAP Explanations** — shows which features drive each prediction
- **Risk bands** — LOW / MEDIUM / HIGH based on probability score

### Intervention Engine
- **Rule-based interventions** — 21 features mapped to specific faculty actions
- **Groq LLaMA 3.3-70b** — rewrites interventions into personalized, empathetic language
- **Silent fallback** — if Groq fails (rate limit, timeout, etc.), rule-based text is used automatically with no error shown to faculty

### Backend (FastAPI)
- JWT authentication for faculty accounts
- Single student assessment endpoint
- Batch CSV upload and processing
- Assessment history stored in PostgreSQL
- PDF export of individual or batch assessment reports
- Delete assessments, batches, or all records for a student

### Frontend (React)
- Dark-themed, professional UI built with Tailwind CSS v4
- Login and Signup pages
- Dashboard with risk distribution charts and paginated history table
- Upload page with single student form and drag-and-drop CSV upload
- Student detail page with risk trend chart, SHAP visualization, and intervention cards
- PDF export button per assessment

---

## Tech Stack

| Layer | Technology |
|---|---|
| Machine Learning | Python, XGBoost, scikit-learn, SHAP, Pandas, imbalanced-learn |
| LLM | Groq API (LLaMA 3.3-70b-versatile) |
| Backend | FastAPI, SQLAlchemy, PostgreSQL, JWT (python-jose), bcrypt |
| Frontend | React 18, Vite, Tailwind CSS v4, Recharts, Axios |
| PDF Export | ReportLab |
| Deployment | Render (backend), Vercel (frontend), Supabase (database) |

---

## Project Structure

```
failsafe/
│
├── notebooks/                          ← Jupyter notebooks (ML pipeline)
│   ├── 01_eda.ipynb                    ← Exploratory data analysis
│   ├── 02_preprocessing.ipynb          ← Feature selection, encoding, SMOTE
│   ├── 03_model_training.ipynb         ← XGBoost, threshold tuning, SHAP
│   ├── 04_intervention_engine_groq.ipynb    ← Groq LLM + rule fallback
│   │
│   ├── data/
│   │   ├── student-mat.csv             ← Raw dataset (UCI)
│   │   └── processed/
│   │       ├── X_train.csv
│   │       ├── X_test.csv
│   │       ├── y_train.csv
│   │       ├── y_test.csv
│   │       └── features.json
│   │
│   └── models/
│       ├── failsafe_model.pkl
│       ├── shap_explainer.pkl
│       ├── threshold_config.json
│       ├── best_params.json
│       └── metrics.json
│
├── backend/
│   ├── main.py                         ← FastAPI app, lifespan, CORS
│   ├── config.py                       ← Settings from environment variables
│   ├── database.py                     ← SQLAlchemy tables and session
│   ├── auth.py                         ← bcrypt + JWT utilities
│   ├── schemas.py                      ← Pydantic request/response models
│   ├── model_loader.py                 ← Lazy load
│   ├── intervention_engine_groq.py     ← Groq LLM + rule-based fallback
│   ├── download_models.py              ← Manual model download script
│   ├── setup_db.py                     ← Create tables + default user
│   ├── requirements.txt
│   ├── .env                            ← Local environment variables (not committed)
│   ├── .env.example                    ← Template for environment variables
│   ├── .gitignore
│   │
│   ├── routes/
│   │   ├── auth.py                     ← /auth/register, /auth/login, /auth/me
│   │   ├── predict.py                  ← /predict, /predict-batch, /assessment, /batch
│   │   └── dashboard.py                ← /dashboard/stats, /history, /student
│   │
│   ├── models/                         ← Model files go here (not in git)
│   │   ├── failsafe_model.pkl
│   │   ├── shap_explainer.pkl
│   │   └── threshold_config.json
│   │
│   └── data/processed/
│       └── features.json
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js                  ← Vite + Tailwind v4 + dev proxy
    ├── vercel.json                     ← React Router fix for Vercel
    ├── .env.example
    ├── .gitignore
    │
    └── src/
        ├── main.jsx
        ├── App.jsx                     ← Router + protected routes
        ├── index.css                   ← Tailwind v4 theme + component classes
        │
        ├── api/
        │   └── client.js               ← Axios instance with JWT + all API calls
        │
        ├── context/
        │   ├── AuthContext.js          ← React context (no components)
        │   ├── AuthProvider.jsx        ← Login/logout logic
        │   └── useAuth.js              ← useAuth hook
        │
        ├── components/
        │   ├── Navbar.jsx              ← Sidebar navigation
        │   ├── RiskBadge.jsx           ← Color-coded risk label
        │   ├── ShapChart.jsx           ← Horizontal SHAP bar chart
        │   └── InterventionCard.jsx    ← Priority-colored intervention card
        │
        └── pages/
            ├── Login.jsx
            ├── Signup.jsx              ← With password strength indicator
            ├── Dashboard.jsx           ← Stats, charts, paginated history
            ├── Upload.jsx              ← Single form + batch CSV upload
            └── StudentDetail.jsx       ← Risk trend, SHAP, interventions, PDF
```

---

## Machine Learning Pipeline

### Dataset
- **UCI Student Performance Dataset** — Math course (`student-mat.csv`)
- 395 students, 33 features
- Available on [Kaggle](https://www.kaggle.com/datasets/uciml/student-alcohol-consumption)

### Features Used (21 total)

| Category | Features |
|---|---|
| Academic | G1, G2, failures, studytime, absences |
| Behavioural | Dalc, Walc, goout, freetime, traveltime |
| Support | schoolsup, famsup, paid, activities, internet, higher |
| Background | Medu, Fedu, famrel, health, romantic |

### Dropped Features
`school`, `sex`, `age`, `address`, `famsize`, `Pstatus`, `guardian`, `reason`, `nursery`, `Mjob`, `Fjob`, `G3` (target)

### Target Variable
```
at_risk = 1  if G3 < 10  (failing)
at_risk = 0  if G3 >= 10 (passing)
```

### Model
- **Algorithm**: XGBoost Classifier
- **Imbalance handling**: SMOTE (on training set only)
- **Tuning**: GridSearchCV optimized for Recall (5-fold stratified CV)
- **Threshold**: Tuned below 0.5 to maximize recall (catch more at-risk students)
- **Explainability**: SHAP TreeExplainer

### Risk Bands
| Band | Probability |
|---|---|
| 🟢 LOW | < 35% |
| 🟡 MEDIUM | 35% – 65% |
| 🔴 HIGH | ≥ 65% |

---

## Backend API

### Authentication
All endpoints except `/auth/login` and `/auth/register` require a Bearer JWT token in the `Authorization` header.

### All Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Create a faculty account |
| POST | `/auth/login` | No | Login, receive JWT token |
| GET | `/auth/me` | Yes | Get current user info |
| GET | `/template` | Yes | Download CSV upload template |
| POST | `/predict` | Yes | Assess a single student |
| POST | `/predict-batch` | Yes | Upload CSV, assess all students |
| GET | `/assessment/{id}` | Yes | Get a saved assessment |
| GET | `/assessment/{id}/pdf` | Yes | Export assessment as PDF |
| GET | `/batch/{batch_id}` | Yes | Get all assessments in a batch |
| GET | `/batch/{batch_id}/pdf` | Yes | Export batch as PDF report |
| DELETE | `/assessment/{id}` | Yes | Delete one assessment |
| DELETE | `/batch/{batch_id}` | Yes | Delete entire batch |
| DELETE | `/student/{id}` | Yes | Delete all records for a student |
| GET | `/dashboard/stats` | Yes | Overall stats and charts data |
| GET | `/dashboard/history` | Yes | Recent 50 assessments |
| GET | `/dashboard/student/{id}` | Yes | Student risk trend over time |
| GET | `/health` | No | Health check + model status |

### Student Input Fields

| Field | Type | Range | Description |
|---|---|---|---|
| `student_id` | string | — | Any identifier |
| `G1` | int | 0–20 | First period grade |
| `G2` | int | 0–20 | Second period grade |
| `absences` | int | 0–93 | Number of absences |
| `failures` | int | 0–3 | Past class failures |
| `studytime` | int | 1–4 | Weekly study time |
| `traveltime` | int | 1–4 | Travel time to school |
| `famrel` | int | 1–5 | Family relationship quality |
| `freetime` | int | 1–5 | Free time after school |
| `goout` | int | 1–5 | Going out with friends |
| `Dalc` | int | 1–5 | Weekday alcohol consumption |
| `Walc` | int | 1–5 | Weekend alcohol consumption |
| `health` | int | 1–5 | Current health status |
| `Medu` | int | 0–4 | Mother's education level |
| `Fedu` | int | 0–4 | Father's education level |
| `schoolsup` | 0 or 1 | — | Receiving school support |
| `famsup` | 0 or 1 | — | Family study support |
| `paid` | 0 or 1 | — | Extra paid classes |
| `activities` | 0 or 1 | — | Extracurricular activities |
| `higher` | 0 or 1 | — | Wants higher education |
| `internet` | 0 or 1 | — | Internet access at home |
| `romantic` | 0 or 1 | — | In a romantic relationship |

---

## Frontend

### Pages

| Route | Page | Description |
|---|---|---|
| `/login` | Login | Sign in with email and password |
| `/signup` | Signup | Create a new faculty account |
| `/dashboard` | Dashboard | Risk stats, charts, assessment history |
| `/upload` | Upload | Single student form or batch CSV |
| `/student/:id` | StudentDetail | Risk trend, SHAP, interventions, PDF |

### Key Features
- **Protected routes** — redirects to login if not authenticated
- **JWT auto-injection** — all API calls include the token automatically
- **401 handling** — clears token and redirects to login on expiry
- **Pagination** — 10 assessments per page on the dashboard
- **Drag and drop** — CSV upload supports drag and drop
- **PDF export** — downloads a formatted report per assessment

---

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+

### 1. Clone the Repository
```bash
git clone https://github.com/gogoi-anuraj/FailSafe.git
cd FailSafe
```

### 2. Run the Jupyter Notebooks

Install notebook dependencies:
```bash
pip install jupyter pandas scikit-learn xgboost shap matplotlib seaborn imbalanced-learn
```

Run in order:
```
notebooks/01_eda.ipynb
notebooks/02_preprocessing.ipynb
notebooks/03_model_training.ipynb
notebooks/04_intervention_engine_groq.ipynb
```

This produces the model files in `notebooks/models/`.

### 3. Set Up the Backend

```bash
cd backend

# Create virtual environment
python -m venv myvenv
myvenv\Scripts\activate        # Windows
source myvenv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy model files from notebooks
mkdir -p models data/processed
copy ..\notebooks\models\failsafe_model.pkl    models\         # Windows
copy ..\notebooks\models\shap_explainer.pkl   models\
copy ..\notebooks\models\threshold_config.json models\
copy ..\notebooks\data\processed\features.json data\processed\

# Copy intervention engine
copy ..\notebooks\backend\intervention_engine_groq.py .
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=failsafe_db
DB_USER=postgres
DB_PASSWORD=your_password

JWT_SECRET=run_python_-c_"import_secrets;_print(secrets.token_hex(32))"
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

GROQ_API_KEY=your_groq_key_from_console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

APP_ENV=development
ALLOWED_ORIGINS=http://localhost:3000
```

### 5. Create the Database

```bash
# Create database in PostgreSQL
psql -U postgres -c "CREATE DATABASE failsafe_db;"

# Create tables and default user
python setup_db.py
```

Default credentials created:
```
Email    : faculty@failsafe.edu
Password : password123
```

### 6. Start the Backend

```bash
uvicorn main:app --reload
```

API runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 7. Set Up the Frontend

```bash
cd ../frontend
npm install
```

Create `.env`:
```env
# Leave empty — Vite proxy handles it in development
# VITE_API_URL=
```

### 8. Start the Frontend

```bash
npm run dev
```

App runs at: `http://localhost:3000`

---

## Deployment

### Services Used
| Service | Purpose | Cost |
|---|---|---|
| [Supabase](https://supabase.com) | PostgreSQL database | Free |
| [Render](https://render.com) | FastAPI backend hosting | Free tier |
| [Vercel](https://vercel.com) | React frontend hosting | Free |
| [Groq](https://console.groq.com) | LLM inference | Free tier |

### Deployment Steps

#### 1. Upload Model Files to Google Drive
Upload these 4 files, make each **publicly accessible**:
- `failsafe_model.pkl`
- `shap_explainer.pkl`
- `threshold_config.json`
- `features.json`

#### 2. Push to GitHub
```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

#### 3. Set Up Supabase
1. Create project at supabase.com
2. Go to Settings → Database → Connection string → URI
3. Copy the connection string

#### 4. Deploy Backend to Render
1. New Web Service → connect GitHub repo
2. Root Directory: `backend`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:

```
APP_ENV                = production
DATABASE_URL_OVERRIDE  = your_supabase_connection_string
JWT_SECRET             = your_generated_secret
JWT_ALGORITHM          = HS256
JWT_EXPIRE_MINUTES     = 480
GROQ_API_KEY           = your_groq_key
GROQ_MODEL             = llama-3.3-70b-versatile
ALLOWED_ORIGINS        = https://your-app.vercel.app
```

6. Deploy — model files download automatically at startup
7. Open Render Shell → `python setup_db.py`

#### 5. Deploy Frontend to Vercel
1. New Project → import GitHub repo
2. Root Directory: `frontend`
3. Add environment variable:
```
VITE_API_URL = https://your-render-app.onrender.com
```
4. Deploy

#### 6. Update CORS on Render
Once you have your Vercel URL, update:
```
ALLOWED_ORIGINS = https://your-app.vercel.app
```

---

## API Reference

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "faculty@failsafe.edu",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_name": "Faculty Demo",
  "user_email": "faculty@failsafe.edu"
}
```

### Single Student Assessment
```http
POST /predict
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "student_id": "STU-001",
  "G1": 9, "G2": 8, "absences": 12, "failures": 1,
  "studytime": 1, "traveltime": 2, "famrel": 3,
  "freetime": 4, "goout": 4, "Dalc": 2, "Walc": 3,
  "health": 3, "Medu": 2, "Fedu": 1,
  "schoolsup": 0, "famsup": 1, "paid": 0,
  "activities": 0, "higher": 1, "internet": 1, "romantic": 0
}
```

Response:
```json
{
  "student_id": "STU-001",
  "risk_score": 78.4,
  "risk_band": "HIGH",
  "prediction": "AT-RISK",
  "top_factors": [["G2", 3.271], ["absences", 1.843], ...],
  "rule_interventions": [...],
  "intervention_plan": "This student is showing...",
  "plan_source": "llm"
}
```

### Batch Upload
```http
POST /predict-batch
Authorization: Bearer eyJ...
Content-Type: multipart/form-data

file: students.csv
```

Download the CSV template first:
```http
GET /template
Authorization: Bearer eyJ...
```

---

## Dataset

**UCI Student Performance Dataset**
- Source: Paulo Cortez, University of Minho, Portugal
- Available on [Kaggle](https://www.kaggle.com/datasets/uciml/student-alcohol-consumption)
- Two datasets: Math (`student-mat.csv`) and Portuguese (`student-por.csv`)
- FAILSAFE uses the Math dataset (395 students)
- Target: Final grade G3 — students with G3 < 10 are labelled as at-risk

---

## Live Demo
> Start the backend first, before going to the vercel app
- Backend Render deployment: https://failsafe-nki6.onrender.com/
- Frontend Vercel deployment: https://fail-safe-ag.vercel.app

## Environment Variables Reference

### Backend (`.env`)

| Variable | Description | Example |
|---|---|---|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `failsafe_db` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `your_password` |
| `DATABASE_URL_OVERRIDE` | Full DB URL (overrides above) | `postgresql://...` |
| `JWT_SECRET` | Secret for signing JWT tokens | 64-char hex string |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token expiry in minutes | `480` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `GROQ_MODEL` | Groq model to use | `llama-3.3-70b-versatile` |
| `APP_ENV` | Environment | `development` or `production` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

### Frontend (`.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | Backend URL (production only) | `https://app.onrender.com` |

---

## License

This project was built as part of a Coding Club, IIT Guwahati Even Semester project on AI-assisted academic intervention systems.

---

## Acknowledgements

- [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/Student+Performance) — dataset
- [Groq](https://groq.com) — LLM inference
- [SHAP](https://shap.readthedocs.io) — model explainability
- [XGBoost](https://xgboost.readthedocs.io) — gradient boosting framework
