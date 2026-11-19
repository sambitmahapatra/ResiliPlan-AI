"""Solve service for the ResiliPlan API.

Wraps the P5/P6 model: accepts a saved scenario id or a custom config (+ optional cost
overrides), validates references, solves with HiGHS, validates balances independently,
and returns compact KPIs + manager-facing recommendations.
"""
from __future__ import annotations
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.model.instance import build_instance, build_instance_from_config, load_scenario
from src.model.milp import build_and_solve, solution_frames, DIRECT_GROUPS
from src.model.validate import validate_solution
from app.api.data_access import get_network, get_precomputed_scenarios

VALID_MODS = {"arc_capacity_multiplier", "arc_lead_time_delta", "car_demand_multiplier",
              "enable_expedite"}


def _valid_arcs() -> set:
    net = get_network()
    return {(a["starting_node_i"], a["ending_node_j"]) for a in net["arcs"]}


def validate_modifications(mods: dict) -> list[str]:
    """Return a list of human-readable errors (empty = valid)."""
    errors = []
    arcs = _valid_arcs()
    for key in mods:
        if key not in VALID_MODS:
            errors.append(f"unknown modification '{key}'")
    for m in mods.get("arc_capacity_multiplier", []):
        if tuple(m.get("arc", [])) not in arcs:
            errors.append(f"arc_capacity_multiplier references unknown arc {m.get('arc')}")
        if not (0 <= float(m.get("factor", -1))):
            errors.append("arc_capacity_multiplier.factor must be >= 0")
    for m in mods.get("arc_lead_time_delta", []):
        if tuple(m.get("arc", [])) not in arcs:
            errors.append(f"arc_lead_time_delta references unknown arc {m.get('arc')}")
    for m in mods.get("car_demand_multiplier", []):
        if float(m.get("factor", -1)) < 0:
            errors.append("car_demand_multiplier.factor must be >= 0")
    return errors


def _cost_breakdown(sol, inst) -> dict:
    C = inst.costs; pc = C["prod_cost"]; tb = C["transport_cost_base"]; tpl = C["transport_cost_per_lead_period"]
    hr = C["holding_rate_per_period"]; mult = C["expedite_multiplier"]; red = int(C["expedite_lead_reduction"])
    sp = C["shortage_penalty_car"]; g_of = inst.group_of; x = sol["x"]
    cp = sum(v * pc[g_of[k[1]]] for k, v in x.items() if k[0] == "prod")
    ct = sum(v * (tb + tpl * inst.lead[(k[2], k[3])]) for k, v in x.items() if k[0] == "ship")
    ce = sum(v * (tb + tpl * max(0, inst.lead[(k[2], k[3])] - red)) * mult for k, v in x.items() if k[0] == "eship")
    ch = sum(v * hr * pc[g_of[k[1]]] for k, v in x.items() if k[0] == "inv")
    cs = sum(v * sp for k, v in x.items() if k[0] == "short")
    return {"production": round(cp, 2), "transport": round(ct + ce, 2), "expedite": round(ce, 2),
            "holding": round(ch, 2), "shortage": round(cs, 2)}


def _service(sol, inst) -> dict:
    g_of = inst.group_of
    dem, short = {}, {}
    for (p, t), v in inst.comp_demand.items():
        if g_of[p] in DIRECT_GROUPS:
            dem[g_of[p]] = dem.get(g_of[p], 0.0) + v
    for k, v in sol["x"].items():
        if k[0] == "short":
            short[g_of[k[1]]] = short.get(g_of[k[1]], 0.0) + v
    tot_d = sum(dem.values()); tot_s = sum(short.values())
    by_g = {g: round(100 * (1 - short.get(g, 0.0) / d), 2) if d else 100.0 for g, d in dem.items()}
    return {"overall_pct": round(100 * (1 - tot_s / tot_d), 2) if tot_d else 100.0,
            "by_group": by_g, "total_demand": round(tot_d, 2), "total_shortage": round(tot_s, 2)}


