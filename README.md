# ResiliPlan AI

Prescriptive decision-support web app for a multi-tier automotive manufacturing supply
chain. A time-indexed (Mixed-Integer) Linear Program, solved with **HiGHS via
`scipy.optimize.milp`**, recommends feasible, cost-efficient production / inventory /
material-flow decisions under a baseline and under disruption scenarios.

Course project — Goa Institute of Management, PGDM-BDA, Supply Chain Analytics
(prescriptive analytics / CLO 5). The graded deliverable is the **working app** plus a
10–15 page report.

## Repository layout

| Path | Contents |
|---|---|
| `CLAUDE.md` | Coder agent charter (standards, rules, phase plan, gates) |
| `validator.md` / `.claude/agents/validator.md` | Read-only validator (owner proxy) spec + subagent |
| `log.md` | Validator's gate-by-gate review log |
| `ResiliPlan_AI_..._Architecture.md` | Original solution blueprint |
| `data/raw/` | Source `.xlsb` (READ ONLY) |
| `data/clean/`, `data/dictionary/`, `data/assumptions/`, `data/scenarios/` | Cleaned tables, data dictionary, assumed cost params, scenario configs |
| `src/utils/` | Shared utilities: paths, figure/table-image savers, logging, seeds, data IO |
| `src/audit,prep,eda,model,scenarios/` | Pipeline code by phase |
| `reports/figures/`, `reports/tables/` | All report-bound PNGs + backing CSVs |
| `reports/figure_index.md` | Auto-maintained index of every saved figure/table |
| `results/` | Solver outputs and logs |
| `app/frontend/`, `app/api/` | React+TS+Tailwind (Vercel) + Python solver API |
| `tests/` | Validation tests (tiny instance, material balances, scaffold) |

## Environment

- Python: conda env **`myenv`** → `C:\Users\sambi\miniconda3\envs\myenv\python.exe`
  (Windows only — see CLAUDE.md §2 for the Smart App Control constraint).
- Dependencies: `requirements.txt`. Solver = HiGHS via SciPy (no Pyomo/highspy/Gurobi).

## Quick check (Gate G0)

```powershell
C:\Users\sambi\miniconda3\envs\myenv\python.exe D:\SCA\Project\tests\test_p0_scaffold.py
```

Exit code 0 means the scaffold, data access, figure pipeline, and solver all work.
