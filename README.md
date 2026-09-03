# DBOptima

[Türkçe README](README_TR.md)

DBOptima is a PostgreSQL query optimization project that analyzes query execution plans, generates index candidates, benchmarks them, and records the measured results.

The project combines deterministic PostgreSQL plan analysis with a machine-learning model that ranks candidates before benchmark execution. Final recommendation status is based on the measured benchmark result, not the model prediction.

---

## What It Does

For a submitted SQL query, DBOptima can:

- run `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`
- inspect the execution plan
- detect sequential scans
- generate index candidates
- rank candidates with an ML model
- benchmark query latency before and after a temporary index
- calculate measured improvement
- classify the result as `RECOMMENDED`, `REVIEW`, or `REJECTED`
- persist query, plan, benchmark, recommendation, and training data

Main flow:

```text
SQL Query
   |
   v
EXPLAIN ANALYZE
   |
   v
Plan Analysis
   |
   v
Index Candidate Generation
   |
   v
ML Candidate Ranking
   |
   v
Before / After Benchmark
   |
   v
Measured Improvement
   |
   v
Recommendation Decision
```

The ML model is used to prioritize candidates. PostgreSQL benchmark results remain the final decision source.

---

## Recommendation Policy

Current decision thresholds:

| Measured improvement | Status |
| --- | --- |
| `>= 20%` | `RECOMMENDED` |
| `>= 5%` and `< 20%` | `REVIEW` |
| `< 5%` | `REJECTED` |

---

## Example Query

Example workload:

```sql
SELECT *
FROM orders
WHERE customer_id = 42
  AND status = 'PAID'
ORDER BY created_at DESC;
```

A candidate can be generated around:

```text
customer_id
status
created_at DESC
```

In the current local test database, this query produced very large measured gains after adding the recommended composite index. Exact results vary depending on data size, cache state, hardware, PostgreSQL statistics, and execution plan.

---

## Machine Learning

DBOptima currently uses a V2 model for candidate ranking.

```text
Model version:   v2-final
Feature schema:  v2
Feature count:   26
Training samples: 340
Query groups:     51
```

### Evaluation

Grouped validation results from the current experimental dataset:

| Metric | Result |
| --- | ---: |
| MAE | `10.50 ± 2.88` |
| RMSE | `16.74 ± 2.81` |
| R² | `0.816 ± 0.095` |
| Status accuracy | `78.91% ± 5.31%` |

Cold-start evaluation on unseen query groups:

| Metric | Result |
| --- | ---: |
| MAE | `16.13` |
| RMSE | `22.51` |
| R² | `0.7425` |
| Status accuracy | `70.59%` |

These metrics describe the current project dataset only. They are not intended as a claim of general performance across arbitrary PostgreSQL schemas or workloads.

---

## Architecture

```text
+----------------------+
|      Next.js UI      |
|----------------------|
| Overview             |
| Query Analyzer       |
| Recommendations      |
| Benchmarks           |
| Workload             |
| Models               |
| Databases            |
| Settings             |
+----------+-----------+
           |
           v
+----------+-----------+
|      FastAPI API     |
+----------+-----------+
           |
     +-----+-----+
     |           |
     v           v
Plan Analyzer   ML Ranker
     |           |
     +-----+-----+
           |
           v
    Index Advisor
           |
           v
   Benchmark Engine
      /         \
     v           v
Target DB    Metadata DB
PostgreSQL   PostgreSQL
```

---

## Technology Stack

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- psycopg
- Pydantic
- PostgreSQL
- scikit-learn
- joblib
- Alembic

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Lucide React
- Recharts

### Infrastructure

- Docker
- Docker Compose
- PostgreSQL 17

---

## Project Structure

