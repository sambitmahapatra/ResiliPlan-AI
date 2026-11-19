"""P1 — Generate data/dictionary/data_dictionary.md.

Combines curated semantic descriptions (from the audit) with automatically derived
facts (dtype, distinct counts, missing, example value) for every column of every sheet.
"""
from __future__ import annotations
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
from src.utils import paths, read_all_raw, get_logger

log = get_logger("p1_data_dictionary")
S = read_all_raw()

# --- curated per-sheet purpose + per-column (description, unit) --------------- #
SHEET_PURPOSE = {
    "products": "Master list of every product/SKU in the network and its family (group). "
                "Cars are finished vehicle configurations; the other groups are components.",
    "nodes": "The 12 physical locations in the network: OEM assembly (zp7), the customer/"
             "demand node (zp8), and prod/inv/trans nodes for each supplier family.",
    "nodes_inflow": "Which products are produced at / allowed to flow into each supplier "
                    "production node (component master per supplier).",
    "arcs": "The 11 directed transport links between nodes, each with a transit lead time "
            "and the product group it carries.",
    "capacity_at_arc": "Transport capacity available on each arc in each period.",
    "max_flow_product_per_arc": "Planned / upper-bound flow of a specific product on an arc "
                                "in a period.",
    "max_flow_group_per_arc": "Planned / upper-bound flow of a product group on an arc in a "
                              "period.",
    "operations": "Manufacturing transformations at a node: input group -> output group with "
                  "input/output quantities and yield parameters (alpha, beta).",
    "BOM": "Bill of materials: for each parent product (mother) the child components required "
           "and the quantity per parent. Includes 49 benign identity rows (mother==child).",
    "demands": "Customer demand: units of each finished car required at the demand node per "
               "period. Make-to-order (each config demanded 1 unit, once).",
    "initial_inventories": "Starting inventory at period 60 per node/product, with safety and "
                           "maximum stock levels.",
    "initial_flows": "Material already in transit at the start (dispatched in earlier periods, "
                     "arriving within the horizon) — needed because some lead times exceed 14.",
}

COLS = {
    "product_p": ("Product / SKU identifier (car config id like 64001, or component code "
                  "like DK8).", "id"),
    "group_g": ("Product family: car, engine, gear, battery, seat, seat_componment, "
                "battery_componment.", "category"),
    "transportation_size_s": ("Transport size class of the product. Constant 0 across all "
                              "rows in this dataset (no size differentiation used).", "size class"),
    "node_n": ("Node identifier.", "id"),
    "starting_node_i": ("Origin node of the arc.", "id"),
    "ending_node_j": ("Destination node of the arc.", "id"),
    "process_lead_time_l_ij": ("Transit/process lead time on the arc, in planning periods "
                               "(0-23; battery/seat 'trans' arcs exceed the 14-period horizon).",
                               "periods"),
    "period_t": ("Planning period index. Horizon is 61-74 (14 periods); initial-state tables "
                 "use earlier periods (39-60).", "period"),
    "capacity_c_ijt": ("Transport capacity on arc (i,j) in period t.", "flow units/period"),
    "planned_flow": ("Planned / upper-bound flow (product- or group-specific) on the arc in "
                     "the period.", "units/period"),
    "input_product_group_x": ("Input product group consumed by the operation.", "category"),
    "output_product_group_y": ("Output product group produced by the operation.", "category"),
    "input_quantity_in_nxy": ("Units of input group consumed per operation (e.g. 20 battery "
                              "components -> 1 battery).", "units"),
    "output_quantity_out_nxy": ("Units of output group produced per operation.", "units"),
    "alpha_nxy": ("Operation yield/efficiency parameter alpha (fixed component).", "coef"),
    "beta_nxy": ("Operation yield/efficiency parameter beta (variable component; 1 = active "
                 "transformation, 0 = sink/pass-through at zp8).", "coef"),
    "mother": ("Parent product in a BOM relationship.", "id"),
    "child": ("Child component required by the parent.", "id"),
    "individual_input_quantity_q_mc": ("Quantity of child required per one unit of parent "
                                       "(1-10).", "units/parent"),
    "demand_d_npt": ("Demand for the product at the node in the period (all = 1 unit).", "units"),
    "initial_inventory_I_np0": ("Inventory on hand at the start (period 60).", "units"),
    "safety_stock": ("Safety-stock level (mostly 0 in this dataset).", "units"),
    "max_inventory": ("Maximum inventory bound (mostly 99999 = effectively uncapped).", "units"),
    "initial_flow": ("Units already in transit on the arc at the start.", "units"),
}

