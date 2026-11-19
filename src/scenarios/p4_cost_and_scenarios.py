"""P4 — Cost & scenario parameterization.

The raw workbook has NO cost data, so every cost coefficient below is an ASSUMPTION with
a stated basis, unit, and sensitivity range. Disruption scenarios are SYNTHETIC stress
tests (clearly labelled), referencing real nodes/arcs in the network.

Outputs
- data/assumptions/cost_assumptions.csv / .md   (documented, labelled ASSUMED)
- data/scenarios/scenario_*.json                (6 configs) + scenarios_index.json
- reports/figures + tables                       cost table, scenario summary (images)
- results/p4_results.json

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\src\\scenarios\\p4_cost_and_scenarios.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
from src.utils import paths, read_clean, save_table_image, get_logger

log = get_logger("p4_cost_scenarios")
PHASE = "P4"

# =========================================================================== #
# 1. COST ASSUMPTIONS  (all ASSUMED — no cost data in the source workbook)
# =========================================================================== #
# Monetary unit = "MU" (dimensionless currency). Values chosen for internally
# consistent relative magnitudes typical of automotive manufacturing cost tiers;
# the DECISIONS depend on relative ratios, not absolute currency. Every row has a
# basis and a sensitivity range for the P6 sensitivity analysis.
GROUPS = ["car", "engine", "gear", "battery", "seat", "battery_componment", "seat_componment"]

cost_rows = [
    # --- production cost per unit produced, by group ---
    ("prod_cost.car", "per unit (group=car)", 1000, "MU/unit",
     "Final assembly is the most cost-intensive step; anchor value.", 700, 1300),
    ("prod_cost.engine", "per unit (group=engine)", 300, "MU/unit",
     "Major powertrain component; ~30% of assembly anchor.", 210, 390),
    ("prod_cost.gear", "per unit (group=gear)", 150, "MU/unit",
     "Mechanical sub-assembly; ~15% of anchor.", 105, 195),
    ("prod_cost.battery", "per unit (group=battery)", 250, "MU/unit",
     "Battery pack assembly from cells; ~25% of anchor.", 175, 325),
    ("prod_cost.seat", "per unit (group=seat)", 120, "MU/unit",
     "Seat assembly from components; ~12% of anchor.", 84, 156),
    ("prod_cost.battery_componment", "per unit", 15, "MU/unit",
     "Raw battery cell/module; low unit cost, high multiplicity (20/pack).", 10, 20),
    ("prod_cost.seat_componment", "per unit", 20, "MU/unit",
     "Raw seat component (frame/foam/trim).", 14, 26),
    # --- transport cost: base + per-period-of-lead-time surcharge ---
    ("transport_cost.base", "per unit shipped on any arc", 2, "MU/unit",
     "Fixed handling/loading cost per unit moved.", 1, 4),
    ("transport_cost.per_lead_period", "per unit per lead-time period of the arc", 1.0, "MU/unit/period",
     "Transport cost scales with transit time/distance (lead time as proxy).", 0.5, 2.0),
    # --- inventory holding ---
    ("holding_cost.rate_per_period", "fraction of item production cost, per period", 0.02,
     "fraction/period", "~2%/period carrying cost (≈ 25-30%/yr typical automotive).", 0.01, 0.04),
    # --- shortage / backorder penalty (service priority) ---
    ("shortage_penalty.car", "per unfulfilled car per period late", 5000, "MU/car/period",
     "Set ABOVE full fulfilment cost so the optimiser prefers to serve demand; proxy for "
     "lost-sale + contractual penalty. Dominant term enforcing service.", 3000, 10000),
    # --- expediting premium (only when a scenario enables it) ---
    ("expedite_multiplier", "multiplier on transport cost for expedited flow", 3.0, "x",
     "Premium (air/priority freight) relative to standard transport.", 2.0, 5.0),
    # --- lead-time reduction from expediting ---
    ("expedite_lead_reduction", "periods removed from an arc's lead time when expedited", 1, "periods",
     "Expedited shipments arrive faster by ~1 period (bounded at >=0).", 1, 2),
]
cost_df = pd.DataFrame(cost_rows, columns=["parameter", "scope", "value", "unit", "basis",
                                           "sensitivity_low", "sensitivity_high"])
cost_df.insert(0, "status", "ASSUMED")
paths.ASSUMPTIONS.mkdir(parents=True, exist_ok=True)
cost_df.to_csv(paths.ASSUMPTIONS / "cost_assumptions.csv", index=False)

# machine-usable structured form for the MILP
cost_params = {
    "monetary_unit": "MU (dimensionless; decisions depend on relative ratios)",
    "status": "ALL ASSUMED — source workbook contains no cost data",
    "prod_cost": {g: cost_df.loc[cost_df["parameter"] == f"prod_cost.{g}", "value"].iloc[0]
                  for g in GROUPS},
    "transport_cost_base": 2, "transport_cost_per_lead_period": 1.0,
    "holding_rate_per_period": 0.02, "shortage_penalty_car": 5000,
    "expedite_multiplier": 3.0, "expedite_lead_reduction": 1,
}
(paths.ASSUMPTIONS / "cost_params.json").write_text(json.dumps(cost_params, indent=2), encoding="utf-8")

# markdown writeup
md = ["# Cost & Parameter Assumptions — ResiliPlan AI\n",
      "> **The source workbook contains NO cost data.** Every parameter below is an "
      "**ASSUMPTION**, chosen for internally consistent relative magnitudes (not real prices). "
      "Optimisation decisions depend on the *ratios* between these costs. Each has a stated "
      "basis and a sensitivity range used in P6.\n",
      "Monetary unit: **MU** (dimensionless currency).\n",
      "| status | parameter | scope | value | unit | basis | sens. low | sens. high |",
      "|---|---|---|---:|---|---|---:|---:|"]
for _, r in cost_df.iterrows():
    md.append(f"| {r['status']} | `{r['parameter']}` | {r['scope']} | {r['value']} | {r['unit']} "
              f"| {r['basis']} | {r['sensitivity_low']} | {r['sensitivity_high']} |")
md.append("\n## How these enter the MILP objective\n")
md.append("minimise  Z = production + transport + holding + shortage(+expedite)\n"
          "- production: Σ prod_cost[group(p)] · produced(p,node,t)\n"
          "- transport: Σ (transport_base + transport_per_lead·lead(i,j)) · shipped(i,j,p,t)\n"
          "- holding:   Σ holding_rate · prod_cost[group(p)] · end_inventory(p,node,t)\n"
          "- shortage:  Σ shortage_penalty_car · backorder(car,t)\n"
          "- expedite:  Σ (expedite_multiplier−1)·transport · expedited(i,j,p,t)   (scenarios only)\n")
(paths.ASSUMPTIONS / "cost_assumptions.md").write_text("\n".join(md) + "\n", encoding="utf-8")

save_table_image(cost_df.set_index("parameter"), "p4_cost_assumptions",
                 "P4 — Assumed cost parameters (ALL ASSUMED; basis + sensitivity ranges)",
                 PHASE, max_rows=20)
log.info("Wrote cost assumptions (%d params)", len(cost_df))

# =========================================================================== #
# 2. DISRUPTION SCENARIOS  (SYNTHETIC stress tests — clearly labelled)
# =========================================================================== #
# Validate node/arc references against the cleaned network.
arcs = read_clean("arcs")
arc_set = set(zip(arcs["starting_node_i"].astype(str), arcs["ending_node_j"].astype(str)))
node_set = set(read_clean("nodes")["node_n"].astype(str))

def arc(i, j):
    assert (i, j) in arc_set, f"arc {i}->{j} not in network"
    return [i, j]

scenarios = [
    {
        "id": "baseline",
        "name": "Baseline",
        "nature": "reference (no disruption)",
        "managerial_question": "What is the least-cost feasible plan under nominal conditions?",
        "modifications": {},
    },
    {
        "id": "supplier_disruption",
        "name": "Battery supplier capacity reduction",
        "nature": "SYNTHETIC stress test",
        "managerial_question": "A battery supplier loses capacity for several periods — which "
                               "downstream vehicles are affected and how should production adapt?",
        "modifications": {
            "arc_capacity_multiplier": [
                {"arc": arc("battery-supplier_prod", "battery-supplier_inv"),
                 "factor": 0.5, "periods": [64, 65, 66, 67]}
            ]
        },
    },
    {
        "id": "material_delay",
        "name": "Gear inbound lead-time increase",
        "nature": "SYNTHETIC stress test",
        "managerial_question": "Gear deliveries are delayed — what inventory/shipment "
                               "adjustments mitigate late arrivals?",
        "modifications": {
            "arc_lead_time_delta": [
                {"arc": arc("gear-supplier_inv", "zp7"), "delta_periods": 3,
                 "periods": "all"}
            ]
        },
    },
    {
        "id": "demand_surge",
        "name": "Demand surge (mid-horizon)",
        "nature": "SYNTHETIC stress test",
        "managerial_question": "Demand spikes for a block of periods — which orders can still "
                               "be fulfilled and at what cost?",
        "modifications": {
            "car_demand_multiplier": [
                {"periods": [66, 67, 68], "factor": 1.3}
            ]
        },
    },
    {
        "id": "transport_constraint",
        "name": "Engine inbound arc capacity cut",
        "nature": "SYNTHETIC stress test",
        "managerial_question": "A key inbound transport link is constrained — which material "
                               "flows should be reprioritised?",
        "modifications": {
            "arc_capacity_multiplier": [
                {"arc": arc("engine-supplier_inv", "zp7"), "factor": 0.6, "periods": "all"}
            ]
        },
    },
    {
        "id": "emergency_response",
        "name": "Battery disruption + expedited recovery",
        "nature": "SYNTHETIC stress test (policy option on top of supplier disruption)",
        "managerial_question": "Given the battery disruption, is the premium cost of expedited "
                               "flow justified by the service improvement?",
        "modifications": {
            "arc_capacity_multiplier": [
                {"arc": arc("battery-supplier_prod", "battery-supplier_inv"),
                 "factor": 0.5, "periods": [64, 65, 66, 67]}
            ],
            "enable_expedite": True,
        },
    },
]

paths.SCENARIOS.mkdir(parents=True, exist_ok=True)
for sc in scenarios:
    sc["disclaimer"] = ("Disruption inputs are SYNTHETIC assumptions for stress testing, not "
                        "observed historical events.")
    (paths.SCENARIOS / f"scenario_{sc['id']}.json").write_text(json.dumps(sc, indent=2), encoding="utf-8")
index = {"scenarios": [{"id": s["id"], "name": s["name"], "nature": s["nature"]} for s in scenarios],
         "count": len(scenarios)}
(paths.SCENARIOS / "scenarios_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

scen_tbl = pd.DataFrame([{
    "id": s["id"], "name": s["name"], "nature": s["nature"],
    "modifications": ", ".join(s["modifications"].keys()) or "(none)",
    "managerial_question": s["managerial_question"],
} for s in scenarios]).set_index("id")
save_table_image(scen_tbl[["name", "nature", "modifications"]], "p4_scenarios_summary",
                 "P4 — Disruption scenarios (all SYNTHETIC stress tests)", PHASE, max_rows=10)

results = {"n_cost_params": len(cost_df), "n_scenarios": len(scenarios),
           "scenario_ids": [s["id"] for s in scenarios],
           "all_arc_refs_valid": True}
(paths.RESULTS / "p4_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

print("\n" + "=" * 64)
print("P4 SUMMARY")
print("  cost parameters (ASSUMED):", len(cost_df))
print("  scenarios written        :", len(scenarios), "->", [s["id"] for s in scenarios])
print("  all arc/node refs valid  : True (validated against clean network)")
print("=" * 64)
