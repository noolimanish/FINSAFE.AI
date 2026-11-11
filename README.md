# FinSafe.AI — Personal Financial Security Health Check

FinSafe is an India-focused personal financial security audit engine and interactive dashboard. It combines a deterministic calculation core built with FastAPI and SQLite with an optional language model layer that converts analytical findings into accessible guidance and a prioritized 30-day action checklist. The user interface is built on Next.js 14 with TypeScript, Tailwind CSS, Framer Motion, and Recharts.

---

## Overview & Background

FinSafe addresses financial vulnerabilities common in the Indian context:

- **Reliance on Employer Medical Plans**: Many working professionals depend entirely on corporate group health cover. If employment ends or changes, this coverage is lost immediately.
- **Capital Locked in Traditional Plans**: A significant portion of savings is often allocated to low-yield endowment or money-back policies rather than balanced, inflation-beating investments.
- **Gaps in Term & Disability Coverage**: Individuals with dependents often lack adequate pure term insurance and standalone personal accident coverage.
- **Short Emergency Runways**: High monthly debt obligations can leave households with insufficient liquid reserves for unexpected job or medical shocks.
- **Retirement Planning Shortfalls**: Underestimating medical inflation and lifestyle expenses often leads to inadequate corpus targets.

FinSafe calculates all financial ratios and rule evaluations in pure Python using strict deterministic logic. The language model is used strictly for translation, generating user-friendly explanations from pre-computed results.

---

## Deterministic Rules (R1 to R5)

The engine evaluates five core financial guardrails:

1. **R1: Emergency Fund Runway**
   - Evaluates liquid assets against monthly essential expenditures and EMIs.
   - Benchmark: 6 months of mandatory burn.
   - Status: Critical (< 3 months), Warning (3 to < 6 months), Info (>= 6 months).

2. **R2: Medical Insurance Continuity**
   - Checks standalone personal coverage and total coverage relative to annual income.
   - Benchmark: Total cover >= 3x annual income, with at least ₹10 Lakh in portable personal cover.
   - Status: Critical (zero personal cover), Warning (under 3x income target), Info (adequate).

3. **R3: Endowment & Low-Yield Concentration**
   - Evaluates the proportion of total investments locked in traditional endowment or ULIP products.
   - Benchmark: <= 40% of investment portfolio.
   - Status: Warning (> 40% locked), Info (<= 40%).

4. **R4: Personal Accident & Term Life Protection**
   - Checks pure term life coverage for individuals with dependents and standalone personal accident coverage.
   - Benchmark: 10x annual income for term life (when dependents > 0) and 3x annual income for personal accident.
   - Status: Critical (dependents with zero term cover), Warning (shortfall in accident or term), Info (adequate).

5. **R5: Retirement Corpus Trajectory**
   - Projects existing retirement assets and ongoing contributions at an assumed 10% annual return against an inflation-adjusted (6% p.a.) target of 25x annual expenses.
   - Status: Critical (< 60% funded), Warning (60% to < 100%), Info (>= 100%).

---

## Financial Security Score

The overall score (0 to 100) is calculated deterministically from rule severity:
- Base score: 100
- Deduction: 22 points per Critical finding, 12 points per Warning finding
- Minimum floor: 8 points

Score tiers:
- **Resilient**: 75 - 100
- **Vulnerable**: 50 - 74
- **High Risk**: Below 50

---

## Pre-Configured Personas

FinSafe includes built-in demo personas to explore the system:

- **Aarav Sharma (Bengaluru SDE-2)**: High earner with 100% employer health dependence, zero term life cover, and high monthly debt obligations.
- **Priya Nair (Pune IT Lead)**: Steady saver with a high concentration of portfolio value locked in legacy endowment plans.
- **Rohan Verma (Hyderabad Staff Engineer)**: Balanced profile with personal health insurance, top-up cover, pure term life, and diversified equity/EPF investments.

---

## Architecture & Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLite, SQLAlchemy 2.0, Pydantic v2, Pytest
- **Frontend**: Next.js 14 App Router, React 18, TypeScript, Tailwind CSS, Framer Motion, Recharts, Lucide React
- **Deployment**: Docker & Docker Compose

---

## Project Structure

```
finsafe/
├── docker-compose.yml           # Container orchestration
├── README.md                    # System documentation
├── .gitignore                   # Version control ignore list
├── backend/
│   ├── Dockerfile               # FastAPI backend container
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Backend environment template
│   ├── app/
│   │   ├── main.py              # Application entrypoint & REST routes
│   │   ├── models.py            # SQLite data models & repository
│   │   ├── rules_engine.py      # Deterministic financial rules R1-R5
│   │   ├── llm_service.py       # Narrative generation & deterministic fallback
│   │   └── schemas.py           # Pydantic schemas
│   └── tests/
│       └── test_finsafe.py      # Test suite
└── frontend/
    ├── Dockerfile               # Next.js frontend container
    ├── package.json             # Frontend dependencies
    ├── tsconfig.json            # TypeScript configuration
    ├── tailwind.config.ts       # Tailwind CSS configuration
    ├── .env.example             # Frontend environment template
    ├── app/                     # Next.js App Router pages and layout
    ├── components/              # UI components (ScoreGauge, Charts, Checklist)
    └── lib/                     # API client and TypeScript definitions
```

---

## Getting Started

### Using Docker Compose

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- API documentation (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Local Development Setup

#### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
pytest -v
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## Environment Variables

### Backend (`backend/.env`)

- `DATABASE_URL`: Database path (default: `sqlite:///./finsafe.db`)
- `LLM_API_KEY`: Optional API key for OpenAI-compatible providers. If left blank, the deterministic fallback engine generates all explanations.
- `LLM_BASE_URL`: API provider endpoint (default: `https://api.openai.com/v1`)
- `LLM_MODEL`: Model name (default: `gpt-4o-mini`)
- `CORS_ORIGINS`: Allowed origins (default: `http://localhost:3000,http://127.0.0.1:3000`)

### Frontend (`frontend/.env.local`)

- `NEXT_PUBLIC_API_URL`: Backend endpoint (default: `http://localhost:8000`)

---

## API Summary

- `GET /health` - System health and LLM provider configuration status.
- `POST /api/v1/profile` - Upsert personal income, age, retirement age, and dependent details.
- `GET /api/v1/profile` - Retrieve current profile.
- `POST /api/v1/insurance` - Replace user insurance policies.
- `POST /api/v1/investments` - Replace user investment assets.
- `POST /api/v1/expenses` - Replace user monthly expense breakdown.
- `POST /api/v1/audit/run` - Execute full audit check and generate action plan.
- `GET /api/v1/audit/latest` - Retrieve the most recent audit report.
- `PATCH /api/v1/audit/action-plan/{item_id}` - Toggle completion state of a 30-day action item.
- `POST /api/v1/demo/seed` - Initialize a pre-defined persona (`anxious_tech_worker`, `lic_heavy_saver`, `well_prepared`).

---

## Running Tests

Run the backend test suite:

```bash
cd backend
pytest -v
```
