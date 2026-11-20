# Earth Online Starter

An executable starter for an AI-driven city, economy and society simulation.
It follows the first part of the Earth Online technical plan: one fictional
city, a reproducible daily simulation engine, simple markets, public policy,
a web dashboard and a replaceable institutional decision-agent interface.

## What works now

- Deterministic city generation from a random seed (100–5,000 households).
- 10 synthetic districts, 20 firms, employment, wages, income tax, unemployment
  benefits, goods purchases, rent and satisfaction with neighborhood feedback.
- Every internal transfer is represented by paired ledger entries; the total
  money supply is checked on every simulation day.
- FastAPI endpoints to inspect, advance, reset and modify the simulation.
- React dashboard with district selection, time series, tax slider and reset.
- An offline **heuristic mayor** as an AI integration placeholder. It is *not*
  an LLM; the adapter can be replaced later without giving the model direct
  write access to the simulation.
- Eight simulation and HTTP smoke tests using `unittest`.

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer and npm

## 1. Start the backend

In terminal one, from the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation: http://127.0.0.1:8000/docs

## 2. Start the frontend

In terminal two, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

Vite proxies `/api` requests to the Python backend, so no CORS configuration
is required in this local development setup.

## 3. Run the tests

From the repository root:

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
```

## Example API calls

```bash
curl http://127.0.0.1:8000/api/world
curl -X POST http://127.0.0.1:8000/api/step \
  -H 'Content-Type: application/json' -d '{"days":30}'
curl -X POST http://127.0.0.1:8000/api/policy \
  -H 'Content-Type: application/json' -d '{"tax_rate":0.18}'
curl -X POST http://127.0.0.1:8000/api/reset \
  -H 'Content-Type: application/json' -d '{"seed":42,"population":1000}'
curl -X POST http://127.0.0.1:8000/api/agent/mayor/decide \
  -H 'Content-Type: application/json' -d '{}'
```

## Repository layout

```text
earth-online-starter/
├── backend/
│   ├── app/
│   │   ├── simulation.py    Deterministic simulation, ledger and metrics
│   │   ├── agents.py        Bounded decision-agent stub
│   │   └── main.py          FastAPI endpoints and request validation
│   ├── tests/
│   │   └── test_simulation.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.tsx          Dashboard, visualization and controls
    │   ├── main.tsx
    │   └── styles.css
    └── package.json
```

## Starter limitations

This is a conceptual sandbox, **not a calibrated real-world economic model**.
The rules and currency are synthetic. One API process holds one shared city
in memory: restarting the backend loses the current simulation. Run a single
worker; do not deploy this version as a multi-user public service.

The next milestones are PostgreSQL persistence, independent scenario/run IDs,
checkpoints and event history, parameter calibration, labor and housing market
matching, and a provider-neutral LLM decision adapter that returns strictly
validated structured proposals. The UI currently supports a tax intervention;
other policies and scenario comparison come later.

