"""P5 — Component-layer production/inventory/distribution LP, solved with HiGHS via
scipy.optimize.milp.

Formulation (all variables continuous >= 0; this is an LP, solved with HiGHS):
  inv[p,n,t]     inventory of component p at node n, end of period t
  prod[p,n,t]    production/sourcing of p at node n (source nodes; transform outputs)
  ship[p,i,j,t]  shipment of p on chain arc (i,j) departing in t (arrives t+lead)
  served[p,t]    direct car-component p demand met at zp7 in t
  short[p,t]     direct car-component p demand unmet at zp7 in t

Only the 4 direct car-component groups {engine,gear,battery,seat} carry zp7 demand.
battery/seat are produced at *_prod by consuming sub-components per the BOM SKU quantities
(the 20:1 is applied ONCE, here — see modeling_notes.md). Sub-components have no independent
demand; their requirement is derived from battery/seat production.

See src/model/instance.py for the data. Material balance per (p,n,t):
  inv[t] = inv[t-1] + prod + arrivals - consumed - shipout - served(zp7 only)
  arrivals = sum ship[p,i,n, t-lead(i,n)] (dep>=61) + init_arrivals (seeded in-transit)
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, vstack as _sp_vstack
import scipy.optimize._highspy._core as _hcore  # scipy's bundled HiGHS (SAC-safe)

from src.model.instance import Instance, build_instance, ASSEMBLY

# Map HiGHS model-status string -> our integer code (0 = optimal/success).
_STATUS_MAP = {"Optimal": 0, "Infeasible": 2, "Unbounded": 3,
               "Time limit reached": 1, "Iteration limit reached": 1}


def _highs_solve(cvec, A_eq, b_eq, A_ub, b_ub, lb, ub, integrality=None):
    """Solve via scipy's bundled HiGHS core directly.

    We bypass scipy.optimize.linprog/milp because their Python wrapper spends tens of
    seconds extracting per-variable marginals/basis element-by-element (O(numcol) slow
    pybind accesses) that we never use — HiGHS itself solves this model in <0.05s.
    Returns (sol_dict, x_array). x is None unless optimal.
    """
    ncol = int(cvec.size)
    if A_ub is not None and A_ub.shape[0] > 0:
        A = _sp_vstack([A_eq, A_ub]).tocsc()
        rl = np.concatenate([b_eq, np.full(A_ub.shape[0], -np.inf)])
        ru = np.concatenate([b_eq, b_ub])
    else:
        A = A_eq.tocsc(); rl = b_eq.copy(); ru = b_eq.copy()
    lp = _hcore.HighsLp()
    lp.num_col_ = ncol; lp.num_row_ = int(A.shape[0])
    lp.col_cost_ = np.asarray(cvec, dtype=float)
    lp.col_lower_ = np.asarray(lb, dtype=float)
    lp.col_upper_ = np.asarray(ub, dtype=float)
    lp.row_lower_ = np.asarray(rl, dtype=float)
    lp.row_upper_ = np.asarray(ru, dtype=float)
    lp.a_matrix_.format_ = _hcore.MatrixFormat.kColwise
    lp.a_matrix_.num_col_ = ncol; lp.a_matrix_.num_row_ = int(A.shape[0])
    lp.a_matrix_.start_ = A.indptr
    lp.a_matrix_.index_ = A.indices
    lp.a_matrix_.value_ = A.data
    if integrality is not None and np.sum(integrality) > 0:
        lp.integrality_ = [_hcore.HighsVarType(int(i)) for i in integrality]
    h = _hcore._Highs()
    h.setOptionValue("output_flag", False)
    h.passModel(lp)
    h.run()
    status_str = h.modelStatusToString(h.getModelStatus()).strip()
    optimal = status_str.lower() == "optimal"
    x = np.array(h.getSolution().col_value) if optimal else None
    obj = float(h.getInfo().objective_function_value) if optimal else None
    return {"status": _STATUS_MAP.get(status_str, 0 if optimal else 1),
            "success": optimal, "message": f"HiGHS: {status_str}", "objective": obj}, x

DIRECT_GROUPS = {"engine", "gear", "battery", "seat"}
SUBCOMP_GROUPS = {"battery_componment", "seat_componment"}


class VarRegistry:
    def __init__(self):
        self.index: dict = {}
        self.keys: list = []
        self.lb: list = []
        self.ub: list = []
        self.cost: list = []

    def add(self, key, cost=0.0, lb=0.0, ub=np.inf):
        if key in self.index:
            return self.index[key]
        i = len(self.keys)
        self.index[key] = i
        self.keys.append(key)
        self.lb.append(lb); self.ub.append(ub); self.cost.append(cost)
        return i

    def __contains__(self, key):
        return key in self.index

    def __getitem__(self, key):
        return self.index[key]

    def __len__(self):
        return len(self.keys)


def _base(group: str) -> str:
    return group.replace("_componment", "")


def build_and_solve(inst: Instance, time_limit: float = 120.0):
    V = VarRegistry()
    C = inst.costs
    pc = C["prod_cost"]; tb = C["transport_cost_base"]; tpl = C["transport_cost_per_lead_period"]
    hr = C["holding_rate_per_period"]; sp = C["shortage_penalty_car"]
    red = int(C.get("expedite_lead_reduction", 1)); mult = float(C.get("expedite_multiplier", 3.0))
    exp_on = bool(inst.enable_expedite)
    def exp_lead(i, j):
        return max(0, inst.lead[(i, j)] - red)
    periods = inst.periods; t0 = periods[0]
    g_of = inst.group_of

    # nodes on each component's chain
    chain_nodes = {}
    for g, arcs in inst.group_chain_arcs.items():
        ns = []
        for (i, j) in arcs:
            if i not in ns: ns.append(i)
            if j not in ns: ns.append(j)
        chain_nodes[g] = ns
    in_arcs = {}   # node -> incoming chain arcs within group
    out_arcs = {}
    for g, arcs in inst.group_chain_arcs.items():
        for (i, j) in arcs:
            out_arcs.setdefault((g, i), []).append((i, j))
            in_arcs.setdefault((g, j), []).append((i, j))

    # subcomp consumers: subcomp -> [(parent, qty)] at transform node
    subcomp_consumers = {}
    transform_node = {}
    for base, tr in inst.transform.items():
        transform_node[base] = tr["at"]
        for parent, inputs in tr["inputs"].items():
            for sc, q in inputs.items():
                subcomp_consumers.setdefault(sc, []).append((parent, q, tr["at"]))

    def produces(p, n):
        g = g_of[p]
        if g in {"engine", "gear"} and n == inst.source_node[g]:
            return True
        if g in SUBCOMP_GROUPS and n == inst.source_node[g]:
            return True
        if g in {"battery", "seat"} and n == f"{g}-supplier_prod":
            return True
        return False

    # ---- create variables ----
    for p in inst.components:
        g = g_of[p]; is_direct = g in DIRECT_GROUPS
        for t in periods:
            for n in chain_nodes[g]:
                V.add(("inv", p, n, t), cost=hr * pc[g])
                if produces(p, n):
                    V.add(("prod", p, n, t), cost=pc[g])
                for (i, j) in out_arcs.get((g, n), []):
                    V.add(("ship", p, i, j, t), cost=tb + tpl * inst.lead[(i, j)])
                    if exp_on:
                        V.add(("eship", p, i, j, t), cost=(tb + tpl * exp_lead(i, j)) * mult)
            if is_direct:
                V.add(("served", p, t), cost=0.0)
                V.add(("short", p, t), cost=sp)

    nvar = len(V)
    cvec = np.array(V.cost, dtype=float)
    lb = np.array(V.lb, dtype=float); ub = np.array(V.ub, dtype=float)

    # ---- equality constraints ----
    rows, cols, data, beq = [], [], [], []
    r = 0

    def add_term(row, key, coef):
        rows.append(row); cols.append(V[key]); data.append(coef)

    # balance per (p, n, t)
    for p in inst.components:
        g = g_of[p]; is_direct = g in DIRECT_GROUPS
        for n in chain_nodes[g]:
            for t in periods:
                rhs = 0.0
                add_term(r, ("inv", p, n, t), 1.0)
                if t > t0:
                    add_term(r, ("inv", p, n, t - 1), -1.0)
                else:
                    rhs += inst.init_inv.get((p, n), 0.0)       # inv[t-1] at init period
                if produces(p, n):
                    add_term(r, ("prod", p, n, t), -1.0)
                # consumption of p (sub-component) at transform node
                if g in SUBCOMP_GROUPS:
                    for (parent, q, at) in subcomp_consumers.get(p, []):
                        if at == n:
                            add_term(r, ("prod", parent, at, t), q)   # +q*prod(parent)
                # arrivals from incoming chain arcs
                for (i, j) in in_arcs.get((g, n), []):
                    dep = t - inst.lead[(i, j)]
                    if dep >= t0:
                        add_term(r, ("ship", p, i, j, dep), -1.0)
                    if exp_on:
                        dep_e = t - exp_lead(i, j)
                        if dep_e >= t0 and ("eship", p, i, j, dep_e) in V:
                            add_term(r, ("eship", p, i, j, dep_e), -1.0)
                rhs += inst.init_arrivals.get((p, n, t), 0.0)
                # shipout
                for (i, j) in out_arcs.get((g, n), []):
                    add_term(r, ("ship", p, i, j, t), 1.0)
                    if exp_on and ("eship", p, i, j, t) in V:
                        add_term(r, ("eship", p, i, j, t), 1.0)
                # served at zp7
                if is_direct and n == ASSEMBLY:
                    add_term(r, ("served", p, t), 1.0)
                beq.append(rhs); r += 1

    # demand satisfaction: served + short = demand (direct comps)
    for p in inst.components:
        if g_of[p] in DIRECT_GROUPS:
            for t in periods:
                add_term(r, ("served", p, t), 1.0)
                add_term(r, ("short", p, t), 1.0)
                beq.append(inst.comp_demand.get((p, t), 0.0)); r += 1

    A_eq = coo_matrix((data, (rows, cols)), shape=(r, nvar)).tocsr()
    b_eq = np.array(beq, dtype=float)

    # ---- inequality: arc capacity (sum over components in arc's group) ----
    urows, ucols, udata, bub = [], [], [], []
    ur = 0
    for (i, j) in inst.arcs:
        g = inst.arc_group[(i, j)]
        if g not in g_of.values() and g != "car":
            pass
        for t in periods:
            cap = inst.arc_cap.get((i, j, t))
            if cap is None:
                continue
            terms = [p for p in inst.components if g_of[p] == g and ("ship", p, i, j, t) in V]
            if not terms:
                continue
            for p in terms:
                urows.append(ur); ucols.append(V[("ship", p, i, j, t)]); udata.append(1.0)
            bub.append(cap); ur += 1
    A_ub = coo_matrix((udata, (urows, ucols)), shape=(ur, nvar)).tocsr() if ur else None
    b_ub = np.array(bub, dtype=float) if ur else None

    # ---- solve (scipy's bundled HiGHS core, directly — see _highs_solve) ----
    sol, x = _highs_solve(cvec, A_eq, b_eq, A_ub, b_ub, lb, ub)
    sol.update({"nvar": nvar, "n_eq": r, "n_ub": ur})
    if x is not None:
        # keep only the sparse nonzero map (downstream uses sol["x"] only); drop the full
        # dense array and registry copies to minimise memory across many sequential solves.
        sol["x"] = {V.keys[i]: float(x[i]) for i in range(nvar) if abs(x[i]) > 1e-9}
    return sol, V


def solution_frames(sol: dict, inst: Instance) -> dict:
    """Tidy DataFrames of the solution for reporting / validation."""
    x = sol.get("x", {})
    rows_short, rows_served, rows_ship, rows_prod, rows_inv = [], [], [], [], []
    for key, v in x.items():
        kind = key[0]
        if kind == "short":
            rows_short.append({"component": key[1], "period": key[2], "short": v})
        elif kind == "served":
            rows_served.append({"component": key[1], "period": key[2], "served": v})
        elif kind == "ship":
            rows_ship.append({"component": key[1], "i": key[2], "j": key[3], "period": key[4], "qty": v, "expedited": False})
        elif kind == "eship":
            rows_ship.append({"component": key[1], "i": key[2], "j": key[3], "period": key[4], "qty": v, "expedited": True})
        elif kind == "prod":
            rows_prod.append({"component": key[1], "node": key[2], "period": key[3], "qty": v})
        elif kind == "inv":
            rows_inv.append({"component": key[1], "node": key[2], "period": key[3], "inv": v})
    return {
        "short": pd.DataFrame(rows_short), "served": pd.DataFrame(rows_served),
        "ship": pd.DataFrame(rows_ship), "prod": pd.DataFrame(rows_prod),
        "inv": pd.DataFrame(rows_inv),
    }


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    inst = build_instance("baseline")
    sol, V = build_and_solve(inst)
    print("status:", sol["status"], "| success:", sol["success"], "|", sol["message"])
    print("objective:", sol["objective"])
    print("vars:", sol["nvar"], "| eq:", sol["n_eq"], "| ub:", sol["n_ub"])
    f = solution_frames(sol, inst)
    tot_short = f["short"]["short"].sum() if len(f["short"]) else 0.0
    tot_demand = sum(inst.comp_demand.values())
    print(f"total demand (direct comps): {sum(v for (p,t),v in inst.comp_demand.items() if inst.group_of[p] in DIRECT_GROUPS):.0f}")
    print(f"total shortage: {tot_short:.2f}")
