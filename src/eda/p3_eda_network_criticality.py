"""P3 — EDA: network map, component criticality (BOM fan-out), and exposure analysis.

Outputs (all PNG + indexed; tables also as CSV)
- p3_network_map              echelon network diagram with lead times
- p3_arc_lead_times           lead time per arc
- p3_component_criticality_top  top-N components by fan-out (how many car configs need them)
- p3_criticality_ranking      full 49-component ranking table
- p3_criticality_vs_leadtime  risk scatter (fan-out x cumulative lead time, bubble=demand)
- p3_arc_utilization_heatmap  arc x period utilization vs capacity
- p3_arc_utilization_summary  per-arc max/mean utilization + over-capacity periods
- results/p3_results.json

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\src\\eda\\p3_eda_network_criticality.py
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

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from src.utils import paths, read_clean, save_table_image, save_fig, get_logger

log = get_logger("p3_eda")
PHASE = "P3"
results: dict = {}

# --------------------------------------------------------------------------- #
# Load cleaned tables
# --------------------------------------------------------------------------- #
nodes = read_clean("nodes")["node_n"].astype(str).tolist()
arcs = read_clean("arcs")
for c in ["starting_node_i", "ending_node_j", "group_g"]:
    arcs[c] = arcs[c].astype(str)
arcs["process_lead_time_l_ij"] = pd.to_numeric(arcs["process_lead_time_l_ij"])
ninf = read_clean("nodes_inflow"); ninf["product_p"] = ninf["product_p"].astype(str); ninf["node_n"] = ninf["node_n"].astype(str)
req = read_clean("component_requirements")  # car, component, group, qty_per_car
req["component"] = req["component"].astype(str); req["group"] = req["group"].astype(str)
cd = read_clean("component_demand")  # component, group, period, required_qty
cd["component"] = cd["component"].astype(str); cd["group"] = cd["group"].astype(str)
cap = read_clean("capacity_at_arc")
for c in ["starting_node_i", "ending_node_j"]:
    cap[c] = cap[c].astype(str)
cap["period_t"] = pd.to_numeric(cap["period_t"]); cap["capacity_c_ijt"] = pd.to_numeric(cap["capacity_c_ijt"])

# --------------------------------------------------------------------------- #
# 1. Network graph + echelon map
# --------------------------------------------------------------------------- #
G = nx.DiGraph()
for _, r in arcs.iterrows():
    G.add_edge(r["starting_node_i"], r["ending_node_j"], lead=float(r["process_lead_time_l_ij"]),
               group=r["group_g"])

# echelon level = hops to zp8
level = {n: (nx.shortest_path_length(G, n, "zp8") if nx.has_path(G, n, "zp8") else 99) for n in nodes}
maxlvl = max(level.values())
# position: x by (maxlvl - level) so upstream on the left; y spread by family
fam_order = {}
def fam(n):
    return n.split("-")[0] if "-" in n else n
families = sorted(set(fam(n) for n in nodes))
ypos = {f: i for i, f in enumerate(families)}
pos = {}
for n in nodes:
    x = maxlvl - level[n]
    pos[n] = (x, ypos[fam(n)] + (0.0 if "-" not in n else 0.0))
# nudge zp7/zp8 to their own lane
pos["zp8"] = (maxlvl, len(families) / 2 + 0.6)
pos["zp7"] = (maxlvl - 1, len(families) / 2 + 0.6)

fig, ax = plt.subplots(figsize=(12, 7))
nx.draw_networkx_nodes(G, pos, node_size=1500, node_color="#cfe3f2", edgecolors="#1f2d3d", ax=ax)
nx.draw_networkx_labels(G, pos, font_size=7.5, ax=ax)
nx.draw_networkx_edges(G, pos, arrowstyle="-|>", arrowsize=16, edge_color="#5a6b7b",
                       node_size=1500, min_source_margin=18, min_target_margin=18, ax=ax)
elabels = {(u, v): f"L={int(d['lead'])}" for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=elabels, font_size=7, ax=ax,
                             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
ax.set_title("ResiliPlan network: 12 nodes, 11 arcs (L = transport lead time, periods)")
ax.axis("off")
save_fig(fig, "p3_network_map", "P3 — Multi-echelon network map with lead times", PHASE); plt.close(fig)

# arc lead-time bar
arcs_lbl = arcs.assign(arc=arcs["starting_node_i"] + " -> " + arcs["ending_node_j"]).sort_values("process_lead_time_l_ij")
fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#c1121f" if v > 14 else "#2a6f97" for v in arcs_lbl["process_lead_time_l_ij"]]
ax.barh(arcs_lbl["arc"], arcs_lbl["process_lead_time_l_ij"], color=colors)
ax.axvline(14, ls="--", color="#c1121f", lw=1); ax.text(14.2, 0.2, "horizon = 14", color="#c1121f", fontsize=8)
ax.set_xlabel("lead time (periods)"); ax.set_title("Arc lead times (red = exceeds planning horizon)")
for i, v in enumerate(arcs_lbl["process_lead_time_l_ij"]):
    ax.text(v, i, f" {int(v)}", va="center", fontsize=8)
save_fig(fig, "p3_arc_lead_times", "P3 — Transport lead time by arc", PHASE); plt.close(fig)

# --------------------------------------------------------------------------- #
# 2. Component criticality (BOM fan-out)
# --------------------------------------------------------------------------- #
# origin node per component
origin = {}
inflow_map = dict(zip(ninf["product_p"], ninf["node_n"]))
for comp, grp in req[["component", "group"]].drop_duplicates().itertuples(index=False):
    if comp in inflow_map:
        origin[comp] = inflow_map[comp]
    else:
        origin[comp] = f"{grp}-supplier_prod"   # intermediates (battery, seat)

def cum_lead(node):
    if node == "zp8":
        return 0.0
    if not nx.has_path(G, node, "zp8"):
        return np.nan
    path = nx.shortest_path(G, node, "zp8")
    return float(sum(G[path[i]][path[i + 1]]["lead"] for i in range(len(path) - 1)))

crit = (req.groupby(["component", "group"])
          .agg(n_cars_using=("car", "nunique"), qty_per_car_mean=("qty_per_car", "mean"))
          .reset_index())
gross = cd.groupby("component")["required_qty"].sum().rename("gross_demand_total")
crit = crit.merge(gross, on="component", how="left")
crit["origin_node"] = crit["component"].map(origin)
crit["cum_lead_time"] = crit["origin_node"].map(cum_lead)
n_cars_total = req["car"].nunique()
crit["pct_configs_dependent"] = (100 * crit["n_cars_using"] / n_cars_total).round(2)
# risk score: breadth (configs dependent) x supply lead-time exposure, scaled
crit["risk_score"] = (crit["n_cars_using"] * crit["cum_lead_time"]).round(0)
crit = crit.sort_values(["n_cars_using", "gross_demand_total"], ascending=False).reset_index(drop=True)
crit.to_csv(paths.CLEAN / "component_criticality.v1.csv", index=False)

rank_tbl = crit[["component", "group", "origin_node", "n_cars_using", "pct_configs_dependent",
                 "gross_demand_total", "cum_lead_time", "risk_score"]].set_index("component")
save_table_image(rank_tbl, "p3_criticality_ranking",
                 "P3 — Component criticality ranking (fan-out, demand, lead-time exposure)",
                 PHASE, max_rows=49)

topN = crit.head(15)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(topN["component"][::-1], topN["n_cars_using"][::-1],
               color=[plt.cm.viridis(x) for x in np.linspace(0.15, 0.9, len(topN))])
ax.set_xlabel("number of car configurations that require this component (fan-out)")
ax.set_title("Top 15 critical components by BOM fan-out")
for i, (_, r) in enumerate(topN[::-1].iterrows()):
    ax.text(r["n_cars_using"], i, f"  {int(r['n_cars_using'])} ({r['pct_configs_dependent']}%)",
            va="center", fontsize=8)
save_fig(fig, "p3_component_criticality_top", "P3 — Top-15 components by BOM fan-out", PHASE); plt.close(fig)

# risk scatter: fan-out vs cumulative lead time, bubble = gross demand
fig, ax = plt.subplots(figsize=(10, 6))
cl = crit.dropna(subset=["cum_lead_time"])
sizes = 20 + 400 * (cl["gross_demand_total"] / cl["gross_demand_total"].max())
groups = cl["group"].unique()
cmap = {g: plt.cm.tab10(i) for i, g in enumerate(groups)}
for g in groups:
    sub = cl[cl["group"] == g]
    ax.scatter(sub["cum_lead_time"], sub["n_cars_using"],
               s=20 + 400 * (sub["gross_demand_total"] / cl["gross_demand_total"].max()),
               alpha=0.6, label=g, color=cmap[g], edgecolors="k", linewidths=0.4)
ax.axvline(14, ls="--", color="#c1121f", lw=1); ax.text(14.2, ax.get_ylim()[1]*0.9, "horizon", color="#c1121f", fontsize=8)
ax.set_xlabel("cumulative supply lead time to zp8 (periods)")
ax.set_ylabel("car configurations dependent (fan-out)")
ax.set_title("Component risk: fan-out vs lead-time exposure (bubble = gross demand)")
ax.legend(fontsize=8, title="group")
save_fig(fig, "p3_criticality_vs_leadtime",
         "P3 — Criticality vs lead-time risk quadrant", PHASE); plt.close(fig)

results["criticality"] = {
    "n_components": int(len(crit)),
    "top5_by_fanout": crit.head(5)[["component", "group", "n_cars_using", "pct_configs_dependent"]].to_dict("records"),
    "highest_lead_time": crit.sort_values("cum_lead_time", ascending=False).head(3)[["component", "group", "cum_lead_time"]].to_dict("records"),
    "top5_by_risk": crit.sort_values("risk_score", ascending=False).head(5)[["component", "group", "risk_score"]].to_dict("records"),
}

# --------------------------------------------------------------------------- #
# 3. Arc utilization vs capacity (demand routed by group; each arc carries one group)
# --------------------------------------------------------------------------- #
group_demand = cd.groupby(["group", "period"])["required_qty"].sum().reset_index()
# car demand per period on zp7->zp8 (= number of cars; not in component_demand since car is parent)
dem = read_clean("demands"); dem["period_t"] = pd.to_numeric(dem["period_t"])
car_dem = dem.groupby("period_t")["demand_d_npt"].apply(lambda s: pd.to_numeric(s).sum()).reset_index()
car_dem.columns = ["period", "required_qty"]; car_dem["group"] = "car"
group_demand = pd.concat([group_demand, car_dem[["group", "period", "required_qty"]]], ignore_index=True)

util_rows = []
for _, a in arcs.iterrows():
    g = a["group_g"]
    arc_name = f"{a['starting_node_i']} -> {a['ending_node_j']}"
    acap = cap[(cap["starting_node_i"] == a["starting_node_i"]) & (cap["ending_node_j"] == a["ending_node_j"])]
    for _, cr in acap.iterrows():
        t = int(cr["period_t"]); capacity = float(cr["capacity_c_ijt"])
        d = group_demand[(group_demand["group"] == g) & (group_demand["period"] == t)]["required_qty"].sum()
        util_rows.append({"arc": arc_name, "group": g, "period": t,
                          "demand": d, "capacity": capacity,
                          "utilization": (d / capacity) if capacity else np.nan})
util = pd.DataFrame(util_rows)

# heatmap arc x period
pivot = util.pivot_table(index="arc", columns="period", values="utilization", aggfunc="mean")
fig, ax = plt.subplots(figsize=(12, 6))
im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1.2)
ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns)
ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=8)
ax.set_xlabel("period"); ax.set_title("Arc utilization (demand / capacity); >1.0 = over capacity")
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        v = pivot.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if (v > 0.8 or v < 0.2) else "black")
fig.colorbar(im, ax=ax, label="utilization")
save_fig(fig, "p3_arc_utilization_heatmap",
         "P3 — Arc utilization heatmap (static same-period demand/capacity proxy; "
         "lead-time shifting, inventory and initial in-transit flows are applied only in the "
         "P5 MILP, which may resolve apparent >1.0 pressure)", PHASE); plt.close(fig)

usum = (util.groupby(["arc", "group"])
            .agg(mean_util=("utilization", "mean"), max_util=("utilization", "max"),
                 periods_over_capacity=("utilization", lambda s: int((s > 1.0).sum())))
            .reset_index().sort_values("max_util", ascending=False).set_index("arc"))
usum[["mean_util", "max_util"]] = usum[["mean_util", "max_util"]].round(3)
save_table_image(usum, "p3_arc_utilization_summary",
                 "P3 — Arc utilization summary (static same-period proxy; mean/max, periods "
                 "over capacity). Pressure indicator only — resolved in the P5 MILP.", PHASE, max_rows=20)
results["utilization"] = {
    "bottleneck_arcs": usum[usum["max_util"] > 1.0].reset_index()[["arc", "group", "max_util", "periods_over_capacity"]].to_dict("records"),
    "max_util_arc": {"arc": usum.index[0], "max_util": float(usum["max_util"].iloc[0])},
}

(paths.RESULTS / "p3_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

print("\n" + "=" * 64)
print("P3 SUMMARY")
print("  top components by fan-out:")
for r in results["criticality"]["top5_by_fanout"]:
    print(f"    {r['component']:>20} ({r['group']}): {r['n_cars_using']} configs ({r['pct_configs_dependent']}%)")
print("  highest lead-time components:", [f"{r['component']}({r['cum_lead_time']:.0f})" for r in results["criticality"]["highest_lead_time"]])
print("  bottleneck arcs (max_util>1):", results["utilization"]["bottleneck_arcs"] or "none")
print("  busiest arc:", results["utilization"]["max_util_arc"])
print("=" * 64)
