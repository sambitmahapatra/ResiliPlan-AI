# ResiliPlan AI — Backend API & Frontend Integration Contract

Prescriptive supply-chain optimization backend. Reference data + an on-demand HiGHS
solve. **All monetary figures are ASSUMED** (the source workbook has no cost data) and
disruptions are **synthetic** stress tests. Service is **lost-sales** (no backorder).

## Run locally

```powershell
cd D:\SCA\Project
C:\Users\sambi\miniconda3\envs\myenv\python.exe -m uvicorn app.api.index:app --reload --port 8000
```
- Interactive docs (OpenAPI/Swagger): http://localhost:8000/docs
- No database needed to run; set Supabase env vars (below) to enable run history.

## Integration model (recommended)

| Data | Source for the frontend |
|---|---|
| Network, criticality, scenarios, cost assumptions, precomputed scenario results | **Supabase tables** (read directly via `supabase-js`, anon key) **or** the API GET endpoints below — identical shapes |
| Running an optimization (baseline / scenario / custom) | **`POST /api/solve`** (this API) |
| Run history | **Supabase `optimization_runs`** (written by the API) or `GET /api/runs` |
| CSV download | API `GET/POST /api/export/*.csv` |

So the frontend can be built almost entirely against Supabase + a single `POST /api/solve`.

## Endpoints

All under `/api`. CORS is open by default (set `ALLOWED_ORIGINS` to restrict).

### GET `/api/health`
`{ status, service, version, supabase_configured }`

### GET `/api/network`
```jsonc
{ "nodes": [ { "node_n": "zp7", "family": "oem", "role": "assembly", "echelon_level": 1 } ],
  "arcs":  [ { "starting_node_i": "...", "ending_node_j": "...", "group_g": "battery",
              "lead_time": 20, "exceeds_horizon": true } ] }
```

### GET `/api/criticality`
`{ "components": [ { component_p, group_g, origin_node, n_cars_using, pct_configs_dependent,
   gross_demand_total, cum_lead_time, risk_score, is_direct_car_component } ] }` (49 rows)

### GET `/api/scenarios`
`{ "scenarios": [ { id, name, nature, managerial_question, modifications, is_synthetic } ] }` (6)

### GET `/api/scenarios/results`
Precomputed baseline + 6-scenario comparison (no solve): `{ results: [ { scenario_id, status,
objective_mu, vs_baseline_mu, service_overall_pct, battery_service_pct, total_shortage,
expedite_units, cost_breakdown, service_by_group, validated } ], baseline_objective }`

### GET `/api/cost-assumptions`
`{ status: "ASSUMED ...", parameters: [ { parameter, scope, value, unit, basis,
sensitivity_low, sensitivity_high, status } ] }` (13)

### GET `/api/monte-carlo`
`{ n, seed, service_mean, service_min, service_max }`

### POST `/api/solve`  ← the one compute call
Request:
```jsonc
{
  "scenario_id": "baseline",        // saved id; ignored if "modifications" is set
  "modifications": {                // OPTIONAL custom scenario
    "arc_capacity_multiplier": [ { "arc": ["engine-supplier_inv","zp7"], "factor": 0.6, "periods": "all" } ],
    "arc_lead_time_delta":     [ { "arc": ["gear-supplier_inv","zp7"], "delta_periods": 3, "periods": "all" } ],
    "car_demand_multiplier":   [ { "periods": [66,67,68], "factor": 1.3 } ],
    "enable_expedite": true
  },
  "cost_overrides": { "shortage_penalty_car": 8000 },   // OPTIONAL
  "detail": false,                  // true -> include full plan (flows/shortages)
  "persist": true,                  // store the run in Supabase if configured
  "created_by": "anon"
}
```
Response:
```jsonc
{
  "scenario_id": "baseline", "is_custom": false, "scenario_name": "Baseline",
  "status": "optimal", "status_message": "HiGHS: Optimal",
  "objective_mu": 18395031.0,
  "cost_breakdown": { "production": .., "transport": .., "expedite": .., "holding": .., "shortage": .. },
  "service": { "overall_pct": 98.22, "by_group": { "battery": 48.32, "engine": 100, ... },
               "total_demand": 87003, "total_shortage": 1552 },
  "expedite_units": 0,
  "validation": { "all_ok": true, "max_balance_residual": 0.0, "max_capacity_violation": 0.0 },
  "model_size": { "variables": 5096, "equality_constraints": 2548, "capacity_constraints": 140 },
  "vs_baseline": { "delta_cost_mu": .., "delta_service_pp": .. } | null,
  "recommendations": [ "..." ],
  "solve_seconds": 0.45,
  "persisted": { "ok": true, "id": "<uuid>" } | null
}
```
Errors: `422` with `{detail}` for invalid modifications (e.g. unknown arc); `500` on solve failure.

### GET `/api/runs?limit=50`
`{ runs: [...] }` from Supabase, or `{ runs: [], note }` if Supabase is not configured.

### Exports
- `GET /api/export/scenario-comparison.csv` → CSV of the 6-scenario comparison.
- `POST /api/export/solve.csv` (same body as `/api/solve`) → CSV of one solve's KPIs.

## Environment (optional Supabase)
See `.env.example`. Set `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` (server-side) to enable
persistence. The frontend uses the **anon** key with the provided RLS policies (read-all +
public run inserts).

## Notes for the report / UI
- Surface the `status`, `validation.all_ok`, and `recommendations` so the manager sees solver
  honesty and guidance. Never present a non-optimal result as optimal.
- Label every MU value and disruption as ASSUMED/synthetic in the UI (an "About / Assumptions"
  panel maps to `/api/cost-assumptions`).
