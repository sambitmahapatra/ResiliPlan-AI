# CLAUDE.md — ResiliPlan AI (Coder Agent Charter)

> This file is the standing charter for the **Coder agent** (the main building session).
> It is auto-loaded by Claude Code. A separate **Validator agent** (`validator.md`,
> wired as `.claude/agents/validator.md`) audits every phase read-only and records
> verdicts in `log.md`. Do not start a phase that the Validator has marked BLOCK.

---

## 0. Project in one paragraph

Build **ResiliPlan AI**, a prescriptive decision-support web app for a multi-tier
automotive manufacturing supply chain. Core method: a **time-indexed (Mixed-Integer)
Linear Program** solved with **HiGHS via `scipy.optimize.milp`** (free, SAC-safe — see §2). The app lets a
supply-chain manager run a baseline plan and disruption scenarios, and returns
feasible, cost-efficient production / inventory / material-flow decisions plus
service and cost KPIs. This is a graded group project (Goa Institute of Management,
PGDM-BDA, Supply Chain Analytics). The **deliverable is the working app**, backed by
a 10–15 page report. See `ResiliPlan_AI_Problem_Statement_and_Solution_Architecture.md`
for the full blueprint and `BDASCAProjectGuidelines (1).docx` for grading rules.

---

## 1. Non-negotiable rules (read before every work session)

1. **Never fabricate numbers.** Every figure, KPI, cost, or saving in any output must
   be traceable to a script and its recorded output. No invented savings, no
   plausible-looking placeholders presented as results.
2. **Label every assumption.** The dataset contains **no cost data** and no disruption
   probabilities. All cost coefficients and disruption inputs are **ASSUMED** — tag
   them as such with a documented basis, units, and a sensitivity range.
3. **SAVE EVERY VISUAL AND TABLE AS AN IMAGE.** Every chart, plot, network diagram,
   and results table that will appear in the report must be written as a **PNG** to
   `reports/figures/` via the shared `save_fig` / `save_table_image` utilities, and
   registered in `reports/figure_index.md`. A result that is not saved as an image
   does not count as done. (This is an explicit owner requirement.)
4. **Preserve raw data.** `data/raw/2020_dataset_OfAutomotiveProductionNetwork.xlsb`
   is read-only. Never modify or overwrite it. All cleaning writes to `data/clean/`.
5. **Solver honesty.** Always record solver status (optimal / feasible-not-proven /
   infeasible / time-limited), objective, and MIP gap. Never call a non-optimal
   result "optimal." Infeasible/failed runs are reported as such — never papered over
   with a fabricated recommendation.
6. **Reproducibility.** Fixed random seeds for any simulation. Versioned clean tables.
   Deterministic scripts re-run to the same numbers.
7. **Gate discipline.** At the end of each phase, update `reports/figure_index.md`,
   write a short phase summary, and request Validator review. Do not advance past a
   gate the Validator has not APPROVED.
8. **Academic integrity.** This is coursework. Keep an `AI_USE_DISCLOSURE.md` running
   log of what AI assistance did, for the mandatory report appendix.

---

## 2. Environment & tooling

- **Python:** use the conda env **`myenv`** → `C:\Users\sambi\miniconda3\envs\myenv\python.exe`
  (owner's instruction: Windows `myenv` only, **do not use WSL/Linux** for dev).
  Run data scripts with `-I` when they read files under `data/raw/`.
- **Installed & verified in `myenv`:** pandas, numpy, **scipy 1.15.2**, matplotlib,
  openpyxl, pyxlsb, networkx, plotly.
- **SOLVER = `scipy.optimize.milp` (HiGHS engine).** Verified working on this machine
  (`HiGHS Status 7: Optimal` on a test MILP).
- **⚠ Smart App Control is ENFORCED on this machine (critical constraint).** It blocks
  unsigned, low-reputation native binaries. **`pyomo`+`highspy` DO NOT WORK here** —
  highspy's `_core.pyd` is blocked (confirmed via both pip and conda-forge), and Pyomo's
  compiled extensions are blocked too. Do NOT reintroduce pyomo/highspy/glpk/cbc or any
  standalone solver `.exe`. HiGHS is available **only** because it is bundled inside
  SciPy's trusted wheel. Build the MILP as sparse matrices (`c`, `A_ub`/`A_eq`, `bounds`,
  `integrality`) and solve with `scipy.optimize.milp` / `scipy.optimize.linprog`.
- **Model builder:** write a thin in-house builder in `src/model/` (a variable-index
  registry + constraint assembler over SciPy) so model code stays readable and the
  report's math↔code mapping is clear. No Gurobi, no Pyomo.
