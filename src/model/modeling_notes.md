# Modeling Notes (for the P5 MILP)

Running record of modeling decisions and traps surfaced during earlier phases. Read
before implementing the MILP.

## 1. Avoid double-counting the battery (and seat) conversion — CRITICAL
The 20:1 battery conversion is expressed **twice** in the raw data, consistently:
- **BOM (SKU level):** 1 battery (BEV) requires componment_battery1×10 + _2×6 + _3×4 = **20**.
- **operations (group level):** `battery-supplier_prod`: battery_componment (20) → battery (1).

They are the SAME relationship at different granularities. The model is at the component
(SKU) layer, so **use the BOM SKU quantities (10/6/4) for material consumption** and use
`operations` only to identify WHICH node performs the transform and the group mapping.
**Do NOT multiply BOM quantities by the operations 20:1 again** — that would double-count.
Same principle applies to seat → seat_componment. Add a P5 validation check that
battery_componment consumed per battery produced == 20 exactly.

## 2. Operation yield ratios are production constraints, not demand explosion
The P2 BOM explosion (`component_demand.v1.csv`) applies only BOM input quantities to turn
car demand into component gross requirements. Node-level production recipes/yields live in
the MILP production/operation constraints (P5), consuming inputs per BOM at the producing
node. Keep the two separate.

## 3. Long lead times exceed the horizon — rely on initial_flows
Battery-trans lead = 20, seat-trans lead = 23 (> 14-period horizon 61–74). Material for
those long arcs that must arrive within the horizon is already in transit — see
`initial_flows` (dispatch periods 39–60). The MILP must seed in-transit arrivals from
`initial_flows`, or those upstream nodes will look infeasible.

### 3a. Battery service (~48%) — state the driver ACCURATELY (G5 note)
The baseline under-serves battery (~48%) while seat is 100% even though seat's sub-arc
lead (23) is LONGER than battery's (20). So "lead > horizon" alone is NOT the explanation.
The real driver is **consumption ratio × pipeline volume × timing**: battery is 20:1
(1 BEV needs 20 sub-components) and its pre-horizon pipeline (init_inv + in-horizon
`initial_flows` arrivals ≈ 29,240 subs) supports only ~1,873 of 3,003 BEV demanded; seat is
1:1 and its pipeline is adequate. Because both sub-arcs exceed the horizon, neither can be
replenished in-period — so the pipeline you start with is all you get. Report it this way.

## 4. No costs in data — all cost coefficients are ASSUMED (P4)
Objective cost terms (production/transport/holding/shortage/expedite) are assumed, with
basis + units + sensitivity ranges, in `data/assumptions/`. Never present them as observed.

## 5a. Carry-forward checks from P3 (EDA)
- **Battery arc pressure:** the static proxy showed battery-supplier_trans→prod util ≈3.7×
  and battery-supplier_inv→zp7 ≈2.4×. Verify in P5/P6 whether these arcs are genuinely
  binding once lead-time shifting, initial inventory and `initial_flows` are applied; report
  honestly either way (do not assume infeasibility).
- **Criticality weighting:** `risk_score = fan-out × cum_lead_time` sends finished seats
  (Q4H/Q2J, lead 0 at their assembly) to 0 while surfacing the long-lead raw seat
  components. Keep BOTH breadth (fan-out) and lead-time exposure visible in the report
  (the P3 scatter does this); don't rely on the single scalar.

## 5. Make-to-order demand + LOST-SALES shortage (name accurately — G5 note)
Each car config is demanded exactly 1 unit, once (2,000/period). The model uses a
**lost-sales** shortage: per (component, period), `served + short = demand`; unmet demand is
penalised and NOT carried backward to a later period (inventory only carries forward). Call
it "lost-sales shortage", not "backorder", in the report. A true backorder (serve late at a
per-period-late penalty) is a possible extension.

## 5b. P6 scenario carry-forwards for the report (G6 notes)
- **Emergency-response framing:** report it as "battery disruption + a NEW expedite policy", and
  quote the expedite value as supplier_disruption (18.396M) → emergency (16.45M) ≈ **1.945M
  saved / battery +13.6pp**. Do NOT present "cost below baseline" without this framing (baseline
  simply lacks the expedite option).
- **Expedite assumption:** "expedited flow bypasses normal arc capacity, at 3× transport cost
  and lead −1" is a labeled structural ASSUMPTION (params already ASSUMED in cost_params.json);
  state it explicitly in the report.

## 6. Pure LP (not MIP) — justify in the report (G5 note)
The baseline is a **pure LP** (all variables continuous); the optimal solution happens to be
integer-valued here. CLAUDE.md §0 says "(Mixed-Integer) LP" as a general label. For the
report: either justify the LP relaxation (flows/production are large aggregate quantities, so
continuous is appropriate and far faster) or add integrality to flow/production variables if
strict integrality must be guaranteed. Keep `integrality` hooks in milp.py for this.
