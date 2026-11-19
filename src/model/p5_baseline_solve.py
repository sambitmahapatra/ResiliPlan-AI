"""P5 — Solve the baseline, validate it independently, compute KPIs, save figures/tables.

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\src\\model\\p5_baseline_solve.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.utils import paths, save_fig, save_table_image, get_logger
from src.model.instance import build_instance
from src.model.milp import build_and_solve, solution_frames, DIRECT_GROUPS
from src.model.validate import validate_solution

log = get_logger("p5_baseline")
PHASE = "P5"

inst = build_instance("baseline")
sol, V = build_and_solve(inst)
log.info("solver status=%s success=%s obj=%.2f", sol["status"], sol["success"], sol["objective"])
f = solution_frames(sol, inst)
checks = validate_solution(sol, inst)
log.info("validation all_ok=%s max_balance_residual=%.2e max_cap_viol=%.2e",
         checks["all_ok"], checks["max_balance_residual"], checks["max_capacity_violation"])

# --- cost breakdown (recomputed from solution) ---
C = inst.costs; pc = C["prod_cost"]; tb = C["transport_cost_base"]; tpl = C["transport_cost_per_lead_period"]
hr = C["holding_rate_per_period"]; sp = C["shortage_penalty_car"]; g_of = inst.group_of
x = sol["x"]
cost_prod = sum(v * pc[g_of[k[1]]] for k, v in x.items() if k[0] == "prod")
cost_tx = sum(v * (tb + tpl * inst.lead[(k[2], k[3])]) for k, v in x.items() if k[0] == "ship")
cost_hold = sum(v * hr * pc[g_of[k[1]]] for k, v in x.items() if k[0] == "inv")
cost_short = sum(v * sp for k, v in x.items() if k[0] == "short")
recomputed = cost_prod + cost_tx + cost_hold + cost_short

# --- service levels ---
tot_demand = sum(v for (p, t), v in inst.comp_demand.items() if g_of[p] in DIRECT_GROUPS)
tot_short = f["short"]["short"].sum() if len(f["short"]) else 0.0
service = 1 - tot_short / tot_demand if tot_demand else 1.0
# by group
dem_by_g, short_by_g = {}, {}
for (p, t), v in inst.comp_demand.items():
    if g_of[p] in DIRECT_GROUPS:
        dem_by_g[g_of[p]] = dem_by_g.get(g_of[p], 0.0) + v
if len(f["short"]):
    for _, r in f["short"].iterrows():
        gg = g_of[r["component"]]
        short_by_g[gg] = short_by_g.get(gg, 0.0) + r["short"]
svc_rows = []
for gg in sorted(dem_by_g):
    d = dem_by_g[gg]; s = short_by_g.get(gg, 0.0)
    svc_rows.append({"group": gg, "demand": d, "short": s,
                     "service_level_%": round(100 * (1 - s / d), 2) if d else 100.0})
svc_df = pd.DataFrame(svc_rows).set_index("group")

# --- KPI table ---
kpi = pd.DataFrame({"value": [
    "optimal (HiGHS 7)" if sol["status"] == 0 else sol["message"],
    round(sol["objective"], 2), round(recomputed, 2),
    "YES" if abs(recomputed - sol["objective"]) < 1 else "**NO**",
    round(cost_prod, 2), round(cost_tx, 2), round(cost_hold, 2), round(cost_short, 2),
    int(tot_demand), round(tot_short, 2), round(100 * service, 2),
    "YES" if checks["all_ok"] else "**NO**",
    f"{checks['max_balance_residual']:.2e}", f"{checks['max_capacity_violation']:.2e}",
    sol["nvar"], sol["n_eq"], sol["n_ub"],
]}, index=[
    "solver status", "objective (MU)", "objective recomputed", "objective reconciles",
    "cost: production", "cost: transport", "cost: holding", "cost: shortage penalty",
    "direct component demand (units)", "total shortage (units)", "component service level %",
    "independent validation all_ok", "max balance residual", "max capacity violation",
    "variables", "equality constraints", "capacity constraints",
])
kpi.index.name = "metric"
save_table_image(kpi, "p5_baseline_kpis", "P5 — Baseline solve KPIs + independent validation", PHASE, max_rows=20)
save_table_image(svc_df, "p5_service_by_group", "P5 — Baseline component service level by group", PHASE, max_rows=10)

# --- figures ---
# cost breakdown
fig, ax = plt.subplots(figsize=(8, 4.5))
cats = ["production", "transport", "holding", "shortage penalty"]
vals = [cost_prod, cost_tx, cost_hold, cost_short]
ax.bar(cats, vals, color=["#2a6f97", "#468faf", "#61a5c2", "#c1121f"])
ax.set_ylabel("MU"); ax.set_title(f"Baseline cost breakdown (total {sol['objective']:,.0f} MU)")
for i, v in enumerate(vals):
    ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=8)
save_fig(fig, "p5_cost_breakdown", "P5 — Baseline cost breakdown by category", PHASE); plt.close(fig)

# service by group
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(svc_df.index, svc_df["service_level_%"], color="#2a9d8f")
ax.axhline(100, ls="--", color="grey", lw=0.8); ax.set_ylim(min(90, svc_df["service_level_%"].min() - 2), 101)
ax.set_ylabel("service level %"); ax.set_title("Baseline component service level by group")
for i, v in enumerate(svc_df["service_level_%"]):
    ax.text(i, v, f"{v:.1f}%", ha="center", va="bottom", fontsize=8)
save_fig(fig, "p5_service_by_group_fig", "P5 — Baseline service level by group", PHASE); plt.close(fig)

# shortage by period (stacked by group)
if len(f["short"]):
    sh = f["short"].copy(); sh["group"] = sh["component"].map(g_of)
    piv = sh.groupby(["group", "period"])["short"].sum().unstack("period").fillna(0)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bottom = np.zeros(piv.shape[1])
    for gg in piv.index:
        ax.bar(piv.columns, piv.loc[gg], bottom=bottom, label=gg); bottom += piv.loc[gg].values
    ax.set_xlabel("period"); ax.set_ylabel("shortage (units)")
    ax.set_title("Baseline shortage by period and group"); ax.legend(fontsize=8)
    save_fig(fig, "p5_shortage_by_period", "P5 — Baseline shortage by period/group", PHASE); plt.close(fig)

# arc actual utilization heatmap
ship = f["ship"]
util_rows = []
for (i, j) in inst.arcs:
    for t in inst.periods:
        cap = inst.arc_cap.get((i, j, t))
        if cap is None:
            continue
        flow = ship[(ship["i"] == i) & (ship["j"] == j) & (ship["period"] == t)]["qty"].sum() if len(ship) else 0.0
        util_rows.append({"arc": f"{i} -> {j}", "period": t, "util": flow / cap if cap else np.nan})
udf = pd.DataFrame(util_rows); upiv = udf.pivot_table(index="arc", columns="period", values="util")
fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(upiv.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1.0)
ax.set_xticks(range(len(upiv.columns))); ax.set_xticklabels(upiv.columns)
ax.set_yticks(range(len(upiv.index))); ax.set_yticklabels(upiv.index, fontsize=8)
ax.set_title("Baseline ACTUAL arc utilization (optimized flow / capacity)")
for a in range(upiv.shape[0]):
    for b in range(upiv.shape[1]):
        v = upiv.values[a, b]
        if not np.isnan(v):
            ax.text(b, a, f"{v:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if (v > 0.75 or v < 0.15) else "black")
fig.colorbar(im, ax=ax, label="utilization")
save_fig(fig, "p5_arc_utilization_actual",
         "P5 — Baseline actual arc utilization (optimized flow / capacity)", PHASE); plt.close(fig)

# --- persist ---
results = {
    "scenario": "baseline", "status": sol["status"], "success": sol["success"],
    "objective": sol["objective"], "objective_recomputed": recomputed,
    "objective_reconciles": bool(abs(recomputed - sol["objective"]) < 1),
    "cost_breakdown": {"production": cost_prod, "transport": cost_tx, "holding": cost_hold, "shortage": cost_short},
    "total_demand": tot_demand, "total_shortage": tot_short, "service_level": service,
    "service_by_group": svc_df.reset_index().to_dict("records"),
    "validation": {k: (v if not isinstance(v, tuple) else list(v)) for k, v in checks.items()},
    "model_size": {"vars": sol["nvar"], "eq": sol["n_eq"], "ub": sol["n_ub"]},
}
(paths.RESULTS / "p5_baseline.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

print("\n" + "=" * 64)
print("P5 BASELINE SUMMARY")
print("  status            :", "optimal" if sol["status"] == 0 else sol["message"])
print(f"  objective         : {sol['objective']:,.0f} MU  (recomputed {recomputed:,.0f}, reconciles={abs(recomputed-sol['objective'])<1})")
print(f"  cost breakdown    : prod={cost_prod:,.0f} tx={cost_tx:,.0f} hold={cost_hold:,.0f} short={cost_short:,.0f}")
print(f"  service level     : {100*service:.2f}%  (shortage {tot_short:.0f} / demand {tot_demand:.0f})")
print("  service by group  :", {r['group']: r['service_level_%'] for r in svc_rows})
print("  validation all_ok :", checks["all_ok"], "| max balance resid:", f"{checks['max_balance_residual']:.2e}",
      "| max cap viol:", f"{checks['max_capacity_violation']:.2e}")
print("=" * 64)