- **Node/React:** Node is installed (`C:\Program Files\nodejs\node.exe`). Frontend is
  React + TypeScript + Tailwind (Vite).
- **Shell:** primary is PowerShell; a Bash tool is also available. On Windows, prefer
  calling the env python by full path.

---

## 3. Architecture (as decided by the owner)

- **Frontend:** React + TypeScript + Tailwind (Vite), deployed on **Vercel** (free).
- **Solver API:** **Python serverless functions on Vercel** (`app/api/`, FastAPI-style
  handlers) running **HiGHS via `scipy.optimize.milp`** server-side (same solver code as
  dev — SciPy installs cleanly on Vercel's Linux runtime). The MILP is small (≈49
  components × 12 nodes × 14 periods), so it solves within serverless time limits.
- **Supabase (free):** Postgres (cleaned tables, scenario configs, run history/results),
  Storage (sample dataset files + generated CSV/PDF exports), Auth (test credentials —
  include them in the report).
- **Fallback:** if any scenario is too heavy for serverless, precompute results offline
  and serve a result cache from Supabase. The solver still runs live for in-range inputs.
- The browser never runs the solver. Frontend sends validated scenario params → API
  solves → verifies status → computes KPIs → returns structured JSON.

---

## 4. Ground truth about the dataset (from the completed audit — treat as validated facts)

| Fact | Value |
|---|---|
| Nodes | **12**: `zp7` (OEM assembly), `zp8` (demand/customer), and `prod`/`inv`/`trans` nodes for engine, gear, battery, seat |
| Arcs | **11**, with lead times 0–23 periods; battery-trans=20, seat-trans=23 (exceed the horizon; covered by `initial_flows`) |
| Periods | **61–74 (14 periods)** |
| Products | **28,049**; group `car`=28,000, engine=29, gear=8, seat=4, seat_componment=4, battery_componment=3, battery=1 |
| **Distinct BOM components** | **Only 49** (children). 87,059 BOM rows; each car = 3–4 components (mean 3.1), nested/multi-level |
| Demand | Make-to-order: each car config demanded **1 unit, once**; 2,000 distinct configs/period × 14 = 28,000 |
| Costs | **None present.** All columns are quantity/capacity/lead-time/flow |
| Node production-capacity sheet | None; capacity is on arcs + `max_flow_product/group_per_arc` |

Sheets: `products, nodes, nodes_inflow, arcs, capacity_at_arc, max_flow_product_per_arc,
max_flow_group_per_arc, operations, BOM, demands, initial_inventories, initial_flows`.

**Modeling consequence (key design decision):** model at the **component layer**, not the
finished-car layer. Explode the 2,000 cars/period through the BOM into demand for the
**49 components** per period, then solve the **full network exactly**. Reconstruct
car-level service afterward (a car ships in its period iff all its components are
available). No "representative subset" compromise is needed for correctness; a subset is
only an optional UI drill-down. **Do not build forecasting** — 14 deterministic periods,
demand ≡ 1, make-to-order; it is neither feasible nor meaningful here. Core method is
prescriptive MILP (CLO 5); the only stochastic extension is Monte Carlo on disruptions.

---

## 5. Directory layout (create in P0)

```
D:\SCA\Project\
  CLAUDE.md  validator.md  log.md  AI_USE_DISCLOSURE.md  README.md
  .claude/agents/validator.md
  data/
    raw/            # the .xlsb — READ ONLY
    clean/          # versioned cleaned CSVs (e.g. nodes.v1.csv)
    dictionary/     # data_dictionary.md
    assumptions/    # cost_assumptions.{md,csv}  (ASSUMED params + basis + ranges)
    scenarios/      # scenario_*.json|yaml configs
  src/
    utils/          # save_fig, save_table_image, logging, io, seeds
    audit/  prep/  eda/  model/  scenarios/
  reports/
    figures/        # ALL PNGs (results, charts, tables-as-images)
    tables/         # CSVs backing each figure
    figure_index.md # index: filename -> caption -> source script -> phase
    report_draft.md # assembled 10-15 page report
  results/          # solver outputs per scenario (json/csv)
  tests/            # tiny-instance + material-balance + validation tests
  app/
    frontend/       # React + TS + Tailwind (Vite) -> Vercel
    api/            # Python serverless funcs (scipy.optimize.milp / HiGHS) -> Vercel
  requirements.txt
```

---

## 6. Phase plan & exit gates

