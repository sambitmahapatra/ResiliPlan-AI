# log.md — ResiliPlan AI Validation Log

Maintained by the **Validator agent** only (read-only project-owner proxy). One appended
entry per gate review. Verdicts: **APPROVE** / **CHANGES REQUESTED** / **BLOCK**.
Entry format is defined in `validator.md` §6.

---

## [2026-11-19] — Project setup (pre-build)
**Verdict:** n/a (setup only — building not yet started)

### Established
- Assignment requirements extracted from `BDASCAProjectGuidelines (1).docx`.
- Dataset audited (`2020_dataset_OfAutomotiveProductionNetwork.xlsb`): 12 nodes, 11 arcs,
  periods 61–74, 28,049 products but only **49 distinct BOM components**, make-to-order
  demand (1 unit/config/period), **no cost data present**.
- Blueprint reviewed; upgrades agreed: component-layer MILP (exact, no subset compromise),
  drop forecasting, add BOM fan-out component-criticality, React+TS+Tailwind on
  Vercel+Supabase with Pyomo+HiGHS as Vercel Python serverless functions.
- Agent charters created: `CLAUDE.md` (Coder), `validator.md` + `.claude/agents/validator.md`
  (Validator). Phase plan P0–P8 with gates G0–G8 defined.

### Status
- **Awaiting owner green signal to begin P0.** No project code, data cleaning, or app
  work has started. First Validator review will be at **Gate G0**.

---
<!-- Validator appends gate reviews (G0 … G8) below this line. -->

## [2026-11-19 08:52 UTC] — Review of P0 / Gate G0
**Verdict:** APPROVE

### Reproduced
- Re-ran `tests/test_p0_scaffold.py` with `myenv` python → **exit code 0**, "G0 SELF-TEST:
  ALL CHECKS PASSED". All 13 checks PASS.
- Independently confirmed audited counts via the test's `read_raw` calls: products
  (28049, 3), BOM (87059, 3), 12 nodes, 11 arcs, **49 distinct BOM components**, demand
  periods 61–74 — all match CLAUDE.md §4.
- Solver smoke test reproduced: `scipy.optimize.milp` (HiGHS) returns x=[6,4], obj=26.0 on
  the hand-checkable MILP (maximize 3x+2y s.t. x+y≤10, x≤6, y integer). Optimal, success=True.
- Confirmed artifacts actually written: `reports/figures/p0_selftest.png`,
  `reports/figures/p0_selftest_table.png`, backing `reports/tables/p0_selftest_table.csv`,
  both rows registered in `reports/figure_index.md`, log at `results/logs/p0_selftest.log`.

### Checklist
- [x] Reproducibility — self-test exit 0; counts + solver reproduce exactly.
- [x] Honesty / labeled assumptions — no numbers claimed yet; no cost data introduced;
  `AI_USE_DISCLOSURE.md` seeded; solver choice/SAC constraint documented honestly.
- [x] Figures & tables saved as images + indexed — `save_fig`/`save_table_image` both
  write PNG to `reports/figures/`, CSV to `reports/tables/`, and auto-append to
  `reports/figure_index.md`; verified end-to-end.
- [x] Guideline alignment — core method is SciPy/HiGHS MILP (CLO 5); no forecasting; layout
  matches CLAUDE.md §5; env is `myenv` only.
- [x] Data governance — `data/raw/*.xlsb` is read-only (`-r--r--r--`), original copy left at
  project root, `.gitignore` deliberately does NOT ignore `data/raw`, `reports/*`, `data/clean`.

### Findings
1. Directory tree complete and matches CLAUDE.md §5 (data/{raw,clean,dictionary,assumptions,
   scenarios}, src/{utils,audit,prep,eda,model,scenarios}, reports/{figures,tables},
   results/logs, tests, app/{frontend,api}, .claude/agents).
2. Shared utils all present and correct: `paths.py` (central paths + `ensure_dirs`),
   `seeds.py` (SEED=42, `set_seeds`), `logging_utils.py`, `figures.py` (save_fig +
   save_table_image + auto index), `data_io.py` (read_raw/read_all_raw/save_clean/read_clean),
   `__init__.py` re-exports the public API.
3. No dependency on pyomo/highspy/glpk/cbc/gurobi — grep of non-doc files found only the
   explanatory comment in `requirements.txt` stating they are intentionally unused (SAC).
   `requirements.txt` pins scipy==1.15.2 (HiGHS bundled).
4. `figures.py` enforces the owner's image rule: a table cannot be saved without also
   writing its backing CSV, and both figures and tables funnel through `_update_index`.
