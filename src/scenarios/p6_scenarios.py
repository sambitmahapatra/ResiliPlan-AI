"""P6 — Scenario & resilience analysis.

Runs all 6 scenarios, validates each independently, compares against baseline (cost,
service, disruption premium), runs a seeded Monte Carlo on demand uncertainty, and saves
every result as an indexed PNG (+ backing CSV).

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\src\\scenarios\\p6_scenarios.py
"""
from __future__ import annotations
import dataclasses
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

from src.utils import paths, save_fig, save_table_image, get_logger, SEED, set_seeds
from src.model.instance import build_instance
from src.model.milp import build_and_solve, solution_frames, DIRECT_GROUPS
from src.model.validate import validate_solution

log = get_logger("p6_scenarios")
PHASE = "P6"
set_seeds()


def cost_breakdown(sol, inst):
    C = inst.costs; pc = C["prod_cost"]; tb = C["transport_cost_base"]; tpl = C["transport_cost_per_lead_period"]
    hr = C["holding_rate_per_period"]; sp = C["shortage_penalty_car"]
    mult = C["expedite_multiplier"]; red = int(C["expedite_lead_reduction"]); g_of = inst.group_of
    x = sol["x"]
    cp = sum(v * pc[g_of[k[1]]] for k, v in x.items() if k[0] == "prod")
    ct = sum(v * (tb + tpl * inst.lead[(k[2], k[3])]) for k, v in x.items() if k[0] == "ship")
    ce = sum(v * (tb + tpl * max(0, inst.lead[(k[2], k[3])] - red)) * mult for k, v in x.items() if k[0] == "eship")
    ch = sum(v * hr * pc[g_of[k[1]]] for k, v in x.items() if k[0] == "inv")
    cs = sum(v * sp for k, v in x.items() if k[0] == "short")
    return {"production": cp, "transport": ct + ce, "expedite": ce, "holding": ch, "shortage": cs}


def service_metrics(sol, inst):
    g_of = inst.group_of
    dem_by_g, short_by_g = {}, {}
    for (p, t), v in inst.comp_demand.items():
        if g_of[p] in DIRECT_GROUPS:
            dem_by_g[g_of[p]] = dem_by_g.get(g_of[p], 0.0) + v
    for k, v in sol["x"].items():
        if k[0] == "short":
            gg = g_of[k[1]]; short_by_g[gg] = short_by_g.get(gg, 0.0) + v
    tot_d = sum(dem_by_g.values()); tot_s = sum(short_by_g.values())
    by_g = {gg: round(100 * (1 - short_by_g.get(gg, 0.0) / d), 2) if d else 100.0 for gg, d in dem_by_g.items()}
    return {"overall": round(100 * (1 - tot_s / tot_d), 2) if tot_d else 100.0,
            "by_group": by_g, "total_demand": tot_d, "total_shortage": tot_s}


def run_scenario(sid):
    inst = build_instance(sid)
    sol, V = build_and_solve(inst)
    chk = validate_solution(sol, inst)
    cb = cost_breakdown(sol, inst)
    sm = service_metrics(sol, inst)
    f = solution_frames(sol, inst)
    exp_units = f["ship"][f["ship"].get("expedited", False) == True]["qty"].sum() if len(f["ship"]) and "expedited" in f["ship"] else 0.0
    return {"scenario": sid, "name": inst.meta.get("scenario_name"), "status": sol["status"],
            "optimal": sol["status"] == 0, "objective": sol["objective"], "cost": cb,
            "service": sm, "validation_ok": chk["all_ok"],
            "max_resid": chk["max_balance_residual"], "expedite_units": float(exp_units)}


# =========================================================================== #
# 1. Run all scenarios
# =========================================================================== #
scen_ids = json.loads((paths.SCENARIOS / "scenarios_index.json").read_text())["scenarios"]
rows = [run_scenario(s["id"]) for s in scen_ids]
base = next(r for r in rows if r["scenario"] == "baseline")
log.info("ran %d scenarios; all optimal=%s all valid=%s",
         len(rows), all(r["optimal"] for r in rows), all(r["validation_ok"] for r in rows))

