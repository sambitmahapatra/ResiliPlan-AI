"""P5 — Build a solver-ready instance from the cleaned data, cost params, and a scenario.

Component-layer formulation. Each component belongs to a group whose supply chain is a
fixed serial path of nodes/arcs toward the assembly node zp7, where component requirements
(the P2 explosion) are consumed to fulfil car demand. Battery/seat have an upstream
transform (sub-component -> component) per the BOM SKU quantities (NOT the operations 20:1
again — see src/model/modeling_notes.md).

This module only PREPARES data (sets, params, chains, demand, initial state, scenario
modifications). The optimisation lives in src/model/milp.py.
"""
from __future__ import annotations
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.utils import paths, read_clean

ASSEMBLY = "zp7"
DEMAND_NODE = "zp8"
PERIODS = list(range(61, 75))          # 61..74
INIT_PERIOD = 60


def _cid(x):
    try:
        f = float(x)
        if f.is_integer():
            return str(int(f))
    except (TypeError, ValueError):
        pass
    return str(x).strip()


@dataclass
class Instance:
    scenario_id: str
    periods: list
    components: list                   # list of component ids (49)
    group_of: dict                     # comp -> group
    nodes: list
    arcs: list                         # list of (i,j)
    lead: dict                         # (i,j) -> lead time (int, after scenario deltas)
    arc_group: dict                    # (i,j) -> group carried
    arc_cap: dict                      # (i,j,t) -> capacity (after scenario multipliers)
    group_chain_arcs: dict             # group -> ordered list of arcs source..zp7
    source_node: dict                  # group -> source node (most upstream)
    transform: dict                    # group -> {"at": node, "inputs": {sub_comp: qty_per_output}}
    comp_demand: dict                  # (comp, t) -> required qty at zp7 (after scenario)
    init_inv: dict                     # (comp, node) -> starting inventory at INIT_PERIOD
    init_arrivals: dict                # (comp, node, t) -> units arriving from initial_flows
    costs: dict
    enable_expedite: bool = False
    meta: dict = field(default_factory=dict)


def load_scenario(scenario_id: str) -> dict:
    p = paths.SCENARIOS / f"scenario_{scenario_id}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def build_instance(scenario_id: str = "baseline") -> Instance:
    """Build an instance from a saved scenario file (data/scenarios/scenario_<id>.json)."""
    return build_instance_from_config(load_scenario(scenario_id))


