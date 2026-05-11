# Architecture

## Overview

This system is a clinical rules engine for a population health platform. It ingests patient demographics, diagnoses, labs, and encounter history, applies program-specific eligibility and risk stratification rules, and generates actionable tasks for two types of clinical staff: schedulers (who book appointments directly) and clinical team members (who review and approve referrals). The current implementation supports two programs — Primary Care Wellness and Diabetes Management — and is designed so that adding new programs or care protocols requires minimal structural changes to existing code.

## Data Flow

```
CSVs → SQLite input tables → Rules Engine → SQLite output tables → API → Frontend
```

Data flows in one direction only. The rules engine reads from input tables and writes to output tables. The API reads tasks and enrollments as the source of truth for workload, and joins patients for display demographics only. It does not read diagnoses, labs, or encounters and never re-runs clinical logic. This matters because the API layer has zero coupling to the engine logic — you can re-run the engine, change program rules, or add a new program without touching a single line in `router.py`. The frontend is a pure read consumer.

## Database Schema

### Input Tables

```
patients
  patient_id        TEXT  PRIMARY KEY
  first_name        TEXT
  last_name         TEXT
  date_of_birth     DATE
  gender            TEXT
  phone             TEXT
  language          TEXT
  pcp_provider_name TEXT   -- nullable

diagnoses
  id              INTEGER  PRIMARY KEY AUTOINCREMENT
  patient_id      TEXT     REFERENCES patients
  icd_code        TEXT
  description     TEXT
  diagnosed_date  DATE

labs
  id            INTEGER  PRIMARY KEY AUTOINCREMENT
  patient_id    TEXT     REFERENCES patients
  test_name     TEXT
  result_value  REAL
  result_date   DATE

encounters
  id              INTEGER  PRIMARY KEY AUTOINCREMENT
  patient_id      TEXT     REFERENCES patients
  specialty       TEXT
  encounter_date  DATE
  provider_name   TEXT
  is_future       BOOLEAN  DEFAULT FALSE
```

**Why `is_future` is pre-computed:** Tags encounters deterministically at load time against REFERENCE_DATE — simpler queries, one consistent definition of as-of date across all engine evaluations.

**Why `pcp_provider_name` is nullable:** The source data has 24 patients with no assigned PCP. The field is informational — it has no effect on task generation logic. Whether a patient has a PCP name or not, `generate_task()` in `task_generator.py` still evaluates encounter history to decide whether to emit a scheduling task or no task.

### Output Tables

```
enrollments
  id           INTEGER    PRIMARY KEY AUTOINCREMENT
  patient_id   TEXT       REFERENCES patients
  program      TEXT
  tier         TEXT
  evaluated_at TIMESTAMP

tasks
  id           INTEGER    PRIMARY KEY AUTOINCREMENT
  patient_id   TEXT       REFERENCES patients
  program      TEXT
  specialty    TEXT
  task_type    TEXT       -- "scheduling" or "referral"
  need_type    TEXT       -- "specialist_visit" (extensibility hook)
  cadence_days INTEGER
  last_visit   DATE       -- nullable (null on referral tasks)
  days_overdue INTEGER    -- nullable (null on referral tasks)
  evaluated_at TIMESTAMP
```

**Why enrollments and tasks are separate tables:** Enrollment tracks which program a patient qualifies for and their risk tier. Tasks track what actions need to happen. These are distinct facts — a patient can be enrolled in Diabetes Management as High Risk with zero tasks if all specialists are already scheduled. Merging them would repeat program/tier on every task row and make tier-level queries require deduplication.

**Why `need_type` exists on tasks:** It is the dispatch key into `TASK_HANDLERS` in `task_generator.py`. Currently all needs are `"specialist_visit"`, but adding a `"lab_order"` need type requires only a new handler function and a new dict key — no engine change; schema untouched if new need types fit existing columns. Need types with richer payloads would require adding columns but no structural reorganization. The column makes each task record self-describing.

**Why `evaluated_at` exists on both tables:** Every row is stamped with the datetime the engine ran. In a production system running nightly batch jobs, this lets you audit when a patient's tier last changed, compare task counts across runs, and identify patients whose status is stale.

## Component Overview