# comparison table
comp = []
for r in rows:
    comp.append({
        "scenario": r["scenario"], "status": "optimal" if r["optimal"] else "non-optimal",
        "objective_MU": round(r["objective"], 0),
        "vs_baseline_MU": round(r["objective"] - base["objective"], 0),
        "service_%": r["service"]["overall"],
        "service_vs_base_pp": round(r["service"]["overall"] - base["service"]["overall"], 2),
        "battery_service_%": r["service"]["by_group"].get("battery", 100.0),
        "shortage_units": round(r["service"]["total_shortage"], 0),
        "expedite_units": round(r["expedite_units"], 0),
        "valid": "YES" if r["validation_ok"] else "**NO**",
    })
comp_df = pd.DataFrame(comp).set_index("scenario")
save_table_image(comp_df, "p6_scenario_comparison",
                 "P6 — Scenario comparison vs baseline (cost, service, disruption premium)", PHASE, max_rows=10)

svc_by_g = pd.DataFrame({r["scenario"]: r["service"]["by_group"] for r in rows}).T
save_table_image(svc_by_g, "p6_service_by_group_scenarios",
                 "P6 — Component service level % by group × scenario", PHASE, max_rows=10)

# =========================================================================== #
# 2. Figures
# =========================================================================== #
order = [r["scenario"] for r in rows]
# service level by scenario
fig, ax = plt.subplots(figsize=(10, 5))
svc = [r["service"]["overall"] for r in rows]
colors = ["#2a9d8f" if s == "baseline" else "#e76f51" for s in order]
ax.bar(order, svc, color=colors)
ax.set_ylabel("overall component service %"); ax.set_ylim(min(svc) - 3, 101)
ax.axhline(base["service"]["overall"], ls="--", color="grey", lw=0.8, label="baseline")
ax.set_title("Overall service level by scenario"); ax.legend(fontsize=8)
plt.xticks(rotation=20, ha="right")
for i, s in enumerate(svc):
    ax.text(i, s, f"{s:.1f}%", ha="center", va="bottom", fontsize=8)
save_fig(fig, "p6_service_by_scenario", "P6 — Overall service level by scenario", PHASE); plt.close(fig)

# cost stacked by scenario
fig, ax = plt.subplots(figsize=(10, 5.5))
cats = ["production", "transport", "holding", "shortage"]
palette = {"production": "#2a6f97", "transport": "#468faf", "holding": "#61a5c2", "shortage": "#c1121f"}
bottom = np.zeros(len(rows))
for cat in cats:
    vals = [r["cost"][cat] for r in rows]
    ax.bar(order, vals, bottom=bottom, label=cat, color=palette[cat]); bottom += np.array(vals)
ax.set_ylabel("MU"); ax.set_title("Total cost by scenario (stacked by category)")
ax.legend(fontsize=8); plt.xticks(rotation=20, ha="right")
save_fig(fig, "p6_cost_by_scenario", "P6 — Total cost by scenario (stacked)", PHASE); plt.close(fig)

# battery service by scenario (the resilience focus)
fig, ax = plt.subplots(figsize=(10, 5))
bsvc = [r["service"]["by_group"].get("battery", 100.0) for r in rows]
ax.bar(order, bsvc, color="#6a4c93")
ax.set_ylabel("battery service %"); ax.set_title("Battery service level by scenario (resilience chokepoint)")
plt.xticks(rotation=20, ha="right")
for i, s in enumerate(bsvc):
    ax.text(i, s, f"{s:.1f}%", ha="center", va="bottom", fontsize=8)
save_fig(fig, "p6_battery_service_by_scenario", "P6 — Battery service by scenario", PHASE); plt.close(fig)

