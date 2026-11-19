"""Reference-data access for the ResiliPlan API and the Supabase seed generator.

Reads the versioned clean tables (data/clean) and phase results (results/*.json). No
database required — these feed both the API GET endpoints and the Supabase seed export.
"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

# project root = .../Project (this file is .../Project/app/api/data_access.py)
ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

import pandas as pd
import networkx as nx

from src.utils import paths

DIRECT_GROUPS = {"engine", "gear", "battery", "seat"}
HORIZON_LEN = 14


def _read_clean(name: str) -> pd.DataFrame:
    return pd.read_csv(paths.CLEAN / f"{name}.v1.csv")


def _node_meta(node: str) -> tuple[str, str]:
    """Return (family, role) parsed from a node id."""
    if node == "zp8":
        return "oem", "demand"
    if node == "zp7":
        return "oem", "assembly"
    fam = node.split("-")[0] if "-" in node else node
    role = "prod" if node.endswith("_prod") else "inv" if node.endswith("_inv") else \
           "trans" if node.endswith("_trans") else "node"
    return fam, role


@lru_cache(maxsize=1)
def get_network() -> dict:
    nodes = _read_clean("nodes")["node_n"].astype(str).tolist()
    arcs = _read_clean("arcs")
    for c in ["starting_node_i", "ending_node_j", "group_g"]:
        arcs[c] = arcs[c].astype(str)
    arcs["process_lead_time_l_ij"] = pd.to_numeric(arcs["process_lead_time_l_ij"]).astype(int)
    G = nx.DiGraph(); G.add_nodes_from(nodes)
    G.add_edges_from(zip(arcs["starting_node_i"], arcs["ending_node_j"]))
    node_rows = []
    for n in nodes:
        fam, role = _node_meta(n)
        try:
            lvl = nx.shortest_path_length(G, n, "zp8")
        except Exception:
            lvl = None
        node_rows.append({"node_n": n, "family": fam, "role": role, "echelon_level": lvl})
    arc_rows = [{"starting_node_i": i, "ending_node_j": j, "group_g": g,
                 "lead_time": int(l), "exceeds_horizon": bool(l > HORIZON_LEN)}
                for i, j, g, l in zip(arcs["starting_node_i"], arcs["ending_node_j"],
                                      arcs["group_g"], arcs["process_lead_time_l_ij"])]
    return {"nodes": node_rows, "arcs": arc_rows}


@lru_cache(maxsize=1)
def get_criticality() -> list[dict]:
    df = _read_clean("component_criticality")
    df["is_direct_car_component"] = df["group"].isin(DIRECT_GROUPS)
    df = df.rename(columns={"component": "component_p", "group": "group_g"})
    cols = ["component_p", "group_g", "origin_node", "n_cars_using", "pct_configs_dependent",
            "gross_demand_total", "cum_lead_time", "risk_score", "is_direct_car_component"]
    return df[cols].where(pd.notna(df[cols]), None).to_dict("records")


@lru_cache(maxsize=1)
def get_scenarios() -> list[dict]:
    out = []
    for f in sorted(paths.SCENARIOS.glob("scenario_*.json")):
        sc = json.loads(f.read_text(encoding="utf-8"))
        out.append({"id": sc["id"], "name": sc["name"], "nature": sc.get("nature", ""),
                    "managerial_question": sc.get("managerial_question", ""),
                    "modifications": sc.get("modifications", {}),
                    "is_synthetic": "synthetic" in sc.get("nature", "").lower()})
    return out


@lru_cache(maxsize=1)
def get_cost_assumptions() -> list[dict]:
    df = pd.read_csv(paths.ASSUMPTIONS / "cost_assumptions.csv")
    return df.to_dict("records")


@lru_cache(maxsize=1)
def get_precomputed_scenarios() -> dict:
    """Baseline + 6-scenario results + Monte Carlo, from results/p6_results.json."""
    p = paths.RESULTS / "p6_results.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_data_summary() -> dict:
    """Source-table catalog + validation status (real), for the Data Studio screen.

    Reads results/p1_audit_results.json (validation) and the clean tables (row counts)."""
    sheets_meta = [
        ("products", "Product master (cars + components)", "Master data"),
        ("nodes", "Production / inventory / transport nodes", "Network"),
        ("nodes_inflow", "Products produced at each supplier node", "Network"),
        ("arcs", "Directed transport links + lead times", "Network"),
        ("capacity_at_arc", "Transport capacity by period", "Capacity"),
        ("max_flow_product_per_arc", "Planned product flow per arc/period", "Capacity"),
        ("max_flow_group_per_arc", "Planned group flow per arc/period", "Capacity"),
        ("operations", "Manufacturing transformations (recipes)", "Production"),
        ("BOM", "Bill of materials (parent -> child)", "BOM"),
        ("demands", "Customer demand by product/period", "Demand"),
        ("initial_inventories", "Starting inventory, safety & max stock", "Inventory"),
        ("initial_flows", "In-transit material at horizon start", "Inventory"),
    ]
    rows = []
    for name, desc, role in sheets_meta:
        try:
            n = int(pd.read_csv(paths.CLEAN / f"{name}.v1.csv").shape[0])
        except Exception:
            n = None
        rows.append({"table": name, "rows": n, "description": desc, "role": role})

    audit = {}
    p = paths.RESULTS / "p1_audit_results.json"
    if p.exists():
        a = json.loads(p.read_text(encoding="utf-8"))
        s = a.get("summary", {})
        audit = {
            "counts_all_match": s.get("counts_all_match"),
            "referential_failures": s.get("referential_failures", []),
            "duplicate_key_sheets": s.get("duplicate_key_sheets", []),
            "bom_is_dag": s.get("bom_is_dag_real_edges"),
            "bom_identity_rows": s.get("bom_identity_rows"),
            "any_negative_quantities": s.get("any_negative_quantities"),
            "columns_with_missing": a.get("integrity", {}).get("columns_with_missing"),
        }
    return {
        "source_file": "2020_dataset_OfAutomotiveProductionNetwork.xlsb",
        "source_format": "XLSB", "worksheets": len(sheets_meta),
        "horizon": "Periods 61–74 (14 periods)",
        "status": "Cleaned, validated & loaded (versioned CSVs in data/clean)",
        "tables": rows, "validation": audit,
    }


def scenario_result_rows() -> list[dict]:
    """Flatten p6 results into scenario_results rows (for seed + /scenarios/results)."""
    data = get_precomputed_scenarios()
    base_obj = data.get("baseline_objective")
    rows = []
    for r in data.get("scenarios", []):
        cb = r.get("cost", {})
        rows.append({
            "scenario_id": r["scenario"], "status": "optimal" if r.get("optimal") else "non-optimal",
            "objective_mu": round(r.get("objective", 0), 2),
            "vs_baseline_mu": round(r.get("objective", 0) - (base_obj or 0), 2),
            "service_overall_pct": r.get("service", {}).get("overall"),
            "battery_service_pct": r.get("service", {}).get("by_group", {}).get("battery"),
            "total_shortage": round(r.get("service", {}).get("total_shortage", 0), 2),
            "expedite_units": round(r.get("expedite_units", 0), 2),
            "cost_breakdown": cb,
            "service_by_group": r.get("service", {}).get("by_group", {}),
            "validated": bool(r.get("validation_ok", False)),
        })
    return rows
