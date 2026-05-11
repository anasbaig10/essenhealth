# Clinical Rules Engine

A population health rules engine that evaluates patients against clinical programs and generates work for schedulers and clinical teams.

## What This Is

A clinical rules engine for population health. It evaluates every patient against two programs (Primary Care Wellness and Diabetes Management) on each startup. It generates scheduling and referral tasks routed to either schedulers or clinical staff based on role.

## Prerequisites

- Python 3.11+
- Node 22+
- pip

## Setup

### Backend

```
cd project/backend
pip install -r ../requirements.txt
python main.py
```

Expected output:

```
patients loaded: 300
diagnoses loaded: 312
labs loaded: 238
encounters loaded: 1159 (past: 1030, future: 129)
Engine complete: 403 enrollments, 278 tasks (170 scheduling, 108 referral)
Uvicorn running on http://0.0.0.0:8000
```

### Frontend (open a new terminal)

```
cd project/frontend
npm install
npm run dev
```

## Open The App

```
Frontend:   http://localhost:5173
API:        http://localhost:8000
API Docs:   http://localhost:8000/docs
```

## How To Use

Role toggle (top left):
- **Scheduler** — scheduling tasks only (patients who need appointments booked directly)
- **Clinical Team** — all tasks including referrals (patients who need clinician review first)

Filters:
- Specialty: PCP, Endocrinology, Cardiology, Podiatry, Ophthalmology, Nephrology
- Task Type: scheduling or referral
- All filters combine with role

## API

```
GET /patients
  ?role=scheduler or clinical
  ?specialty=Endocrinology (or any specialty)
  ?task_type=scheduling or referral

GET /patients/{patient_id}
  Full detail — all programs, tiers, active tasks
```

Interactive docs: http://localhost:8000/docs

## Clinical Programs

**Primary Care Wellness**
- All patients 18+
- High Priority (age 65+ or chronic condition): PCP every 180 days
- Standard: PCP every 365 days

**Diabetes Management**
- Patients with E10/E11 diagnosis only
- Tier based on most recent HbA1c within 6 months:
  - High Risk (>=9.0):    5 specialists
  - Moderate (7.0–8.9):   3 specialists
  - Low Risk (<7.0):      2 specialists
  - Unmonitored:          Endocrinology only

## Project Structure

```
project/
  backend/
    config.py          reference date constants
    database.py        SQLite schema
    data_loader.py     CSV ingestion
    rules_engine.py    base class + PROGRAM_REGISTRY
    programs/
      pcw.py           Primary Care Wellness
      diabetes.py      Diabetes Management
    task_generator.py  scheduling/referral logic
    engine_runner.py   orchestration
    router.py          API endpoints
    models.py          Pydantic schemas
    main.py            startup
  frontend/
    src/
      api/patients.ts  API calls
      components/      UI components
      App.tsx          state + layout
  data/                input CSVs
  requirements.txt     Python dependencies
  architecture.md      system design document
  README.md            this file
```

## Architecture

See `architecture.md` for full system design:
- Database schema and decisions
- Extensibility patterns
- Scalability approach
- EHR integration design
- Trade-offs

## Assumptions

- Reference date fixed to 2026-05-08 to match the provided static dataset
- HbA1c cutoff: 2025-11-08 (6 months prior)
- Role-based access via query param — no auth (as per assessment scope)
- SQLite used for zero-setup local running
