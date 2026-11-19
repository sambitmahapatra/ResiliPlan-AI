"""P5 / G5 — Tiny hand-checkable MILP instances (plain runnable script).

Builds minimal synthetic instances whose optimum can be computed by hand, and checks the
solver matches. Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe D:\\SCA\\Project\\tests\\test_tiny_instance.py
Exit 0 == tiny-instance checks pass.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.model.instance import Instance
from src.model.milp import build_and_solve, solution_frames

COSTS = {
    "prod_cost": {"engine": 300, "gear": 150, "battery": 250, "seat": 120,
                  "battery_componment": 15, "seat_componment": 20, "car": 1000},
    "transport_cost_base": 2, "transport_cost_per_lead_period": 1.0,
    "holding_rate_per_period": 0.02, "shortage_penalty_car": 5000,
    "expedite_multiplier": 3.0, "expedite_lead_reduction": 1,
}
failures = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: failures.append(msg)

def tiny(arc_cap):
    """One engine component, chain prod->inv->zp7, zero lead, 2 periods, demand 10 then 5."""
    arcs = [("engine-supplier_prod", "engine-supplier_inv"), ("engine-supplier_inv", "zp7")]
    return Instance(
        scenario_id="tiny", periods=[61, 62], components=["E1"], group_of={"E1": "engine"},
        nodes=["engine-supplier_prod", "engine-supplier_inv", "zp7"], arcs=arcs,
        lead={arcs[0]: 0, arcs[1]: 0}, arc_group={arcs[0]: "engine", arcs[1]: "engine"},
        arc_cap=arc_cap, group_chain_arcs={"engine": arcs},
        source_node={"engine": "engine-supplier_prod"}, transform={},
        comp_demand={("E1", 61): 10.0, ("E1", 62): 5.0}, init_inv={}, init_arrivals={},
        costs=COSTS,
    )

# --- Case 1: ample capacity -> full service, hand-computed objective ---
big = {(i, j, t): 1e6 for (i, j) in [("engine-supplier_prod", "engine-supplier_inv"),
                                     ("engine-supplier_inv", "zp7")] for t in [61, 62]}
sol, _ = build_and_solve(tiny(big))
f = solution_frames(sol, tiny(big))
served = f["served"]["served"].sum() if len(f["served"]) else 0
short = f["short"]["short"].sum() if len(f["short"]) else 0
# Hand calc: produce 15 (cost 300*15=4500); each unit crosses 2 arcs @ base 2 => 4*15=60;
# produce & serve same period => zero holding; zero shortage. Objective = 4560.
check(sol["status"] == 0 and sol["success"], "Case1 solves to optimal")
check(abs(served - 15) < 1e-6, f"Case1 served == 15 (got {served})")
check(abs(short - 0) < 1e-6, f"Case1 shortage == 0 (got {short})")
check(abs(sol["objective"] - 4560) < 1e-6, f"Case1 objective == 4560 (got {sol['objective']})")

# --- Case 2: inv->zp7 capacity 6 in t61 -> shortage 4 in t61 (no backorder) ---
cap2 = dict(big)
cap2[("engine-supplier_inv", "zp7", 61)] = 6
sol2, _ = build_and_solve(tiny(cap2))
f2 = solution_frames(sol2, tiny(cap2))
short2 = f2["short"].set_index(["component", "period"])["short"].to_dict() if len(f2["short"]) else {}
tot_short2 = sum(short2.values())
check(sol2["status"] == 0, "Case2 solves to optimal")
check(abs(tot_short2 - 4) < 1e-6, f"Case2 total shortage == 4 (got {tot_short2})")
check(abs(short2.get(("E1", 61), 0) - 4) < 1e-6, f"Case2 shortage in t61 == 4 (got {short2.get(('E1',61),0)})")

# --- Case 3: battery transform 20:1 applied ONCE (modeling_notes #1) ---
# BEV needs 10+6+4 battery components; demand 1 BEV -> exactly 20 sub-components produced.
barcs = [("battery-supplier_trans", "battery-supplier_prod"),
         ("battery-supplier_prod", "battery-supplier_inv"),
         ("battery-supplier_inv", "zp7")]
binst = Instance(
    scenario_id="tinyB", periods=[61], components=["BEV", "componment_battery1", "componment_battery2", "componment_battery3"],
    group_of={"BEV": "battery", "componment_battery1": "battery_componment",
              "componment_battery2": "battery_componment", "componment_battery3": "battery_componment"},
    nodes=["battery-supplier_trans", "battery-supplier_prod", "battery-supplier_inv", "zp7"],
    arcs=barcs, lead={a: 0 for a in barcs}, arc_group={a: g for a, g in zip(barcs, ["battery_componment", "battery", "battery"])},
    arc_cap={(i, j, 61): 1e6 for (i, j) in barcs},
    group_chain_arcs={"battery": barcs[1:], "battery_componment": [barcs[0]]},
    source_node={"battery": "battery-supplier_prod", "battery_componment": "battery-supplier_trans"},
    transform={"battery": {"at": "battery-supplier_prod",
                           "inputs": {"BEV": {"componment_battery1": 10.0, "componment_battery2": 6.0, "componment_battery3": 4.0}}},
               "seat": {"at": "seat-supplier_prod", "inputs": {}}},
    comp_demand={("BEV", 61): 1.0}, init_inv={}, init_arrivals={}, costs=COSTS,
)
solB, _ = build_and_solve(binst)
fB = solution_frames(binst and solB, binst)
prodB = fB["prod"].set_index(["component", "node"])["qty"].to_dict() if len(fB["prod"]) else {}
servedB = fB["served"]["served"].sum() if len(fB["served"]) else 0
sub_total = sum(v for (c, n), v in prodB.items() if c.startswith("componment_battery"))
check(solB["status"] == 0, "Case3 (battery) solves to optimal")
check(abs(servedB - 1) < 1e-6, f"Case3 served 1 BEV (got {servedB})")
check(abs(sub_total - 20) < 1e-6, f"Case3 sub-components produced == 20 (10+6+4), applied once (got {sub_total})")

print("\n" + "=" * 56)
if failures:
    print(f"TINY-INSTANCE: {len(failures)} FAILURE(S)")
    sys.exit(1)
print("TINY-INSTANCE: ALL CHECKS PASSED")
sys.exit(0)