def build_instance_from_config(sc: dict) -> Instance:
    """Build an instance from a scenario config dict (same shape as the saved JSON).

    Enables the API to run custom/ad-hoc scenarios without writing a file. The dict may
    carry an 'id', 'name', 'nature', and 'modifications' (arc_capacity_multiplier,
    arc_lead_time_delta, car_demand_multiplier, enable_expedite)."""
    scenario_id = sc.get("id", "custom")
    mods = sc.get("modifications", {})
    costs = json.loads((paths.ASSUMPTIONS / "cost_params.json").read_text(encoding="utf-8"))

    # --- products / components ---
    prod = read_clean("products"); prod["product_p"] = prod["product_p"].map(_cid); prod["group_g"] = prod["group_g"].map(_cid)
    group_of_all = dict(zip(prod["product_p"], prod["group_g"]))
    bom_real = read_clean("bom_real");
    components = sorted(set(bom_real["child"].map(_cid)))
    group_of = {c: group_of_all[c] for c in components}

    # --- nodes / arcs / lead / capacity ---
    nodes = read_clean("nodes")["node_n"].map(_cid).tolist()
    arcs_df = read_clean("arcs")
    for c in ["starting_node_i", "ending_node_j", "group_g"]:
        arcs_df[c] = arcs_df[c].map(_cid)
    arcs_df["process_lead_time_l_ij"] = pd.to_numeric(arcs_df["process_lead_time_l_ij"]).astype(int)
    arcs = list(zip(arcs_df["starting_node_i"], arcs_df["ending_node_j"]))
    lead = {(i, j): int(l) for i, j, l in zip(arcs_df["starting_node_i"], arcs_df["ending_node_j"], arcs_df["process_lead_time_l_ij"])}
    arc_group = {(i, j): g for i, j, g in zip(arcs_df["starting_node_i"], arcs_df["ending_node_j"], arcs_df["group_g"])}

    # scenario: arc lead-time deltas
    for m in mods.get("arc_lead_time_delta", []):
        i, j = m["arc"]; lead[(i, j)] = max(0, lead[(i, j)] + int(m["delta_periods"]))

    cap_df = read_clean("capacity_at_arc")
    for c in ["starting_node_i", "ending_node_j"]:
        cap_df[c] = cap_df[c].map(_cid)
    cap_df["period_t"] = pd.to_numeric(cap_df["period_t"]).astype(int)
    cap_df["capacity_c_ijt"] = pd.to_numeric(cap_df["capacity_c_ijt"]).astype(float)
    arc_cap = {(i, j, t): c for i, j, t, c in zip(cap_df["starting_node_i"], cap_df["ending_node_j"], cap_df["period_t"], cap_df["capacity_c_ijt"])}
    # scenario: arc capacity multipliers
    for m in mods.get("arc_capacity_multiplier", []):
        i, j = m["arc"]; f = float(m["factor"])
        per = m["periods"] if m["periods"] != "all" else PERIODS
        for t in per:
            if (i, j, t) in arc_cap:
                arc_cap[(i, j, t)] *= f

    # --- group chains (source -> ... -> zp7) via the arc network, per group ---
    import networkx as nx
    Gnet = nx.DiGraph(); Gnet.add_edges_from(arcs)
    groups = sorted(set(group_of.values()))
    group_chain_arcs, source_node = {}, {}
    for g in groups:
        g_arcs = [a for a in arcs if arc_group[a] == g]
        sub = nx.DiGraph(); sub.add_edges_from(g_arcs)
        # source = node with no incoming g-arc; sink toward zp7
        starts = [i for (i, j) in g_arcs]; ends = [j for (i, j) in g_arcs]
        src_candidates = [n for n in set(starts) if n not in set(ends)]
        source_node[g] = src_candidates[0] if src_candidates else (starts[0] if starts else None)
        # ordered path from source to the last node before/at zp7
        if source_node[g] is not None and g_arcs:
            # target = node that connects to zp7 (end == zp7) else deepest
            tgt = next((j for (i, j) in g_arcs if j == ASSEMBLY), ends[-1])
            try:
                node_path = nx.shortest_path(sub, source_node[g], tgt)
                group_chain_arcs[g] = [(node_path[k], node_path[k + 1]) for k in range(len(node_path) - 1)]
            except Exception:
                group_chain_arcs[g] = g_arcs
        else:
            group_chain_arcs[g] = g_arcs

    # --- transforms (battery, seat): sub-component -> component, qty from BOM SKU ---
    # parent(component) -> children(sub-components) with qty, at the group's *_prod node
    bom_real["mother"] = bom_real["mother"].map(_cid); bom_real["child"] = bom_real["child"].map(_cid)
    bom_real["individual_input_quantity_q_mc"] = pd.to_numeric(bom_real["individual_input_quantity_q_mc"])
    transform = {}
    for g in ["battery", "seat"]:
        node = f"{g}-supplier_prod"
        # components of group g that are parents of sub-components
        parents = [c for c in components if group_of[c] == g]
        inputs = {}
        for parent in parents:
            kids = bom_real[bom_real["mother"] == parent]
            for _, r in kids.iterrows():
                child = r["child"]
                if group_of.get(child, "") == f"{g}_componment":
                    inputs.setdefault(parent, {})[child] = float(r["individual_input_quantity_q_mc"])
        transform[g] = {"at": node, "inputs": inputs}

    # --- component demand at zp7 (P2 explosion), with scenario demand surge ---
    cd = read_clean("component_demand")
    cd["component"] = cd["component"].map(_cid); cd["period"] = pd.to_numeric(cd["period"]).astype(int)
    cd["required_qty"] = pd.to_numeric(cd["required_qty"]).astype(float)
    comp_demand = {(c, t): q for c, t, q in zip(cd["component"], cd["period"], cd["required_qty"])}
    # demand surge multiplies car demand -> scales all component requirements in those periods
    for m in mods.get("car_demand_multiplier", []):
        f = float(m["factor"]); per = m["periods"] if m["periods"] != "all" else PERIODS
        for (c, t) in list(comp_demand.keys()):
            if t in per:
                comp_demand[(c, t)] *= f

    # --- initial inventory (period 60) ---
    inv = read_clean("initial_inventories")
    inv["node_n"] = inv["node_n"].map(_cid); inv["product_p"] = inv["product_p"].map(_cid)
    inv["initial_inventory_I_np0"] = pd.to_numeric(inv["initial_inventory_I_np0"]).astype(float)
    init_inv = {(p, n): v for p, n, v in zip(inv["product_p"], inv["node_n"], inv["initial_inventory_I_np0"])
                if p in group_of}

    # --- initial flows (in-transit) -> arrivals within horizon ---
    fl = read_clean("initial_flows")
    for c in ["starting_node_i", "ending_node_j"]:
        fl[c] = fl[c].map(_cid)
    fl["product_p"] = fl["product_p"].map(_cid); fl["period_t"] = pd.to_numeric(fl["period_t"]).astype(int)
    fl["initial_flow"] = pd.to_numeric(fl["initial_flow"]).astype(float)
    init_arrivals = {}
    for _, r in fl.iterrows():
        i, j, p, dep, q = r["starting_node_i"], r["ending_node_j"], r["product_p"], r["period_t"], r["initial_flow"]
        if p not in group_of:
            continue
        L = lead.get((i, j))
        if L is None:
            continue
        arr = dep + L
        if arr in PERIODS:
            init_arrivals[(p, j, arr)] = init_arrivals.get((p, j, arr), 0.0) + q

    return Instance(
        scenario_id=scenario_id, periods=PERIODS, components=components, group_of=group_of,
        nodes=nodes, arcs=arcs, lead=lead, arc_group=arc_group, arc_cap=arc_cap,
        group_chain_arcs=group_chain_arcs, source_node=source_node, transform=transform,
        comp_demand=comp_demand, init_inv=init_inv, init_arrivals=init_arrivals,
        costs=costs, enable_expedite=bool(mods.get("enable_expedite", False)),
        meta={"scenario_name": sc.get("name"), "nature": sc.get("nature")},
    )


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    inst = build_instance("baseline")
    print("components:", len(inst.components), "| groups:", sorted(set(inst.group_of.values())))
    print("periods:", inst.periods[0], "-", inst.periods[-1])
    for g, chain in inst.group_chain_arcs.items():
        print(f"  chain[{g}]: source={inst.source_node[g]}  arcs={chain}")
    print("transforms:")
    for g, tr in inst.transform.items():
        ex = next(iter(tr["inputs"].items())) if tr["inputs"] else None
        print(f"  {g} at {tr['at']}: {len(tr['inputs'])} parents; example {ex}")
    print("comp_demand entries:", len(inst.comp_demand),
          "| init_inv entries:", len(inst.init_inv),
          "| init_arrivals entries:", len(inst.init_arrivals))
