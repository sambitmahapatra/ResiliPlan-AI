"""P1 — Data Audit for ResiliPlan AI.

Reproduces the Section-4 counts, runs integrity + referential-integrity checks,
analyses BOM structure (cycles, closure, depth), and saves every summary as an
indexed PNG table. Also emits machine-readable JSON under results/ for the Validator.

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\src\\audit\\p1_data_audit.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:  # make console tolerant of unicode (∈, →) on Windows cp1252
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
import networkx as nx

from src.utils import paths, read_all_raw, save_table_image, save_fig, get_logger

log = get_logger("p1_data_audit")
PHASE = "P1"

# ----------------------------------------------------------------------------- #
# Load all raw sheets (read-only workbook)
# ----------------------------------------------------------------------------- #
log.info("Reading raw workbook: %s", paths.RAW_XLSB)
S = read_all_raw()

# Canonicalise ALL identifier columns to a single string form across every sheet.
# Rationale: product_p is mixed (car ints like 64001 + component strings like 'DK8')
# so it reads as object, while demands.product_p is pure int64 — without a uniform
# canonical form, set comparisons give false "not found" results. period_t and
# quantities stay numeric.
ID_COLS = {"product_p", "mother", "child", "node_n", "starting_node_i",
           "ending_node_j", "group_g", "input_product_group_x", "output_product_group_y"}

def _cid(x):
    """Canonical id: integer-valued floats -> '64001', everything else stripped str."""
    try:
        f = float(x)
        if f.is_integer():
            return str(int(f))
    except (TypeError, ValueError):
        pass
    return str(x).strip()

for name, df in S.items():
    for c in df.columns:
        if c in ID_COLS:
            df[c] = df[c].map(_cid)
log.info("Loaded %d sheets; canonicalised ID columns", len(S))

results: dict = {"counts": {}, "integrity": {}, "referential": {}, "bom": {}}

# ----------------------------------------------------------------------------- #
# 1. Sheet overview
# ----------------------------------------------------------------------------- #
overview = pd.DataFrame(
    [{"sheet": k, "rows": v.shape[0], "cols": v.shape[1],
      "columns": ", ".join(map(str, v.columns))} for k, v in S.items()]
).set_index("sheet")
save_table_image(overview, "p1_sheet_overview",
                 "P1 — Workbook sheet overview (rows, columns)", PHASE, max_rows=20)

# ----------------------------------------------------------------------------- #
# 2. Count reproduction vs CLAUDE.md §4 ground truth
# ----------------------------------------------------------------------------- #
prod, bom, nodes, arcs = S["products"], S["BOM"], S["nodes"], S["arcs"]
dem, inv, flows = S["demands"], S["initial_inventories"], S["initial_flows"]

n_components = bom["child"].nunique()
grp_counts = prod["group_g"].value_counts()

checks = [
    ("products rows", 28049, prod.shape[0]),
    ("products cols", 3, prod.shape[1]),
    ("BOM rows", 87059, bom.shape[0]),
    ("nodes", 12, len(nodes)),
    ("arcs", 11, len(arcs)),
    ("distinct BOM components (children)", 49, int(n_components)),
    ("product group 'car'", 28000, int(grp_counts.get("car", 0))),
    ("demand rows", 28000, dem.shape[0]),
    ("demand periods (min)", 61, int(dem["period_t"].min())),
    ("demand periods (max)", 74, int(dem["period_t"].max())),
    ("demand distinct products", 28000, int(dem["product_p"].nunique())),
    ("capacity_at_arc rows", 154, S["capacity_at_arc"].shape[0]),  # 11 arcs x 14 periods
]
counts_df = pd.DataFrame(checks, columns=["metric", "expected", "observed"])
counts_df["match"] = np.where(counts_df["expected"] == counts_df["observed"], "YES", "**NO**")
counts_df = counts_df.set_index("metric")
save_table_image(counts_df, "p1_count_reproduction",
                 "P1 — Reproduction of audited counts (expected vs observed)", PHASE, max_rows=20)
results["counts"] = {m: {"expected": e, "observed": o, "match": bool(e == o)}
                     for m, e, o in checks}
counts_all_ok = bool((counts_df["match"] == "YES").all())
log.info("Count reproduction all-match: %s", counts_all_ok)

# ----------------------------------------------------------------------------- #
# 3. Missing values + dtype summary
# ----------------------------------------------------------------------------- #
miss_rows = []
for k, v in S.items():
    for c in v.columns:
        nmiss = int(v[c].isna().sum()) + int((v[c].astype(str).str.lower().isin(["nan", "none", ""])).sum()
                                             if v[c].dtype == object else 0)
        miss_rows.append({"sheet": k, "column": c, "dtype": str(v[c].dtype),
                          "n_missing": int(v[c].isna().sum()),
                          "pct_missing": round(100 * v[c].isna().mean(), 3)})
miss_df = pd.DataFrame(miss_rows).set_index(["sheet", "column"])
miss_flagged = miss_df[miss_df["n_missing"] > 0]
save_table_image(miss_df, "p1_missing_values",
                 "P1 — Missing-value & dtype summary (all columns)", PHASE, max_rows=60)
results["integrity"]["columns_with_missing"] = int(len(miss_flagged))
log.info("Columns with missing values: %d", len(miss_flagged))

# ----------------------------------------------------------------------------- #
# 4. Duplicate key checks
# ----------------------------------------------------------------------------- #
KEYS = {
    "products": ["product_p"],
    "nodes": ["node_n"],
    "nodes_inflow": ["node_n", "product_p"],
    "arcs": ["starting_node_i", "ending_node_j"],
    "capacity_at_arc": ["starting_node_i", "ending_node_j", "period_t"],
    "max_flow_product_per_arc": ["starting_node_i", "ending_node_j", "product_p", "period_t"],
    "max_flow_group_per_arc": ["starting_node_i", "ending_node_j", "group_g", "period_t"],
    "operations": ["node_n", "input_product_group_x", "output_product_group_y"],
    "BOM": ["mother", "child"],
    "demands": ["node_n", "product_p", "period_t"],
    "initial_inventories": ["node_n", "product_p", "period_t"],
    "initial_flows": ["starting_node_i", "ending_node_j", "product_p", "period_t"],
}
dup_rows = []
for sheet, key in KEYS.items():
    df = S[sheet]
    ndup = int(df.duplicated(subset=key, keep=False).sum())
    dup_rows.append({"sheet": sheet, "candidate_key": " + ".join(key),
                     "duplicate_rows": ndup, "status": "OK" if ndup == 0 else "**DUPLICATES**"})
dup_df = pd.DataFrame(dup_rows).set_index("sheet")
save_table_image(dup_df, "p1_duplicate_keys",
                 "P1 — Candidate-key uniqueness (duplicate rows per key)", PHASE, max_rows=20)
results["integrity"]["duplicate_key_sheets"] = [r["sheet"] for r in dup_rows if r["duplicate_rows"] > 0]

# ----------------------------------------------------------------------------- #
# 5. Referential integrity
# ----------------------------------------------------------------------------- #
node_set = set(nodes["node_n"])
prod_set = set(prod["product_p"])
group_set = set(prod["group_g"])
arc_set = set(zip(arcs["starting_node_i"], arcs["ending_node_j"]))

def ref_check(desc, bad_series):
    bad = list(dict.fromkeys(map(str, bad_series)))  # unique, preserve order
    return {"check": desc, "violations": len(bad),
            "status": "OK" if len(bad) == 0 else "**FAIL**",
            "examples": ", ".join(bad[:5])}

ref = []
# arcs endpoints in nodes
ref.append(ref_check("arcs.start_node ∈ nodes", arcs.loc[~arcs["starting_node_i"].isin(node_set), "starting_node_i"]))
ref.append(ref_check("arcs.end_node ∈ nodes", arcs.loc[~arcs["ending_node_j"].isin(node_set), "ending_node_j"]))
ref.append(ref_check("arcs.group ∈ product groups", arcs.loc[~arcs["group_g"].isin(group_set), "group_g"]))
# capacity arcs ∈ arcs
cap = S["capacity_at_arc"]
cap_bad = cap.loc[~cap.apply(lambda r: (r["starting_node_i"], r["ending_node_j"]) in arc_set, axis=1)]
ref.append({"check": "capacity_at_arc (i,j) ∈ arcs", "violations": int(len(cap_bad)),
            "status": "OK" if len(cap_bad) == 0 else "**FAIL**",
            "examples": ", ".join(f"{a}->{b}" for a, b in list(zip(cap_bad['starting_node_i'], cap_bad['ending_node_j']))[:5])})
# max_flow_product arcs + products
mfp = S["max_flow_product_per_arc"]
mfp_bad_arc = mfp.loc[~mfp.apply(lambda r: (r["starting_node_i"], r["ending_node_j"]) in arc_set, axis=1)]
ref.append({"check": "max_flow_product (i,j) ∈ arcs", "violations": int(len(mfp_bad_arc)),
            "status": "OK" if len(mfp_bad_arc) == 0 else "**FAIL**", "examples": ""})
ref.append(ref_check("max_flow_product.product ∈ products", mfp.loc[~mfp["product_p"].isin(prod_set), "product_p"]))
# max_flow_group
mfg = S["max_flow_group_per_arc"]
ref.append(ref_check("max_flow_group.group ∈ groups", mfg.loc[~mfg["group_g"].isin(group_set), "group_g"]))
# operations
ops = S["operations"]
ref.append(ref_check("operations.node ∈ nodes", ops.loc[~ops["node_n"].isin(node_set), "node_n"]))
ref.append(ref_check("operations.input_group ∈ groups", ops.loc[~ops["input_product_group_x"].isin(group_set), "input_product_group_x"]))
ref.append(ref_check("operations.output_group ∈ groups", ops.loc[~ops["output_product_group_y"].isin(group_set), "output_product_group_y"]))
# BOM closure
ref.append(ref_check("BOM.mother ∈ products", bom.loc[~bom["mother"].isin(prod_set), "mother"]))
ref.append(ref_check("BOM.child ∈ products", bom.loc[~bom["child"].isin(prod_set), "child"]))
# demands
ref.append(ref_check("demands.node ∈ nodes", dem.loc[~dem["node_n"].isin(node_set), "node_n"]))
ref.append(ref_check("demands.product ∈ products", dem.loc[~dem["product_p"].isin(prod_set), "product_p"]))
# inventories
ref.append(ref_check("initial_inventories.node ∈ nodes", inv.loc[~inv["node_n"].isin(node_set), "node_n"]))
ref.append(ref_check("initial_inventories.product ∈ products", inv.loc[~inv["product_p"].isin(prod_set), "product_p"]))
# initial flows
ref.append(ref_check("initial_flows.product ∈ products", flows.loc[~flows["product_p"].isin(prod_set), "product_p"]))
fl_bad_arc = flows.loc[~flows.apply(lambda r: (r["starting_node_i"], r["ending_node_j"]) in arc_set, axis=1)]
ref.append({"check": "initial_flows (i,j) ∈ arcs", "violations": int(len(fl_bad_arc)),
            "status": "OK" if len(fl_bad_arc) == 0 else "**NOTE**",
            "examples": ", ".join(f"{a}->{b}" for a, b in list(dict.fromkeys(zip(fl_bad_arc['starting_node_i'], fl_bad_arc['ending_node_j'])))[:5])})
# nodes_inflow
ninf = S["nodes_inflow"]
ref.append(ref_check("nodes_inflow.node ∈ nodes", ninf.loc[~ninf["node_n"].isin(node_set), "node_n"]))
ref.append(ref_check("nodes_inflow.product ∈ products", ninf.loc[~ninf["product_p"].isin(prod_set), "product_p"]))

ref_df = pd.DataFrame(ref).set_index("check")
save_table_image(ref_df, "p1_referential_integrity",
                 "P1 — Referential integrity across tables", PHASE, max_rows=40)
results["referential"] = {r["check"]: r["violations"] for r in ref}
ref_fail = [r["check"] for r in ref if r["status"] == "**FAIL**"]
log.info("Referential FAILs: %s", ref_fail or "none")

# ----------------------------------------------------------------------------- #
# 6. BOM structure: cycles, closure, depth
# ----------------------------------------------------------------------------- #
# Separate the 49 benign identity rows (mother == child, qty 1 — each component "is
# itself", matching the identity pass-through operations) from the real parent->child
# BOM edges. Acyclicity and depth are assessed on the real edges.
self_mask = bom["mother"] == bom["child"]
self_loop_rows = bom[self_mask]
real = bom[~self_mask]
G = nx.DiGraph(); G.add_edges_from(zip(real["mother"], real["child"]))
is_dag = nx.is_directed_acyclic_graph(G)
depth = nx.dag_longest_path_length(G) if is_dag else -1
real_cycle = "none"
if not is_dag:
    try:
        real_cycle = str(nx.find_cycle(G))
    except Exception:
        real_cycle = "undetermined"

cpm = bom.groupby("mother").size()
qty = bom["individual_input_quantity_q_mc"]
mothers = set(real["mother"]); children = set(real["child"])
leaves = children - mothers           # pure raw components (never a parent)
selfloop_ids = set(self_loop_rows["mother"])
all_components = set(bom["child"])
bom_summary = pd.DataFrame({
    "value": [
        bom.shape[0], len(self_loop_rows), real.shape[0],
        len(all_components), len(selfloop_ids),
        len(mothers), len(mothers & children), len(leaves),
        "YES" if is_dag else "NO (REAL CYCLE!)", depth, real_cycle,
        int(cpm.min()), round(float(cpm.mean()), 3), int(cpm.max()),
        float(qty.min()), round(float(qty.mean()), 4), float(qty.max()),
    ]}, index=[
        "total BOM rows", "benign identity rows (mother==child)", "real parent->child edges",
        "distinct components (children)", "components with identity row",
        "distinct real mothers", "real mothers that are also children (nested)",
        "pure leaf components (raw)",
        "is DAG after removing identity rows", "max BOM depth (levels)", "real cycle found",
        "children/mother min", "children/mother mean", "children/mother max",
        "input qty min", "input qty mean", "input qty max",
    ])
bom_summary.index.name = "metric"
save_table_image(bom_summary, "p1_bom_structure",
                 "P1 — BOM structure: identity rows, closure, cycles, nesting depth", PHASE, max_rows=20)
results["bom"] = {"is_dag_real_edges": bool(is_dag), "max_depth": int(depth),
                  "identity_rows": int(len(self_loop_rows)), "real_cycle": real_cycle,
                  "pure_leaves": int(len(leaves))}
log.info("BOM (real edges) is_dag=%s depth=%s identity_rows=%d leaves=%d",
         is_dag, depth, len(self_loop_rows), len(leaves))

# ----------------------------------------------------------------------------- #
# 7. Value ranges / unit sanity for key numeric columns
# ----------------------------------------------------------------------------- #
num_specs = [
    ("arcs", "process_lead_time_l_ij", "periods"),
    ("capacity_at_arc", "capacity_c_ijt", "flow units/period"),
    ("max_flow_product_per_arc", "planned_flow", "units/period"),
    ("max_flow_group_per_arc", "planned_flow", "units/period"),
    ("operations", "input_quantity_in_nxy", "units"),
    ("operations", "output_quantity_out_nxy", "units"),
    ("BOM", "individual_input_quantity_q_mc", "units/parent"),
    ("demands", "demand_d_npt", "units/period"),
    ("initial_inventories", "initial_inventory_I_np0", "units"),
    ("initial_inventories", "safety_stock", "units"),
    ("initial_inventories", "max_inventory", "units"),
    ("initial_flows", "initial_flow", "units"),
    ("products", "transportation_size_s", "size class"),
]
vr = []
for sh, col, unit in num_specs:
    s = pd.to_numeric(S[sh][col], errors="coerce")
    vr.append({"sheet.column": f"{sh}.{col}", "unit (assumed)": unit,
               "min": s.min(), "max": s.max(), "mean": round(float(s.mean()), 3),
               "n_negative": int((s < 0).sum()), "n_distinct": int(s.nunique())})
vr_df = pd.DataFrame(vr).set_index("sheet.column")
save_table_image(vr_df, "p1_value_ranges",
                 "P1 — Value ranges & unit sanity for key numeric fields", PHASE, max_rows=20)
results["integrity"]["any_negative_quantities"] = bool((vr_df["n_negative"] > 0).any())

# period coverage per time-indexed sheet
per_rows = []
for sh in ["demands", "capacity_at_arc", "max_flow_product_per_arc", "max_flow_group_per_arc",
           "initial_inventories", "initial_flows"]:
    s = pd.to_numeric(S[sh]["period_t"], errors="coerce")
    per_rows.append({"sheet": sh, "period_min": int(s.min()), "period_max": int(s.max()),
                     "n_distinct_periods": int(s.nunique()),
                     "periods": ", ".join(map(str, sorted(s.dropna().unique().astype(int))))})
per_df = pd.DataFrame(per_rows).set_index("sheet")
save_table_image(per_df, "p1_period_coverage",
                 "P1 — Period coverage by time-indexed table", PHASE, max_rows=20)

# ----------------------------------------------------------------------------- #
# 8. A couple of audit figures
# ----------------------------------------------------------------------------- #
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4.5))
ov = overview["rows"].sort_values()
ax.barh(ov.index, ov.values, color="#2a6f97")
ax.set_xscale("log"); ax.set_xlabel("rows (log scale)")
ax.set_title("Rows per worksheet")
for i, (name, val) in enumerate(ov.items()):
    ax.text(val, i, f" {val:,}", va="center", fontsize=8)
save_fig(fig, "p1_rows_per_sheet", "P1 — Rows per worksheet (log scale)", PHASE); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4))
gc = grp_counts.sort_values()
ax.barh(gc.index, gc.values, color="#e07a5f")
ax.set_xscale("log"); ax.set_xlabel("number of products (log scale)")
ax.set_title("Products per group")
for i, (name, val) in enumerate(gc.items()):
    ax.text(val, i, f" {val:,}", va="center", fontsize=8)
save_fig(fig, "p1_products_per_group", "P1 — Product count by group", PHASE); plt.close(fig)

# ----------------------------------------------------------------------------- #
# 9. Persist machine-readable audit result
# ----------------------------------------------------------------------------- #
results["summary"] = {
    "counts_all_match": counts_all_ok,
    "referential_failures": ref_fail,
    "duplicate_key_sheets": results["integrity"]["duplicate_key_sheets"],
    "bom_is_dag_real_edges": bool(is_dag),
    "bom_identity_rows": int(len(self_loop_rows)),
    "any_negative_quantities": results["integrity"]["any_negative_quantities"],
}
(paths.RESULTS / "p1_audit_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
log.info("Wrote results/p1_audit_results.json")

print("\n" + "=" * 64)
print("P1 AUDIT SUMMARY")
print("  counts all match      :", counts_all_ok)
print("  duplicate-key sheets  :", results["integrity"]["duplicate_key_sheets"] or "none")
print("  referential failures  :", ref_fail or "none")
print("  BOM DAG (real edges)  :", is_dag, "| max depth:", depth,
      "| benign identity rows:", len(self_loop_rows), "| real cycle:", real_cycle)
print("  negative quantities   :", results["integrity"]["any_negative_quantities"])
print("  figures/tables saved  : see reports/figure_index.md")
print("=" * 64)