```text
dboptima/
├── backend/
│   ├── app/
│   │   ├── analyzers/
│   │   ├── api/
│   │   ├── benchmark/
│   │   ├── collectors/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── recommenders/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── analyzer/
│   │       ├── recommendations/
│   │       ├── benchmarks/
│   │       ├── workload/
│   │       ├── models/
│   │       ├── databases/
│   │       ├── settings/
│   │       ├── components/
│   │       ├── lib/
│   │       └── page.tsx
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## Main Pages

### Overview

Shows aggregate project metrics such as:

- analyzed queries
- query calls
- recommendation counts
- latency samples
- measured gain
- latest recommendations

### Query Analyzer

Main optimization screen.

Shows:

- execution time
- planning time
- detected plan issues
- candidate indexes
- predicted gain
- measured gain
- recommendation status

### Recommendations

Displays persisted recommendation history with filtering and detail views.

### Benchmarks

Displays measured before/after benchmark results.

### Workload

Displays query-level statistics such as:

- total calls
- average latency
- p95 latency
- max latency
- recommendation count
- best measured gain

### Models

Displays production model metadata and feature information.

### Databases

Displays configured database connections and connection test results.

### Settings

Displays current recommendation and benchmark policies.

---

## Local Development

### Requirements

Install:

- Python 3.12+
- Node.js
- npm
- Docker Desktop
- Git

### 1. Start PostgreSQL

From the project root:

```bash
docker compose up -d
```

Check:

```bash
docker ps
```

### 2. Backend

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### 3. Frontend

Create:

```text
frontend/.env.local
```

Example:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## Main API Routes

```text
GET  /health

GET  /api/databases
POST /api/databases
POST /api/databases/{database_id}/test

POST /api/databases/{database_id}/analyze-query
POST /api/databases/{database_id}/optimize-query
POST /api/databases/{database_id}/benchmark-index

GET  /api/overview/{database_id}
GET  /api/recommendations/{database_id}
GET  /api/benchmarks/{database_id}
GET  /api/workload/{database_id}

GET  /api/models/production
GET  /api/settings
```

---

## Example Optimization Request

```http
POST /api/databases/2/optimize-query
Content-Type: application/json
```

```json
{
  "query": "SELECT * FROM orders WHERE customer_id = 42 AND status = 'PAID' ORDER BY created_at DESC"
}
```

The response includes:

```text
baseline
issues
candidate_count
evaluation_context
candidates
persistence
```

Candidate results include fields such as:

```text
ml_rank
actual_rank
ml_prediction
benchmark
decision
prediction_error_percent
```

This makes it possible to compare the ML ranking with the actual PostgreSQL benchmark result.

---

## Data Stored by the Project

DBOptima persists information such as:

- database connections
- normalized queries
- query execution samples
- query plans
- recommendations
- benchmark results
- ML training samples

Query history includes statistics such as:

- total calls
- average latency
- minimum latency
- maximum latency
- p95 latency
- first seen
- last seen

---

## Current Limitations

This project is a development / portfolio prototype.

Current limitations include:

- the ML dataset is based on a limited development workload
- behavior on arbitrary schemas has not been established
- query fingerprinting is lightweight
- optimization jobs currently run synchronously
- authentication is not implemented
- multi-user support is not implemented
- workload-wide index portfolio optimization is not implemented
- production observability is not implemented

For benchmarking, use a local, test, staging, cloned, or otherwise controlled PostgreSQL database.

---

## Future Work

Possible next steps:

- asynchronous benchmark jobs
- stronger SQL parsing
- redundant index detection
- unused index analysis
- table statistics recommendations
- query rewrite candidates
- richer workload statistics
- model version tracking
- model retraining workflow
- drift detection
- benchmark budget management
- workload-wide index selection
- CP-SAT based index portfolio optimization
- authentication and authorization
- automated tests and Testcontainers
- production observability

---

## Development Status

Implemented:

- PostgreSQL connection management
- execution plan collection
- sequential scan analysis
- index candidate generation
- real before/after benchmark flow
- recommendation classification
- query fingerprinting
- query history
- latency sample persistence
- recommendation history
- ML training sample persistence
- V2 feature schema
- V2 model evaluation
- production V2 model artifact
- ML candidate ranking
- benchmark vs prediction comparison
- Overview UI
- Query Analyzer UI
- Recommendations UI
- Benchmarks UI
- Workload UI
- Models UI
- Databases UI
- Settings UI

---

## Notes

Do not commit real credentials or local environment files.

Recommended `.gitignore` entries:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/

.env
.env.*
!.env.example

frontend/node_modules/
frontend/.next/
frontend/out/
frontend/.env.local

.vscode/
.idea/

.DS_Store
Thumbs.db
```

If model artifacts are included in the repository, keep only the artifacts required to run the current application and avoid unnecessary experimental outputs.

---

## Author

Developed as a full-stack PostgreSQL optimization project combining backend development, query-plan analysis, benchmarking, machine learning, persistence, and frontend development.