5. MINOR: the G0 self-test registers two *disposable* figures (`p0_selftest`,
   `p0_selftest_table`) into the real `reports/figure_index.md` and leaves their PNGs/CSV in
   the deliverable `reports/` tree. Not a correctness/honesty issue, but these artifacts
   should not ship in the final report index.

### Required changes (if any)
- None blocking for G0. (Recommended, not required: before the report is assembled, have the
  self-test write its disposable outputs to the scratch/temp dir or clean them up afterward
  so `reports/figure_index.md` lists only genuine report figures. Can be deferred.)

### Notes to owner
- Solver decision stands as pyomo+highspy → `scipy.optimize.milp` (HiGHS) due to Smart App
  Control blocking the native binaries on this machine. This was verified working, is
  SAC-safe, and installs cleanly on Vercel's Linux runtime. It also means the earlier
  log.md "Project setup" note (which still says "Pyomo+HiGHS") is now superseded — the
  authoritative statement is CLAUDE.md §2. No action needed; flagging for your awareness.
- G0 technical gate is met; Coder is cleared to begin P1 (data audit & dictionary).

---

## [2026-11-19 09:16 UTC] — Review of P1 / Gate G1
**Verdict:** APPROVE

### Reproduced
- Re-ran `src/audit/p1_data_audit.py` with `myenv` python (`-I`) -> **exit code 0**. Console
  summary: counts all match=True, duplicate-key sheets=none, referential failures=none,
  BOM DAG(real edges)=True, max depth=2, benign identity rows=49, negative quantities=False.
- Read `results/p1_audit_results.json` and confirmed every claim: `counts_all_match=true`
  (all 12 count checks match, incl. products 28049x3, BOM 87059, nodes 12, arcs 11, distinct
  components 49, car 28000, demand 28000 rows / periods 61-74, capacity_at_arc 154);
  `referential_failures=[]` (20 referential checks, all 0 violations); `duplicate_key_sheets=[]`
  (12 candidate keys, 0 dups); `bom.is_dag_real_edges=true`, `max_depth=2`, `identity_rows=49`,
  `real_cycle="none"`, `pure_leaves=44`; `integrity.columns_with_missing=0`;
  `any_negative_quantities=false`.
- Independent raw-workbook recheck (my own script, outside project tree, `-I`): BOM
  mother==child rows = **49**, and that set of identity ids **equals** the set of 49 distinct
  children (True); `demands.product_p subset products.product_p` after canonicalization
  (missing=0), with raw dtypes genuinely differing (demands int64 vs products object) — so the
  ID-dtype fix is legitimate, not masking a real violation; arcs start/end nodes subset nodes
  (both True); BOM rows 87059, distinct children 49, products 28049, group car 28000, demand
  28000 / 61-74.

### Checklist
- [x] Reproducibility — audit re-runs to exit 0; JSON + console reproduce; 3 facts
  re-derived straight from the `.xlsb` match independently.
- [x] Honesty / labeled assumptions — no fabricated numbers; dictionary explicitly states
  **NO cost data** and that all units are documented assumptions; the 49 identity rows are
  disclosed and correctly separated from real BOM edges before acyclicity/depth are judged.
- [x] Figures & tables saved as images + indexed — all 10 `p1_*.png` present in
  `reports/figures/`; 8 table-image backing CSVs in `reports/tables/` (the 2 bar charts are
  `save_fig` plots, correctly no CSV); all 10 registered in `reports/figure_index.md`.
- [x] Guideline alignment — pure data-audit phase; no scope creep; no forecasting; method
  stays on track for prescriptive MILP.
- [x] Data governance — `data/raw/*.xlsb` is read-only (`-r--r--r--`), untouched;
  `data/dictionary/data_dictionary.md` covers all 12 sheets and every column with keys,
  dtypes, distinct/missing counts, examples, and semantics.

### Findings
1. All CLAUDE.md section-4 ground-truth counts reproduce exactly (`p1_count_reproduction`,
   `results/p1_audit_results.json`).
2. Integrity clean: 0 missing values, 0 duplicate-key rows across 12 candidate keys, 20/20
   referential checks pass with 0 violations.
3. BOM correctly modeled as 49 benign identity rows (mother==child, qty 1, one per component)
   + real parent->child edges forming a DAG of depth 2 with 44 pure leaves — consistent with
   the "nested/multi-level, each car 3-4 components" fact. No real cycle.
4. The ID-dtype normalization (`_cid`, `src/audit/p1_data_audit.py:46-59`) is applied uniformly
   to both sides of every join; independently confirmed the underlying values genuinely match
   (demands subset products, missing=0), so it corrects a representation artifact, not a data
   defect. The dictionary still honestly reports demands.product_p as raw int64.