KEYS = {
    "products": "product_p", "nodes": "node_n",
    "nodes_inflow": "(node_n, product_p)", "arcs": "(starting_node_i, ending_node_j)",
    "capacity_at_arc": "(starting_node_i, ending_node_j, period_t)",
    "max_flow_product_per_arc": "(starting_node_i, ending_node_j, product_p, period_t)",
    "max_flow_group_per_arc": "(starting_node_i, ending_node_j, group_g, period_t)",
    "operations": "(node_n, input_product_group_x, output_product_group_y)",
    "BOM": "(mother, child)", "demands": "(node_n, product_p, period_t)",
    "initial_inventories": "(node_n, product_p, period_t)",
    "initial_flows": "(starting_node_i, ending_node_j, product_p, period_t)",
}


def example_value(s: pd.Series) -> str:
    v = s.dropna()
    if len(v) == 0:
        return ""
    x = v.iloc[0]
    if isinstance(x, float) and float(x).is_integer():
        x = int(x)
    return str(x)[:24]


lines: list[str] = []
lines.append("# Data Dictionary — ResiliPlan AI\n")
lines.append(f"_Generated {date.today().isoformat()} by `src/audit/p1_data_dictionary.py` "
             f"from the read-only workbook `data/raw/2020_dataset_OfAutomotiveProductionNetwork.xlsb`._\n")
lines.append("**Source dataset:** Moetz, Quetschlich & Otto (2020), *Optimisation Model for "
             "Multi-Item Multi-Echelon Supply Chains with Nested Multi-Level Products*, "
             "Mendeley Data, https://doi.org/10.17632/pr3sdy5vp3.1\n")
lines.append("## Dataset-level notes\n")
lines.append("- **Scale:** 12 nodes, 11 arcs, 28,049 products, 87,059 BOM rows, 14 periods "
             "(61–74).\n"
             "- **Components:** only **49 distinct components** underlie the 28,000 car "
             "configurations (each car = 3–4 components, mean 3.1).\n"
             "- **BOM shape:** a DAG of max depth 2 (car → component → sub-component) after "
             "excluding 49 benign identity rows (mother==child, qty 1, one per component).\n"
             "- **Demand:** make-to-order — each car config is demanded exactly 1 unit, once; "
             "2,000 configs/period × 14 = 28,000.\n"
             "- **Costs:** the workbook contains **NO cost data**. All cost/price parameters in "
             "the optimization are ASSUMED and disclosed separately (see "
             "`data/assumptions/`).\n"
             "- **Units:** not stated in the source; units below are documented assumptions "
             "based on column semantics (quantities = pieces/units, lead times = periods, "
             "capacity = flow units/period).\n"
             "- **Integrity:** no missing values, no duplicate keys, and all cross-table "
             "references resolve (see P1 audit tables / figures).\n")

for sheet, df in S.items():
    lines.append(f"\n## `{sheet}` — {df.shape[0]:,} rows × {df.shape[1]} cols")
    lines.append(f"\n{SHEET_PURPOSE.get(sheet, '')}\n")
    lines.append(f"**Primary key:** `{KEYS.get(sheet, '?')}`\n")
    lines.append("| column | type | unit (assumed) | distinct | missing | example | description |")
    lines.append("|---|---|---|---:|---:|---|---|")
    for c in df.columns:
        desc, unit = COLS.get(c, ("", ""))
        lines.append(
            f"| `{c}` | {df[c].dtype} | {unit} | {df[c].nunique():,} | "
            f"{int(df[c].isna().sum())} | {example_value(df[c])} | {desc} |"
        )

paths.DICTIONARY.mkdir(parents=True, exist_ok=True)
out = paths.DICTIONARY / "data_dictionary.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
log.info("Wrote %s (%d lines)", out, len(lines))
print("Data dictionary written:", out)