| File | What it does | Why it's separate |
|---|---|---|
| `config.py` | Defines `REFERENCE_DATE` and `HBAIC_CUTOFF` | Single source of truth for all date logic across the entire backend |
| `database.py` | Creates SQLite connection and all 6 table schemas | Centralizes schema — one place to add indexes, migrate columns, or change the DB path |
| `data_loader.py` | Reads 4 CSVs, computes `is_future`, inserts into input tables | Load phase is distinct from compute phase — can re-run independently if source data changes |
| `models.py` | Pydantic response shapes for the API | Defines the API contract in one file; router imports from here |
| `rules_engine.py` | `ClinicalNeed` dataclass, `ClinicalProgram` base class, `PROGRAM_REGISTRY` list | Abstract interface all programs implement; registry pattern enables plugin-style program addition |
| `programs/pcw.py` | Primary Care Wellness — age eligibility, chronic ICD tier check, PCP cadence needs | One file per program; adding a program means adding a file, not editing existing ones |
| `programs/diabetes.py` | Diabetes Management — E10/E11 eligibility, HbA1c tier lookup, specialist needs by tier | Isolated from PCW; independently readable and testable |
| `programs/__init__.py` | Imports both program modules to trigger `PROGRAM_REGISTRY.append()` | Programs self-register at import time; this file ensures both load before the engine runs |
| `task_generator.py` | `generate_task()` implements the 4-step task decision; `TASK_HANDLERS` dict dispatches by need type | Task generation is a separate concern from program rules — the same function handles every program's needs |
| `engine_runner.py` | Iterates all patients × all programs, inserts enrollments and tasks | Orchestration only; knows nothing about specific program logic, calls interfaces defined in `rules_engine.py` |
| `main.py` | FastAPI app, CORS middleware, startup sequence, router include | Entry point; startup order is: create tables → load data → run engine |
| `router.py` | `GET /patients` and `GET /patients/{id}` with role/specialty/task_type filters | Read-only API layer; completely decoupled from engine and data loading |

## Extensibility

### Adding a New Program

1. Create `programs/hypertension.py`:

```python
from rules_engine import ClinicalNeed, ClinicalProgram, PROGRAM_REGISTRY

class HypertensionManagement(ClinicalProgram):
    program_name = "Hypertension Management"

    def check_eligibility(self, patient_id, conn):
        rows = conn.execute(
            "SELECT icd_code FROM diagnoses WHERE patient_id = ?", (patient_id,)
        ).fetchall()
        return any(r["icd_code"].startswith("I10") for r in rows)

    def get_tier(self, patient_id, conn):
        return "Standard"

    def get_needs(self, tier):
        return [ClinicalNeed("Cardiology", 180)]

PROGRAM_REGISTRY.append(HypertensionManagement())
```

2. Add one import to `programs/__init__.py`:

```python
from programs import pcw, diabetes, hypertension  # noqa
```

`engine_runner.py`, `task_generator.py`, `router.py`, and the database schema are all untouched.

### Adding a New Need Type

1. Write `handle_lab_order()` in `task_generator.py`:

```python
def handle_lab_order(patient_id, need, conn):
    # check recent labs, return task dict or None
    ...
```

2. Add one entry to `TASK_HANDLERS`:

```python
TASK_HANDLERS = {
    "specialist_visit": generate_task,
    "lab_order": handle_lab_order,
}
```

Any program can now return `ClinicalNeed("HbA1c", 90, need_type="lab_order")` and the engine dispatches correctly. Nothing else changes.

## Scalability

### 10x Programs

`PROGRAM_REGISTRY` is a plain list. `engine_runner.py` iterates it with `for program in PROGRAM_REGISTRY`. Adding 10 more programs adds 10 more iterations per patient — the loop structure does not change. Each program is stateless and independent, so they can also be evaluated in parallel with minor changes to the runner.

### 100x Patients

The engine writes all results to `tasks` and `enrollments`; the API reads only from those tables and is unaffected by patient volume. At scale: move the engine to a nightly batch job, push eligibility filters into SQL `WHERE` clauses rather than Python conditionals, add `CREATE INDEX ON tasks(patient_id, specialty, task_type)` and `CREATE INDEX ON encounters(patient_id, specialty, is_future)`, and add `LIMIT`/`OFFSET` pagination to `GET /patients`. Patient evaluations are independent, so the engine loop is embarrassingly parallelizable.

### New Need Type Without Restructuring

Handled entirely by the `TASK_HANDLERS` dict. One new function, one new dict key. Schema untouched if new need types fit existing columns. Need types with richer payloads would require adding columns but no structural reorganization.

## Edge Cases