Each phase: produce deliverables → save all visuals/tables as PNG + update
`figure_index.md` → write a 5–10 line phase summary → request Validator review.
Advance only on Validator **APPROVE**.

- **P0 — Scaffold.** Dir tree, packages (scipy/pyxlsb/networkx/plotly — all present),
  `requirements.txt`, read-only raw data, `src/utils` (figure-saver, table-to-image,
  logger, seed), seed `AI_USE_DISCLOSURE.md`. Optionally `git init`.
  **G0:** structure + utils exist; `scipy.optimize.milp` (HiGHS) solves a test MILP.
- **P1 — Data audit & dictionary.** Reproduce all Section-4 counts; integrity &
  referential checks (orphan keys, dup keys, type/unit checks, BOM cycles/closure);
  `data/dictionary/data_dictionary.md`; audit summary tables saved as images.
  **G1:** counts reproduce; integrity report + dictionary complete.
- **P2 — Clean + relational model + BOM explosion.** Versioned clean CSVs; connectivity
  proof; **BOM explosion → component demand per period** (the core transform); validation
  that exploded demand reconciles with raw car demand. **G2:** clean tables + explosion
  verified; connected BOM-consistent model documented.
- **P3 — EDA + network & criticality.** Network map; BOM fan-out **component criticality**
  ranking; demand/capacity/lead-time exposure; utilization proxies. All PNG + indexed.
  **G3:** EDA figures saved, criticality ranking reproducible.
- **P4 — Cost & scenario parameterization.** `cost_assumptions` (production/transport/
  holding/shortage/expedite) with basis, units, sensitivity ranges — all flagged ASSUMED;
  scenario configs for the 6 scenarios (baseline, supplier disruption, material delay,
  demand surge, transport constraint, emergency response). **G4:** params documented &
  labeled; scenario files validated.
- **P5 — MILP core + validation.** SciPy/HiGHS component-flow MILP (conservation, BOM/operation
  feasibility, arc/flow capacity, lead times incl. initial in-transit, inventory bounds,
  demand/backorder, disruption hooks, penalized shortage slacks). **Tiny hand-checkable
  instance** + independent material-balance audit + baseline full solve with recorded
  status/objective/gap. **G5:** tiny instance matches hand calc; baseline feasible &
  balances verified.
- **P6 — Scenario & resilience analysis.** Run 6 scenarios; baseline-vs-scenario KPI
  tables (cost breakdown, service/on-time, backorders, utilization, bottlenecks);
  optional Monte Carlo (fixed seed). Every result saved as image + table CSV. **G6:**
  scenario outputs reproducible; comparisons meaningful; nothing fabricated.
- **P7 — App build.** React+TS+Tailwind pages (Overview/context, Data management,
  Supply-chain explorer, Scenario lab, Optimization results, Explainability/validation,
  Reports); Vercel Python solver API; Supabase DB/Storage/Auth; built-in sample data;
  upload + validation + error messages; live-updating charts/KPIs; **CSV/PDF download**;
  manager recommendations; visible assumptions/limitations. **G7:** upload → solve →
  recommendations → export works locally end to end.
- **P8 — Deploy + E2E + report.** Deploy to Vercel+Supabase; public URL; test with sample
  **and** new inputs; assemble the 10–15p report from saved figures (all 13 required
  sections incl. Technology Outlook/CLO6 and AI-use appendix); user guide + test
  credentials. **G8:** live URL works; report complete; submission-ready.

---

## 7. Shared utilities contract (build in P0, use everywhere)

- `save_fig(fig, name, caption, phase)` → writes `reports/figures/{name}.png` (≥150 dpi),
  appends a row to `reports/figure_index.md` (name · caption · source script · phase · UTC).
- `save_table_image(df, name, caption, phase)` → renders a DataFrame to PNG (and writes the
  backing CSV to `reports/tables/{name}.csv`), then indexes it like a figure.
- `get_logger(name)` → consistent run logging under `results/logs/`.
- `SEED = 42` constant for all stochastic work.

Rule of thumb: if a human would look at it in the report, it must pass through `save_fig`
or `save_table_image`.

---

## 8. Working with the Validator

- The Validator is **read-only** on everything except `log.md`. It reproduces your
  numbers, checks honesty and guideline alignment, and writes a verdict per gate.
- After each phase, post a short "Ready for G{n} review" summary and let the Validator
  run (it is wired as the `validator` subagent).
- If the Validator records **CHANGES REQUESTED** or **BLOCK**, address every item and
  request re-review before advancing. Treat the Validator as the owner's stand-in.