def _recommendations(service, cost, expedite_units, vs_baseline) -> list[str]:
    recs = []
    bsvc = service["by_group"].get("battery", 100.0)
    if bsvc < 70:
        recs.append(f"Battery is the binding constraint (service {bsvc:.0f}%). Root cause is the "
                    f"upstream battery sub-component pipeline whose lead time (20) exceeds the "
                    f"14-period horizon — it cannot be replenished in-plan. Pre-position battery "
                    f"inventory before the horizon or expedite inbound freight.")
    for g, s in service["by_group"].items():
        if g != "battery" and s < 95:
            recs.append(f"{g.capitalize()} service is {s:.0f}% — review inbound arc capacity/lead "
                        f"time for the {g} chain.")
    if expedite_units and expedite_units > 0:
        recs.append(f"Expedited freight was used ({expedite_units:.0f} units). Under the ASSUMED "
                    f"shortage penalty it improves service and can lower total cost because avoided "
                    f"shortage outweighs the premium — validate the penalty assumption before acting.")
    if vs_baseline is not None:
        dc = vs_baseline.get("delta_cost_mu")
        ds = vs_baseline.get("delta_service_pp")
        if dc is not None:
            recs.append(f"Versus baseline: cost {'+' if dc>=0 else ''}{dc:,.0f} MU, "
                        f"service {'+' if (ds or 0)>=0 else ''}{ds:.1f} pp.")
    recs.append("All monetary figures use ASSUMED cost parameters (the source data has no costs); "
                "treat absolute MU as relative, not actual currency.")
    return recs


def solve(scenario_id: str | None = "baseline", modifications: dict | None = None,
          cost_overrides: dict | None = None, detail: bool = False) -> dict:
    """Run the optimizer. Either a saved scenario_id, or custom modifications (id ignored).

    Returns a compact result dict. Raises ValueError on invalid modifications."""
    t0 = time.time()
    if modifications is not None:
        errs = validate_modifications(modifications)
        if errs:
            raise ValueError("; ".join(errs))
        cfg = {"id": scenario_id or "custom", "name": "Custom scenario",
               "nature": "custom", "modifications": modifications}
        inst = build_instance_from_config(cfg)
        is_custom = True
    else:
        inst = build_instance(scenario_id or "baseline")
        is_custom = False

    if cost_overrides:
        merged = dict(inst.costs)
        for k, v in cost_overrides.items():
            merged[k] = v
        inst.costs = merged

    sol, V = build_and_solve(inst)
    chk = validate_solution(sol, inst)
    cost = _cost_breakdown(sol, inst)
    service = _service(sol, inst)
    f = solution_frames(sol, inst)
    exp_units = 0.0
    if len(f["ship"]) and "expedited" in f["ship"].columns:
        exp_units = float(f["ship"][f["ship"]["expedited"] == True]["qty"].sum())

    # baseline comparison (use precomputed baseline if available)
    vs_baseline = None
    pre = get_precomputed_scenarios()
    base_obj = pre.get("baseline_objective")
    base_svc = next((s["service"]["overall"] for s in pre.get("scenarios", [])
                     if s["scenario"] == "baseline"), None)
    if base_obj is not None and (scenario_id != "baseline" or is_custom):
        vs_baseline = {"delta_cost_mu": round(sol["objective"] - base_obj, 2),
                       "delta_service_pp": round(service["overall_pct"] - (base_svc or service["overall_pct"]), 2)}

    result = {
        "scenario_id": inst.scenario_id, "is_custom": is_custom,
        "scenario_name": inst.meta.get("scenario_name") or "Custom scenario",
        "status": "optimal" if sol["status"] == 0 else "non-optimal",
        "status_message": sol["message"],
        "objective_mu": round(sol["objective"], 2) if sol["objective"] is not None else None,
        "cost_breakdown": cost, "service": service,
        "expedite_units": round(exp_units, 2),
        "validation": {"all_ok": bool(chk["all_ok"]),
                       "max_balance_residual": float(chk["max_balance_residual"]),
                       "max_capacity_violation": float(chk["max_capacity_violation"])},
        "model_size": {"variables": sol["nvar"], "equality_constraints": sol["n_eq"],
                       "capacity_constraints": sol["n_ub"]},
        "vs_baseline": vs_baseline,
        "recommendations": _recommendations(service, cost, exp_units, vs_baseline),
        "solve_seconds": round(time.time() - t0, 3),
        "assumptions_note": "Costs and disruptions are ASSUMED/synthetic (source data has no cost "
                            "or probability data). Service is lost-sales (no backorder).",
    }
    if detail:
        result["plan"] = {
            "shortage_by_component_period": f["short"].to_dict("records") if len(f["short"]) else [],
            "shipments": f["ship"].to_dict("records") if len(f["ship"]) else [],
        }
    return result
