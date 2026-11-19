# ResiliPlan AI — Frontend (implementation summary & integration map)

React + TypeScript + Vite app in `app/frontend/`, built to match the **V4 mockup**
(`resiliplan_mockup/`) visually (its `styles.css` is reused verbatim) and wired to the
real FastAPI backend (`app/api/`). No fabricated KPIs — every number comes from a backend
response. Costs are ASSUMED (MU); disruptions are synthetic; service is lost-sales.

## Run locally
```
# 1) backend
cd D:\SCA\Project
"C:\Users\sambi\miniconda3\envs\myenv\python.exe" -m uvicorn app.api.index:app --port 8000
# 2) frontend (new terminal)
cd D:\SCA\Project\app\frontend
npm install        # first time
npm run dev        # http://localhost:5173  (proxies /api -> :8000)
```
Production build: `npm run build` → `dist/`. Set `VITE_API_BASE` to the deployed API for prod.

## Screen → backend source map (verified endpoints)
| Screen | Backend source(s) | Notes |
|---|---|---|
| Home | static (methodology copy reflects real backend) | 8 module tiles → routes; 8-stage methodology |
| Dashboard | `GET /api/scenarios/results`, `/api/criticality`, `/api/monte-carlo` | baseline KPIs, service by group, scenario compare, critical components |
| Network | `GET /api/network`, `/api/criticality` | real 12-node/11-arc SVG map (echelon layout), long-lead arcs flagged |
| Scenario Lab | `POST /api/solve`, `GET /api/scenarios`, `/api/scenarios/results` | draft levers → run → solver-verified KPIs, baseline compare, recommendations |
| Planning | `POST /api/solve` (detail) | cost breakdown, service by group, independent constraint checks, dispatch flows |
| Data Studio | `GET /api/data/summary` | real table catalog + validation; upload shown as not-enabled (honest) |
| Insights | `GET /api/scenarios/results`, `/api/criticality` | cost–service scatter, data-derived priority actions, checklist |
| Reports | `GET /api/scenarios/results`, `GET /api/export/scenario-comparison.csv` | section toggles, print/PDF, real CSV export |
| Settings | `GET /api/health` | theme/compact/reduced-motion (local), real model metadata + health |

## Honest treatments (capabilities not in this build)
- **Live dataset upload/ingestion:** not enabled — Data Studio shows this explicitly instead of faking success. Optimization uses the bundled validated dataset.
- **Run history:** `GET /api/runs` returns runs only when Supabase is configured; otherwise an honest empty note.
- **Currency:** MU (assumed, dimensionless) — never a real currency.
- **Periods:** labeled "Periods 61–74", not calendar dates.

## Visual parity
- `src/styles.css` is the mockup's `styles.css` verbatim (+ 2 small rules: hide mobile-menu on desktop, reduce-motion class). Hero, module grid, 8-stage methodology, sidebar, topbar, cards, tables, charts use the original V4 classes and tokens.
- Charts are the mockup's hand-rolled SVG (line/donut/bars), ported to `src/lib/charts.tsx`, now driven by real data. The network map is rebuilt from the real 12-node graph (the mockup's 7-node diagram was illustrative).
- Removed per V4 approval: floating fake dashboard, capability overlay, intermediate Platform page, dual hero CTAs.

## Deferred to Supabase step (not blocking)
Direct-from-Supabase reads (`VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY`) are scaffolded in
`.env.example` but currently the app reads via the API (identical shapes), so wiring Supabase
later is a config change, not a rewrite.