| Edge Case | Count in Data | How Handled |
|---|---|---|
| Patient in both programs | 115 patients | `engine_runner` loops all programs per patient; tasks from both appear under separate `EnrollmentResponse` objects in the API response |
| Zero encounter history | 45 patients | `generate_task` step 3: no past rows → referral task for specialists, no task for PCP |
| Unmonitored diabetics (no recent HbA1c) | 33 patients | `diabetes.py` `get_tier`: query returns no rows → `"Unmonitored"` → single Endocrinology/90d need |
| Null PCP provider | 24 patients | Field is nullable in schema; never read by task logic |
| Under-18 patients | 12 patients | `pcw.py` `check_eligibility` returns `False`; excluded from PCW only, still eligible for Diabetes Management |
| ICD prefix matching | All diagnoses | `icd_code.startswith(prefix)` — E11.65 correctly matches E11; used in `_has_chronic()` and `diabetes.py` eligibility check |
| G47.3 specificity | Sleep apnea patients | `CHRONIC_PREFIXES` contains `"G47.3"` not `"G47"` — only sleep apnea subcodes match |
| Multiple HbA1c results | Handled generically | `diabetes.py` queries `ORDER BY result_date DESC LIMIT 1` — always takes the most recent result |
| Stale HbA1c (> 6 months old) | Some patients | `get_tier` filters `result_date >= HBAIC_CUTOFF` (`2025-11-08`); no qualifying row → `"Unmonitored"` |
| Future encounters blocking tasks | 129 encounters | `generate_task` step 1: `is_future = 1` → return `None`; no task generated if appointment already scheduled |
| Cadence boundary strictly greater than | All patients | `days_since > need.cadence_days` (not `>=`) — a patient seen exactly on cadence day has no overdue task |

Counts verified against the provided dataset as of 2026-05-08.

## Trade-offs

| Decision | Why | What I'd change with more time |
|---|---|---|
| SQLite over PostgreSQL | Zero infrastructure — one file, no server, runs anywhere | Swap to PostgreSQL for concurrent writes, proper FK enforcement, and connection pooling via SQLAlchemy |
| Hardcoded `REFERENCE_DATE` in `config.py` | Makes all output deterministic and verifiable against the spec regardless of when the code runs | Replace with `date.today()` in production; keep as an override for backfill and testing |
| Engine runs on every startup | Simple to demo; no scheduler dependency | Move to a nightly scheduled job; expose `POST /engine/run` for manual triggers |
| Role passed as query param, not auth | No auth infrastructure needed; both role views are demonstrable immediately | Replace with JWT claims; role should be server-verified, not caller-declared |
| No pagination on API | The worklist returns patients with at least one active task — roughly 155 in this dataset. At scale, LIMIT/OFFSET pagination and SQL WHERE filters would be added. | Add `?page=` and `?page_size=`; `total` is already in `PatientListResponse` |

## EHR Integration

We treat the EHR as a system we never fully trust — async writes, retries, eventual consistency.

**Inbound (EHR → engine):** The EHR sends a webhook on new encounters or scheduled appointments. The handler inserts the encounter into the `encounters` table and triggers a targeted re-evaluation for that patient only — not a full engine re-run. This keeps tasks current within seconds of an EHR event.

**Outbound (engine → EHR):** Task creation never calls the EHR synchronously. A background worker reads pending tasks from the `tasks` table and submits scheduling requests to the EHR API. On failure it retries with exponential backoff up to 5 attempts, then marks the task `failed` for human review. Synchronous EHR calls in the request path would make the entire system dependent on EHR uptime.

**Task states:** The `tasks` table gains a `status` column: `pending → synced | failed`. The API exposes `status` so the frontend can distinguish tasks that have been sent to the EHR from those still queued.

**Eventual consistency:** The tasks table and the EHR's appointment ledger can temporarily disagree. A nightly full engine re-run acts as the safety net: it recomputes all enrollments and tasks from current encounter data, reconciling any drift. Future encounters already in the EHR suppress tasks via the `is_future` flag.

## What I'd Build Next

- **Structured audit logging on engine runs:** record per-patient tier changes between runs — when a patient moves from Moderate Risk to High Risk, that transition should be timestamped and queryable, not just overwritten.
- **Batch SQL engine replacing the per-patient Python loop:** replace `engine_runner.py`'s row-by-row approach with a single SQL pass using window functions for HbA1c recency and bulk `INSERT INTO tasks SELECT ...` — eliminates N×M query overhead entirely.
- **Incremental re-evaluation on EHR webhook instead of full re-run:** on a new encounter event, re-evaluate only the affected patient; the nightly full run becomes a correctness check rather than the primary update mechanism.
- **LLM patient briefing endpoint:** `GET /patients/{id}/brief` — summarize the patient's risk tier, outstanding tasks, recent labs, and encounter history into a one-paragraph briefing a care coordinator reads before calling the patient.