5. Dictionary states the cost-data-absent and units-assumed caveats up front (lines 13-14).

### Required changes (if any)
- None.

### Notes to owner
- Re-running the deterministic audit regenerated the P1 figures/CSVs and appended-in-place
  `reports/figure_index.md` identically (same script, same inputs); no hand edits were made.
- Several per-sheet row counts in the dictionary (e.g. nodes_inflow 44, max_flow_product 365,
  operations 15, initial_inventories 82, initial_flows 117) are auto-derived and not in
  CLAUDE.md section 4; they are internally consistent with `read_all_raw` but were not
  separately cross-audited against the blueprint. Low risk; flag only if the blueprint cites
  different numbers.
- G1 is met; Coder is cleared to begin P2 (clean tables + BOM->component-demand explosion).

---

## [2026-11-19 09:22 UTC] — Review of P2 / Gate G2
**Verdict:** APPROVE

### Reproduced
- Re-ran `src/prep/p2_clean_and_explode.py` with `myenv` python (`-I`) -> **exit 0**.
  `results/p2_results.json` confirms `weakly_connected=true`, `unreached_to_zp8=[]`,
  `cars_with_empty_bom=0`, `totals_match=true` (explosion_total==independent_total=175063.0),
  `per_period_match=true`, `n_component_period_rows=680` (49 distinct components).
- **Independent hand-trace of the BOM explosion (no coder code reused):**
  - Car 64001: direct children DK8(1), G0C(1), Q4H(1); Q4H->componment_seat2(1); others leaf.
    Hand total {DK8:1,G0C:1,Q4H:1,componment_seat2:1} == `component_requirements.v1.csv` rows. MATCH.
  - Car 64002: direct D83(1),G1Z(1),BEV(1),Q2J(1); BEV->cb1(10),cb2(6),cb3(4); Q2J->seat1(1).
    Hand total {D83:1,G1Z:1,BEV:1,cb1:10,cb2:6,cb3:4,Q2J:1,seat1:1} == requirements rows. MATCH.
  - Independent aggregate (my own pandas query, not the script): BEV gross demand @period61 = 52
    (3003 cars carry a BEV direct-parent edge) == coder's 52; componment_battery1 @61 = 520 = 10x. MATCH.
- Row-count integrity (no silent loss): BOM 87059, **bom_real 87010 = 87059-49**, products 28049,
  demands 28000, nodes 12, arcs 11, capacity_at_arc 154, nodes_inflow 44, operations 15,
  initial_inventories 82, initial_flows 117, max_flow_product 365, max_flow_group 20 — all match
  P1/§4 ground truth. component_demand 680 rows, component_requirements 124012 rows.

### Checklist
- [x] Reproducibility — script re-runs to exit 0; JSON + console reproduce; explosion verified by
  independent hand-trace (2 cars incl. nested battery) and an independent aggregate query.
- [x] Honesty / labeled assumptions — no fabricated numbers; the "operation yield ratios deferred to
  MILP" decision is documented (lines 124-127) and defensible: BOM input quantities q_mc (10/6/4 per
  BEV) are applied; the group-level 20:1 production recipe (operations.csv `battery-supplier_prod`)
  is correctly left for P5 production constraints, avoiding double-counting. No cost data introduced.
- [x] Figures & tables saved as images + indexed — all 6 `p2_*.png` in `reports/figures/`; 5 backing
  CSVs in `reports/tables/` (the 6th, `p2_component_demand_per_period`, is a save_fig bar chart =
  correctly no CSV); all 6 registered in `reports/figure_index.md`.
- [x] Guideline alignment — pure data-prep/transform phase; core method stays prescriptive MILP;
  no forecasting; component-layer modeling per §4 realized by the explosion.
- [x] Data governance — `data/raw/*.xlsb` still `-r--r--r--`, mtime 13:17, untouched by the re-run;
  12 versioned clean CSVs + 3 derived (bom_real, component_requirements, component_demand).

### Findings
1. BOM explosion is correct, not merely internally consistent: independent hand calculations for two
   cars (one battery-nested) and an independent aggregate reproduce the coder's rows exactly.
2. Connectivity proof holds: network weakly connected, all 12 nodes reach demand node zp8, 0 unreached.
3. No silent row loss across any table; bom_real correctly drops exactly the 49 identity rows.
4. Figure/table-as-image compliance fully met for P2.

### Required changes (if any)
- None.

### Notes to owner
- P5 cross-check to carry forward: ensure the MILP does not double-apply the battery conversion. The
  BOM already encodes 10+6+4=20 battery_componment per battery; `operations.csv` separately states a
  group-level 20:1 (`battery-supplier_prod`, input_quantity=20 -> output 1). These must reconcile to a
  single 20:1 at the production node, not stack. This is a P5 modeling item, not a P2 defect.