# =========================================================================== #
# 3. Monte Carlo — demand uncertainty (seeded)
# =========================================================================== #
import gc
N = 40
rng = np.random.default_rng(SEED)
base_inst = build_instance("baseline")
mc_rows = []
for k in range(N):
    factor = float(np.clip(rng.normal(1.0, 0.1), 0.75, 1.35))
    cd = {key: v * factor for key, v in base_inst.comp_demand.items()}
    inst_k = dataclasses.replace(base_inst, comp_demand=cd, scenario_id=f"mc_{k}")
    sol_k, V_k = build_and_solve(inst_k)
    sm = service_metrics(sol_k, inst_k)
    mc_rows.append({"run": k, "demand_factor": round(factor, 3),
                    "service_%": sm["overall"], "battery_service_%": sm["by_group"].get("battery", 100.0),
                    "objective_MU": round(sol_k["objective"], 0)})
    del sol_k, V_k, inst_k, cd
    if k % 10 == 0:
        gc.collect()
mc = pd.DataFrame(mc_rows)
mc.to_csv(paths.TABLES / "p6_monte_carlo_runs.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].hist(mc["service_%"], bins=15, color="#2a9d8f", edgecolor="white")
axes[0].axvline(mc["service_%"].mean(), ls="--", color="k", label=f"mean {mc['service_%'].mean():.1f}%")
axes[0].set_xlabel("overall service %"); axes[0].set_ylabel("runs"); axes[0].set_title(f"Service distribution ({N} runs)"); axes[0].legend(fontsize=8)
axes[1].scatter(mc["demand_factor"], mc["service_%"], c="#e76f51", alpha=0.7, edgecolors="k", linewidths=0.3)
axes[1].set_xlabel("demand factor"); axes[1].set_ylabel("overall service %"); axes[1].set_title("Service vs demand factor")
fig.suptitle(f"Monte Carlo: demand uncertainty (seed {SEED})")
save_fig(fig, "p6_monte_carlo", f"P6 — Monte Carlo service under demand uncertainty ({N} runs, seed {SEED})", PHASE); plt.close(fig)

mc_summary = pd.DataFrame({"value": [
    N, SEED, round(mc["service_%"].mean(), 2), round(mc["service_%"].std(), 2),
    round(mc["service_%"].min(), 2), round(mc["service_%"].max(), 2),
    round(mc["battery_service_%"].mean(), 2),
    round(mc["objective_MU"].mean(), 0),
]}, index=["runs", "seed", "service mean %", "service std %", "service min %", "service max %",
           "battery service mean %", "objective mean MU"])
mc_summary.index.name = "metric"
save_table_image(mc_summary, "p6_monte_carlo_summary",
                 "P6 — Monte Carlo summary (demand uncertainty)", PHASE, max_rows=12)

# =========================================================================== #
# 4. Persist
# =========================================================================== #
results = {"scenarios": rows, "baseline_objective": base["objective"],
           "all_optimal": all(r["optimal"] for r in rows),
           "all_valid": all(r["validation_ok"] for r in rows),
           "monte_carlo": {"n": N, "seed": SEED, "service_mean": float(mc["service_%"].mean()),
                           "service_min": float(mc["service_%"].min()), "service_max": float(mc["service_%"].max())}}
(paths.RESULTS / "p6_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

print("\n" + "=" * 70)
print("P6 SUMMARY")
print(f"  scenarios run: {len(rows)} | all optimal: {all(r['optimal'] for r in rows)} | all valid: {all(r['validation_ok'] for r in rows)}")
for r in rows:
    print(f"    {r['scenario']:22s} obj={r['objective']:>12,.0f}  service={r['service']['overall']:5.1f}%  "
          f"battery={r['service']['by_group'].get('battery',100):5.1f}%  exp_units={r['expedite_units']:.0f}")
print(f"  Monte Carlo ({N} runs, seed {SEED}): service mean {mc['service_%'].mean():.1f}% "
      f"[{mc['service_%'].min():.1f}, {mc['service_%'].max():.1f}]")
print("=" * 70)
