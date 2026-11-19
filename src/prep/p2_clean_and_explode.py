"""P2 — Cleaning, relational model, and the core BOM explosion.

Outputs
-------
- data/clean/<sheet>.v1.csv            cleaned, canonical-ID, typed tables (12)
- data/clean/bom_real.v1.csv           BOM with the 49 identity rows removed
- data/clean/component_requirements.v1.csv   per-car full descendant requirements (long)
- data/clean/component_demand.v1.csv   component gross requirement per period (the transform)
- reports/figures + tables             manifest, connectivity, demand summary, reconciliation
- results/p2_results.json              machine-readable summary for the Validator

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\src\\prep\\p2_clean_and_explode.py
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
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

from src.utils import paths, read_all_raw, save_table_image, save_fig, get_logger

log = get_logger("p2_clean_and_explode")
PHASE = "P2"
results: dict = {}

# --------------------------------------------------------------------------- #
# 0. Load + canonicalise (same rules as P1)
# --------------------------------------------------------------------------- #
ID_COLS = {"product_p", "mother", "child", "node_n", "starting_node_i",
           "ending_node_j", "group_g", "input_product_group_x", "output_product_group_y"}
PERIOD_COLS = {"period_t"}

def _cid(x):
    try:
        f = float(x)
        if f.is_integer():
            return str(int(f))
    except (TypeError, ValueError):
        pass
    return str(x).strip()

S = read_all_raw()
for name, df in S.items():
    for c in df.columns:
        if c in ID_COLS:
            df[c] = df[c].map(_cid)
        elif c in PERIOD_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
log.info("Loaded + canonicalised %d sheets", len(S))

# --------------------------------------------------------------------------- #
# 1. Write cleaned, versioned CSVs (raw workbook stays untouched)
# --------------------------------------------------------------------------- #
manifest = []
for name, df in S.items():
    out = paths.CLEAN / f"{name}.v1.csv"
    df.to_csv(out, index=False)
    manifest.append({"sheet": name, "clean_file": out.name, "rows": len(df), "cols": df.shape[1]})

bom = S["BOM"]
bom_real = bom[bom["mother"] != bom["child"]].copy()
bom_real.to_csv(paths.CLEAN / "bom_real.v1.csv", index=False)
manifest.append({"sheet": "bom_real (derived)", "clean_file": "bom_real.v1.csv",
                 "rows": len(bom_real), "cols": bom_real.shape[1]})
man_df = pd.DataFrame(manifest).set_index("sheet")
save_table_image(man_df, "p2_clean_manifest", "P2 — Cleaned table manifest (data/clean/)", PHASE, max_rows=20)
log.info("Wrote %d cleaned CSVs + bom_real", len(S))

# --------------------------------------------------------------------------- #
# 2. Connectivity / relational-model proof
# --------------------------------------------------------------------------- #
nodes = S["nodes"]["node_n"].tolist()
arcs = S["arcs"]
Gnet = nx.DiGraph()
Gnet.add_nodes_from(nodes)
Gnet.add_edges_from(zip(arcs["starting_node_i"], arcs["ending_node_j"]))
undirected = Gnet.to_undirected()
weakly_connected = nx.is_connected(undirected)
# reachability to the demand node zp8
rev = Gnet.reverse()
can_reach_zp8 = set(nx.descendants(rev, "zp8")) | {"zp8"}
unreached = sorted(set(nodes) - can_reach_zp8)
# echelon level = shortest path length to zp8 (0 at zp8)
level = {}
for n in nodes:
    try:
        level[n] = nx.shortest_path_length(Gnet, n, "zp8")
    except Exception:
        level[n] = None

conn_df = pd.DataFrame({
    "value": [len(nodes), Gnet.number_of_edges(), weakly_connected,
              len(can_reach_zp8), ", ".join(unreached) if unreached else "none",
              max(v for v in level.values() if v is not None)]},
    index=["nodes", "arcs", "weakly connected", "nodes that can reach zp8",
           "nodes that CANNOT reach zp8", "max echelon depth to zp8"])
conn_df.index.name = "metric"
save_table_image(conn_df, "p2_connectivity", "P2 — Network connectivity proof", PHASE, max_rows=20)

node_level_df = pd.DataFrame(
    [{"node": n, "echelon_level_to_zp8": level[n],
      "out_arcs": Gnet.out_degree(n), "in_arcs": Gnet.in_degree(n)} for n in nodes]
).sort_values("echelon_level_to_zp8", na_position="last").set_index("node")
save_table_image(node_level_df, "p2_node_echelons",
                 "P2 — Nodes by echelon level (hops to demand node zp8)", PHASE, max_rows=20)
results["connectivity"] = {"weakly_connected": bool(weakly_connected),
                           "unreached_to_zp8": unreached}
log.info("Network weakly_connected=%s unreached_to_zp8=%s", weakly_connected, unreached or "none")

# --------------------------------------------------------------------------- #
# 3. BOM EXPLOSION (the core transform)
#    Gross-requirement propagation over the real-edge DAG (MRP style).
#    R(node)[descendant] = sum over paths of product of edge quantities.
#    NOTE: operation yield ratios (e.g. battery 20:1) are production recipes applied
#    in the MILP (P5), NOT in this demand explosion — this is documented.
# --------------------------------------------------------------------------- #
children_of = defaultdict(list)  # parent -> [(child, qty)]
for m, c, q in zip(bom_real["mother"], bom_real["child"],
                   pd.to_numeric(bom_real["individual_input_quantity_q_mc"], errors="coerce")):
    children_of[m].append((c, float(q)))

prod = S["products"]
group_of = dict(zip(prod["product_p"], prod["group_g"]))

_memo: dict[str, dict] = {}
def requirements(node: str) -> dict:
    """Full descendant gross-requirement dict for one unit of `node`."""
    if node in _memo:
        return _memo[node]
    req: dict[str, float] = defaultdict(float)
    for child, q in children_of.get(node, []):
        req[child] += q
        for desc, qd in requirements(child).items():
            req[desc] += q * qd
    _memo[node] = dict(req)
    return _memo[node]

dem = S["demands"].copy()
dem["period_t"] = dem["period_t"].astype(int)
dem["demand_d_npt"] = pd.to_numeric(dem["demand_d_npt"], errors="coerce").fillna(0.0)

# per-car requirement (long) — for the record + explainability
car_ids = dem["product_p"].unique().tolist()
req_rows = []
cars_with_empty_bom = 0
for car in car_ids:
    r = requirements(car)
    if not r:
        cars_with_empty_bom += 1
    for comp, q in r.items():
        req_rows.append({"car": car, "component": comp, "group": group_of.get(comp, "?"), "qty_per_car": q})
req_df = pd.DataFrame(req_rows)
req_df.to_csv(paths.CLEAN / "component_requirements.v1.csv", index=False)

# component gross requirement per period
comp_demand = defaultdict(float)  # (component, period) -> qty
for car, t, d in zip(dem["product_p"], dem["period_t"], dem["demand_d_npt"]):
    if d == 0:
        continue
    for comp, q in requirements(car).items():
        comp_demand[(comp, int(t))] += q * d
cd_df = pd.DataFrame(
    [{"component": c, "group": group_of.get(c, "?"), "period": t, "required_qty": q}
     for (c, t), q in comp_demand.items()]
).sort_values(["group", "component", "period"]).reset_index(drop=True)
cd_df.to_csv(paths.CLEAN / "component_demand.v1.csv", index=False)
log.info("Exploded to %d (component,period) requirement rows across %d components",
         len(cd_df), cd_df["component"].nunique())

# group x period pivot (summary table + figure)
pivot = cd_df.groupby(["group", "period"])["required_qty"].sum().unstack("period").fillna(0)
save_table_image(pivot.astype(int), "p2_component_demand_by_group",
                 "P2 — Exploded component demand by group × period (gross requirements)",
                 PHASE, max_rows=20)

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 5))
periods = sorted(cd_df["period"].unique())
bottom = np.zeros(len(periods))
for g in pivot.index:
    vals = [pivot.loc[g, p] if p in pivot.columns else 0 for p in periods]
    ax.bar(periods, vals, bottom=bottom, label=g)
    bottom += np.array(vals)
ax.set_xlabel("period"); ax.set_ylabel("gross component requirement (units)")
ax.set_title("Exploded component demand per period, stacked by group")
ax.legend(ncol=4, fontsize=8)
save_fig(fig, "p2_component_demand_per_period",
         "P2 — Exploded component demand per period (stacked by group)", PHASE); plt.close(fig)

# --------------------------------------------------------------------------- #
# 4. Reconciliation of the explosion back to raw car demand
# --------------------------------------------------------------------------- #
cars_per_period = dem.groupby("period_t")["product_p"].nunique()
# independent total: sum over demand rows of (sum of that car's requirement vector)
indep_total = sum(sum(requirements(car).values()) * d
                  for car, d in zip(dem["product_p"], dem["demand_d_npt"]))
explosion_total = cd_df["required_qty"].sum()
# per-period totals match?
per_period_expl = cd_df.groupby("period")["required_qty"].sum()
per_period_indep = defaultdict(float)
for car, t, d in zip(dem["product_p"], dem["period_t"], dem["demand_d_npt"]):
    per_period_indep[int(t)] += sum(requirements(car).values()) * d
per_period_match = all(abs(per_period_expl.get(t, 0) - per_period_indep[t]) < 1e-6
                       for t in per_period_indep)

recon = pd.DataFrame({"value": [
    int(cars_per_period.min()), int(cars_per_period.max()),
    int(dem["product_p"].nunique()), cars_with_empty_bom,
    round(explosion_total, 2), round(indep_total, 2),
    "YES" if abs(explosion_total - indep_total) < 1e-6 else "**NO**",
    "YES" if per_period_match else "**NO**",
    round(float(req_df["qty_per_car"].groupby(req_df["car"]).sum().mean()), 3),
]}, index=[
    "cars demanded / period (min)", "cars demanded / period (max)",
    "distinct cars demanded", "cars with EMPTY BOM (should be 0)",
    "total exploded component-units", "independent total (cross-check)",
    "explosion total == independent total", "per-period totals match",
    "mean component-units per car",
])
recon.index.name = "metric"
save_table_image(recon, "p2_explosion_reconciliation",
                 "P2 — BOM explosion reconciliation vs raw car demand", PHASE, max_rows=20)
results["explosion"] = {
    "cars_with_empty_bom": int(cars_with_empty_bom),
    "explosion_total": float(explosion_total),
    "independent_total": float(indep_total),
    "totals_match": bool(abs(explosion_total - indep_total) < 1e-6),
    "per_period_match": bool(per_period_match),
    "n_component_period_rows": int(len(cd_df)),
}

(paths.RESULTS / "p2_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

print("\n" + "=" * 64)
print("P2 SUMMARY")
print("  cleaned CSVs written  :", len(S), "(+ bom_real, component_requirements, component_demand)")
print("  network connected     :", weakly_connected, "| unreached->zp8:", unreached or "none")
print("  cars w/ empty BOM     :", cars_with_empty_bom, "(expect 0)")
print("  explosion total==indep:", abs(explosion_total - indep_total) < 1e-6,
      f"({explosion_total:.0f})")
print("  per-period totals match:", per_period_match)
print("  component_demand rows :", len(cd_df))
print("=" * 64)