- `component_requirements.v1.csv` is 124,012 rows (per-car descendant detail) — large but fine for
  explainability; the MILP should consume the compact 680-row `component_demand.v1.csv`.
- G2 is met; Coder is cleared to begin P3 (EDA + network & component criticality).

## [2026-11-19 09:35 UTC] — Review of P3 / Gate G3
**Verdict:** APPROVE

### Reproduced
- Re-ran `src/eda/p3_eda_network_criticality.py` with `myenv` python (`-I`) -> **exit 0**;
  read `results/p3_results.json`. Console + JSON agree.
- **Independent criticality recompute (my own pandas/networkx, no coder code):**
  from `component_requirements.v1.csv` distinct cars using Q4H = **12038 (42.99% of 28000)**;
  componment_seat2 = 12038 (42.99%); Q2J = 9726 (34.74%); G0K = 8592 (30.69%) — all match
  JSON exactly; total distinct cars = 28000.
- From `component_demand.v1.csv`: Q4H gross = 12038, componment_seat2 = 12038,
  componment_battery1 = 30030, BEV = 3003; grand total gross demand = **175063.0**
  (reconciles with P2's explosion total). Matches `component_criticality.v1.csv`.
- Cumulative lead time to zp8 (summed over arcs in `arcs.v1.csv`): seat-supplier_trans ->
  seat-supplier_prod -> seat-supplier_inv -> zp7 -> zp8 = 23+0+0+0 = **23** (seat components,
  highest); battery-supplier_trans path = 20+1+1+0 = **22**. Confirms "highest lead-time =
  seat components (23)."
- **Arc utilization logic independently reproduced:** all 11 arcs have unique (i,j) and exactly
  one `group_g`; componment origins verified via `nodes_inflow.v1.csv` (seat componments at
  seat-supplier_trans, battery componments at battery-supplier_trans). Recomputing demand/cap by
  group: battery-supplier_trans->battery-supplier_prod [battery_componment] max_util=**3.732**,
  periods_over=1; battery-supplier_inv->zp7 [battery] max_util=**2.412**, periods_over=3 — match.

### Checklist
- [x] Reproducibility — script exit 0; JSON + console reproduce; criticality, lead-time, and
  utilization numbers independently re-derived from clean data and all match.
- [x] Honesty / labeled assumptions — no cost data introduced; the >1.0 arc-utilization values
  are explicitly captioned (figure title + index captions) as a **static same-period demand/
  capacity PROXY**, with lead-time shifting/inventory/initial in-transit deferred to the P5 MILP.
  Not claimed as proven infeasibility. `risk_score` is a transparent constructed heuristic
  (fan-out x cumulative lead time), computed in code, not presented as a dataset quantity.
- [x] Figures & tables saved as images + indexed — all **7** `p3_*.png` present in
  `reports/figures/`; the 2 table-images (`p3_criticality_ranking`, `p3_arc_utilization_summary`)
  have backing CSVs in `reports/tables/`; the other 5 are `save_fig` plots (correctly no CSV);
  all 7 registered in `reports/figure_index.md` (lines 23-29).
- [x] Guideline alignment — pure EDA/criticality phase; no scope creep; no forecasting; method
  stays on track for prescriptive MILP. Component-layer analysis consistent with §4.
- [x] Data governance — `data/raw/*.xlsb` still `-r--r--r--`, mtime 13:17 (untouched by re-run);
  `component_criticality.v1.csv` = 49 distinct components, 0 null cum_lead_time.

### Findings
1. Every headline P3 number (top fan-out Q4H/componment_seat2 = 12038/42.99%; seat-component
   lead time 23; bottleneck battery arcs 3.73 / 2.41) reproduces from clean data without the
   coder's code. No fabrication.
2. Arc-utilization model is methodologically sound for a proxy: one group per arc, demand =
   that group's gross demand per period (car demand added on zp7->zp8), and the >1.0 readings
   are honestly framed as pre-optimization pressure indicators.
3. Figure/table-as-image compliance fully met (7 figures + 2 backing CSVs, all indexed).

### Required changes (if any)
- None.

### Notes to owner
- `risk_score = n_cars_using * cum_lead_time` is a reasonable but constructed heuristic. A side
  effect: finished-seat items Q4H/Q2J have the highest fan-out yet risk_score = 0 because their
  production arcs carry lead time 0 in the data, so the risk ranking surfaces the componment_seat
  items instead. Defensible, but you may want to decide whether the report's "criticality"
  narrative should weight breadth (fan-out) and lead-time exposure differently. Not blocking.
- The static arc-utilization proxy shows battery supply arcs at 2.4-3.7x same-period capacity;
  this is a pressure flag only. Whether it is real must be judged by the P5 MILP (with lead-time
  shifting, inventory and initial in-transit flows). Carry forward as a P5/P6 check.
- G3 is met; Coder is cleared to begin P4 (cost & scenario parameterization).

## [2026-11-19 09:40 UTC] — Review of P4 / Gate G4
**Verdict:** APPROVE

### Reproduced
- Re-ran `C:/Users/sambi/miniconda3/envs/myenv/python.exe -I src/scenarios/p4_cost_and_scenarios.py` → EXIT=0. Output: 13 ASSUMED cost params, 6 scenarios, "all arc/node refs valid: True".
- Opened data/assumptions/cost_assumptions.csv/.md/cost_params.json and all 6 data/scenarios/scenario_*.json + scenarios_index.json.
- Validated every scenario arc against data/clean/arcs.v1.csv; confirmed period refs vs the 61-74 horizon; sanity-checked shortage/fulfilment ratio; confirmed cost_params.json matches CSV; confirmed the 2 PNGs + backing CSVs exist and are indexed; confirmed raw .xlsb untouched (read-only, unchanged).

### Checklist
- [x] Reproducibility — script re-runs deterministically to the same 13 params / 6 scenarios; results/p4_results.json matches console.
- [x] Honesty / labeled assumptions — all 13 cost rows carry status=ASSUMED, a basis, units, and sensitivity_low/high. .md and cost_params.json both state "source workbook contains NO cost data"; MU explicitly "dimensionless / relative ratios", never presented as real/observed prices. All 6 scenarios labeled SYNTHETIC with a disclaimer "not observed historical events."
- [x] Figures & tables saved as images + indexed — reports/figures/p4_cost_assumptions.png, p4_scenarios_summary.png both present, backed by reports/tables/*.csv, registered at figure_index.md lines 30-31.
- [x] Guideline alignment — scope stays prescriptive MILP; scenarios map to the 6 required (baseline + 5 disruptions); no forecasting creep.
- [x] Data governance — data/raw/ .xlsb still mode -r--r--r--, unmodified; outputs written to data/assumptions, data/scenarios, reports, results only.

### Findings
1. Arc references all valid (script `arc()` asserts membership; run passed): battery-supplier_prod->battery-supplier_inv (arcs.v1 row 9), gear-supplier_inv->zp7 (row 3), engine-supplier_inv->zp7 (row 4). All match.
2. Period references in-horizon: supplier_disruption/emergency [64-67], demand_surge [66-68] all within 61-74; material_delay & transport_constraint use "periods":"all". Consistent.
3. cost_params.json numerically identical to CSV (prod_cost car=1000/engine=300/gear=150/battery=250/seat=120/battery_componment=15/seat_componment=20; transport base=2, per_lead=1.0; holding=0.02; shortage=5000; expedite_mult=3.0, lead_reduction=1). Internally consistent for MILP consumption.
4. Shortage penalty 5000 MU/car/period vs full per-car fulfilment (~1800-2500 MU: car 1000 + engine 300 + gear 150 + battery 250 + seat 120 + sub-components + transport/holding) → ~2x the fulfilment cost; even the sensitivity_low 3000 stays above fulfilment. Service-priority dominance holds. Sanity check passes.

### Required changes (if any)
- None blocking. (Minor/optional: baseline scenario carries the generic "Disruption inputs are SYNTHETIC..." disclaimer despite having no disruptions — harmless but slightly redundant; Coder may leave as-is.)

### Notes to owner
- The 13 cost values (MU, relative) and all disruption parameters (capacity factors, lead deltas, demand multipliers, expedite premium) are ASSUMPTIONS by construction — the workbook has no cost/probability data. They are internally consistent for relative-ratio optimisation, but the actual magnitudes and sensitivity ranges are the team's to review/adjust before the report; P6 sensitivity analysis should exercise the stated low/high bands.

## [2026-11-19 09:58 UTC] — Review of P5 / Gate G5
**Verdict:** APPROVE

### Reproduced
- Re-ran `tests/test_tiny_instance.py` (`myenv` python) -> **exit 0**, "TINY-INSTANCE: ALL CHECKS
  PASSED" (10/10). Independently checked the hand logic: Case1 obj 4560 = produce 15 engines @300
  (4500) + 15 units x 2 arcs x base-2 transport (60) + 0 holding (produce=serve same period) + 0
  shortage. Case2 cap 6 on inv->zp7 @t61 with demand 10 -> shortage 4 (no backward backorder, so
  t61 unmet is lost). Case3 BEV transform: 10+6+4 = **20** sub-components produced for 1 BEV,
  applied **once** (not 20x20).
- Re-ran `src/model/p5_baseline_solve.py` (`-I`) -> **exit 0**. `results/p5_baseline.json`:
  status 0 (HiGHS optimal), success true, objective **18,395,031 MU**, objective_recomputed
  18,395,031, **objective_reconciles=true**; validation **all_ok=true** with max_balance_residual
  **0.0** and max_capacity_violation **0.0**, negatives 0; service 98.22% overall, battery 48.32%,
  engine/gear/seat 100.0%. All match the Coder's reported numbers exactly.
- Cost breakdown reconciles by hand: prod 9,920,000 + tx 370,717 + hold 344,314 + short 7,760,000
  = 18,395,031; shortage 1552 units x 5000 = 7,760,000. Direct demand 87,003 = engine 28000 + gear
  28000 + seat 28000 + battery 3003.
- **Independent material balance** (my own script, not the model matrix): BEV @ zp7, period 70 ->
  inv[70] 366 = inv[69] 254 + arrivals 294 - served 182 - shipout 0. Residual **0**. Demand(70)=182,
  short=0. Holds on the actual solution numbers.

### Checklist
- [x] Reproducibility — tiny tests exit 0; baseline exit 0 and reproduces to the unit; one material
  balance re-derived independently to residual 0.
- [x] Honesty / labeled assumptions — solver status recorded honestly; LP solved to HiGHS optimality
  is genuinely optimal (no integrality => no MIP-gap concern); nothing non-optimal labeled optimal;
  all cost coefficients come from the P4 ASSUMED `cost_params.json`; no fabricated savings.
- [x] Figures & tables saved as images + indexed — all 6 `p5_*.png` present and registered in
  `reports/figure_index.md` (lines 32-37); the 2 table-images (`p5_baseline_kpis`,
  `p5_service_by_group`) have backing CSVs in `reports/tables/`; the other 4 are `save_fig` plots.
- [x] Guideline alignment — prescriptive optimisation (CLO 5); no forecasting; scenario hooks
  (arc lead delta, capacity multiplier, demand multiplier, expedite flag) present for P6.
- [x] Data governance — `data/raw/*.xlsb` still `-r--r--r--`, mtime 13:17, untouched; outputs only
  under results/, reports/.

### Findings
1. **Battery/seat 20:1 applied ONCE — confirmed** (modeling_notes #1). `instance.py` builds the
   transform from BOM SKU quantities only ({BEV: cb1 10, cb2 6, cb3 4} = 20); `milp.py:149-152`
   consumes `q * prod(parent)` at the transform node; the operations group-level 20:1 is NOT
   re-applied. Case3 proves sub_total == 20 for 1 BEV.
2. **No double-count of demand — confirmed.** Only DIRECT_GROUPS {engine,gear,battery,seat} carry
   zp7 demand/served/short (`milp.py:120-123,168-173`); sub-component rows in
   `component_demand.v1.csv` are ignored and their requirement is derived solely from the transform.
   Battery subs needed = 3003 x 20 = 60,060 (single count), not stacked.
3. **Battery 48.32% is a genuine data-driven result, NOT a bug.** The battery_componment arc
   (battery-supplier_trans -> battery-supplier_prod) has lead **20**; in-horizon sub-component
   production (confirmed 0 units, arrives period 81+ > horizon 74) cannot help. Usable battery-sub
   supply in-horizon = init_inv at prod 1,860 + initial_flows arrivals 27,380 = **29,240**, enough
   for only 29,240/20 = **1,462** batteries, plus ~411 pre-made/in-transit finished batteries ->
   theoretical cap ~1,873 vs demand 3,003. With shortage penalty 5000 >> holding/production the
   solver serves everything it physically can (1,451 served; timing/per-period loss accounts for
   the gap below the 1,873 cap). initial_flows/init_inv are correctly seeded (arrivals after the
   horizon are correctly excluded).
4. Solver code is pure SciPy/HiGHS: `grep -i pyomo|highspy|glpk|cbc|gurobi` over `src/` -> **no
   matches**. Model built as sparse COO (`milp.py:175,195`) and solved via `scipy.optimize.milp`.
   Variables are all continuous (`integrality=np.zeros`) — implemented as an LP (docstring says so).
5. Independent validation (`validate.py`) genuinely re-derives balances/demand/capacity/nonneg from
   solution values, not the model matrix; it is a real cross-check, not a tautology.

### Required changes (if any)
- None blocking.

### Notes to owner
- **Report-narrative accuracy (please tighten in P6/P8):** the one-line reason "battery 48% because
  battery_componment lead 20 > horizon 14" is *incomplete* — the seat sub-component arc has an even
  longer lead (**23**) yet seat service is **100%**. The true differentiator is **pipeline volume x
  consumption ratio + timing**: seat is 1:1 and its pipeline (34,000 subs) covers 28,000 seat demand;
  battery is 20:1 so its 29,240-sub pipeline covers only ~1,462 builds vs 3,003 BEV demand. State it
  this way in the report so the finding is defensible.
- **LP vs MILP:** CLAUDE.md §0 says "(Mixed-Integer) LP"; the P5 model is a **pure LP** (all vars
  continuous). The solution happens to come out integer here, and the docstring is honest about it,
  but the report should either justify the LP relaxation (naturally near-integral network flow) or
  flip the demand/flow variables to integer if integrality must be guaranteed. Your call.
- **Lost-sales vs backorder:** demand is served + short per period with **no backward backorder**
  (unmet demand in period t cannot be filled in t+1; inventory only carries forward). modeling_notes
  #5 uses the word "backorder" loosely. This is a legitimate lost-sales model but should be named
  accurately in the report.
- G5 is met; Coder is cleared to begin P6 (6-scenario + resilience analysis). Carry the battery
  pipeline finding and the P3 arc-pressure flags into P6 for honest baseline-vs-scenario comparison.

## [2026-11-19 11:31 UTC] — Review of P6 / Gate G6
**Verdict:** APPROVE

### Reproduced
- Re-ran `tests/test_tiny_instance.py` (`myenv`) -> **exit 0**, "TINY-INSTANCE: ALL CHECKS
  PASSED" (10/10), incl. Case3 battery 20:1 applied once. Solver fix did not break tiny cases.
- Re-ran `src/model/p5_baseline_solve.py` (`-I`) -> **exit 0** in <1s (vs the old ~44s):
  status 0 (HiGHS optimal), objective **18,395,031** (recomputed 18,395,031, reconciles=True),
  validation **all_ok=True**, max_balance_residual **0.0**, max_cap_viol **0.0**, service 98.22%
  / battery 48.32% / engine,gear,seat 100%. Identical to G5 — the direct-HiGHS solve returns the
  same optimum, confirming the performance fix changed only the solve call, not the math.
- Re-ran `src/scenarios/p6_scenarios.py` (`-I`) -> **exit 0** (~17s). All 6 scenarios
  **optimal** and **independently validated** (all_optimal=true, all_valid=true in
  `results/p6_results.json`). Reproduced every headline number: baseline 18,395,031/98.2%/bat48.3;
  supplier_disruption 18,395,831/98.2%/48.3 (arc not binding); material_delay 39,837,879/93.1%,
  gear 84.2%; demand_surge 25,088,831/97.1%, battery 46.0%/seat 96.6%; transport_constraint
  44,777,951/91.8%, engine 79.9%; emergency_response 16,450,508/98.7%, battery 61.9%,
  expedite_units 1390. Monte Carlo (40 runs, seed 42) service mean 97.73% [90.26, 98.62].
- **Monte Carlo reproducibility:** ran P6 twice; MC service_mean 97.73125 / min 90.26 /
  max 98.62 identical both times (seeded `np.random.default_rng(42)` + `set_seeds()`).
- Confirmed solver is scipy's **bundled** HiGHS (`src/model/milp.py:29`
  `import scipy.optimize._highspy._core`), not the SAC-blocked standalone `highspy`/pyomo.

### Checklist
- [x] Reproducibility — tiny + baseline + P6 re-run to exit 0; all objectives/service levels
  reproduce to the unit; Monte Carlo bit-identical across two runs.
- [x] Honesty / labeled assumptions — all costs from P4 ASSUMED `cost_params.json`; every
  scenario config carries nature=SYNTHETIC + disclaimer; nothing non-optimal labeled optimal;
  no fabricated savings. The counter-intuitive emergency<baseline cost is a genuine optimisation
  outcome (see Findings 2), not an invented benefit.
- [x] Figures & tables saved as images + indexed — all **7** `p6_*.png` present in
  `reports/figures/`; 3 table-images (`p6_scenario_comparison`, `p6_service_by_group_scenarios`,
  `p6_monte_carlo_summary`) + raw `p6_monte_carlo_runs.csv` backed in `reports/tables/`; all 7
  registered in `reports/figure_index.md` (lines 38-44). The 4 plots correctly have no CSV.
- [x] Guideline alignment — prescriptive MILP (CLO5) + seeded Monte Carlo resilience extension;
  no forecasting creep; 6 required scenarios covered.
- [x] Data governance — `data/raw/*.xlsb` still `-r--r--r--`, mtime 13:17, untouched by all
  re-runs; outputs only under results/, reports/.

### Findings
1. **Solver performance fix is sound and result-preserving.** `_highs_solve` (milp.py:38-76)
   builds the same c/A_eq/A_ub/bounds and calls `scipy.optimize._highspy._core` directly,
   skipping linprog/milp's per-variable marginal extraction. Baseline and tiny results are
   byte-identical to G5; status is read honestly from `modelStatusToString` and mapped (only
   "Optimal" -> success). No math changed.
2. **emergency_response cost (16.45M) < baseline (18.4M) is LEGITIMATE, not a bug.**
   - Verified cost delta exactly: prod +102,000, transport(incl expedite) +6,618, holding
     -13,141, shortage -2,040,000 => net -1,944,523 = 18,395,031 - 16,450,508. The 5000/unit
     shortage penalty dominates: cutting shortage from 1552 to 1144 units (-408) saves 2.04M,
     dwarfing the 8,340 MU expedite premium + 102K extra production.
   - Mechanism is timing/capacity, not fabricated material: expedite (lead-1 reduction +
     capacity bypass at 3x premium) lets the EXISTING battery sub-component pipeline reach zp7
     within demand periods, raising battery service 48.3%->61.9% (~1,859 builds), right at the
     ~1,873 physical pipeline cap identified in G5. No new material is created.
   - Why below baseline: emergency_response = supplier_disruption + `enable_expedite`. Expedite
     is a capability baseline LACKS, so it strictly enlarges the feasible set; it also relieves
     the chronic baseline battery-arc timing/capacity bottleneck (P3 flagged inv->zp7 at 2.4x).
     The clean "is expedite worth it" comparison is supplier_disruption (18,395,831) vs
     emergency_response (16,450,508) — both carry the disruption, differ only by expedite.
3. **Expedite is correctly and consistently modeled in milp.py AND validate.py.** Arrivals use
   reduced lead (`dep_e = t - max(0, lead-1)`) and eship is a distinct variable (no arrival
   double-count); eship is included in both shipout and arrivals; eship is EXCLUDED from arc
   capacity in both the model (milp.py:246-250) and the independent validator (validate.py:114)
   — intentional "bypass capacity" behaviour, applied symmetrically. emergency_response
   validates to max_resid 0.0 with expedite active, so balances hold. 8,340 MU / 1390 units =
   6 MU/unit = (base 2 + 0 lead)*3, consistent with expedite on lead-1 arcs.
4. **Expedite activates only for emergency_response.** `enable_expedite` is read from each
   scenario's modifications; eship vars are created only when on. All other 5 scenarios
   expedite_units=0 (confirmed in JSON); baseline=0.
5. **Other scenarios behave sensibly.** material_delay (+3 lead on gear-supplier_inv->zp7) ->
   gear service 100%->84.2%, shortage/cost rise, battery unchanged. transport_constraint (engine
   inbound cap x0.6) -> engine 79.9%. demand_surge (x1.3, p66-68) -> total demand 92,555, battery
   46.0%/seat 96.6%. supplier_disruption (battery prod->inv cap x0.5, p64-67) barely moves the
   objective (+800 holding) because battery is already pipeline-capped at 48.3% — honest
   "arc not binding" result consistent with the G5/P3 carry-forward flag.

### Required changes (if any)
- None blocking.

### Notes to owner
- **Report framing for emergency_response (please make explicit):** presenting its 16.45M next
  to the 18.4M baseline will read as "a disruption made things cheaper" unless the report states
  that this scenario BOTH injects the battery capacity cut AND unlocks a new expedite policy that
  baseline never had. Recommend reporting the expedite value as supplier_disruption ->
  emergency_response (same disruption, +expedite): ~1.945M saved, battery +13.6pp. The scenario's
  own managerial_question already frames it this way.
- **Document the "expedite bypasses arc capacity" assumption.** The 3x multiplier and 1-period
  lead reduction are in `cost_params.json` as ASSUMED, but the structural choice that expedited
  flow is UNCAPPED (ignores arc capacity) lives only in code. State it as a labeled assumption
  (basis: emergency/air freight outside contracted lanes) in the report so the 61.9% result is
  defensible.
- Carry forward from G5 (still open, report-wording items, not code): name the model "lost-sales"
  (not backorder); justify LP relaxation vs MILP; state battery driver as pipeline-volume x
  consumption-ratio x timing (not merely "lead > horizon").
- G6 is met; Coder is cleared to begin P7 (app build).
