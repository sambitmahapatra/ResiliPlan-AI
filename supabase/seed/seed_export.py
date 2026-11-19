"""Generate supabase/seed/seed.sql from the clean data + phase results.

Produces idempotent INSERT ... ON CONFLICT DO UPDATE statements for every reference and
precomputed table. Optionally pushes straight to Supabase (if SUPABASE_URL/KEY set) via
the REST upsert in app.api.supabase_client.

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -I D:\\SCA\\Project\\supabase\\seed\\seed_export.py            # writes seed.sql
  ... seed_export.py --push     # also upserts into Supabase
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

from app.api import data_access as da


def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (dict, list)):
        return "'" + json.dumps(v).replace("'", "''") + "'::jsonb"
    return "'" + str(v).replace("'", "''") + "'"


def insert_block(table: str, pk, rows: list[dict]) -> str:
    if not rows:
        return f"-- no rows for {table}\n"
    cols = list(rows[0].keys())
    pks = [pk] if isinstance(pk, str) else list(pk)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c not in pks)
    out = [f"-- {table} ({len(rows)} rows)"]
    values = ",\n  ".join("(" + ", ".join(sql_val(r[c]) for c in cols) + ")" for r in rows)
    out.append(f"insert into public.{table} ({', '.join(cols)}) values\n  {values}")
    conflict = ", ".join(pks)
    out.append(f"on conflict ({conflict}) do update set {updates};" if updates
               else f"on conflict ({conflict}) do nothing;")
    return "\n".join(out) + "\n"


def build_rows():
    net = da.get_network()
    nodes = net["nodes"]
    arcs = [{"starting_node_i": a["starting_node_i"], "ending_node_j": a["ending_node_j"],
             "group_g": a["group_g"], "lead_time": a["lead_time"],
             "exceeds_horizon": a["exceeds_horizon"]} for a in net["arcs"]]
    comps = da.get_criticality()
    scen = [{"id": s["id"], "name": s["name"], "nature": s["nature"],
             "managerial_question": s["managerial_question"], "modifications": s["modifications"],
             "is_synthetic": s["is_synthetic"]} for s in da.get_scenarios()]
    costs = []
    for c in da.get_cost_assumptions():
        costs.append({"parameter": c["parameter"], "scope": c.get("scope"),
                      "value": c.get("value"), "unit": c.get("unit"), "basis": c.get("basis"),
                      "sensitivity_low": c.get("sensitivity_low"),
                      "sensitivity_high": c.get("sensitivity_high"), "status": c.get("status", "ASSUMED")})
    results = da.scenario_result_rows()
    mc = da.get_precomputed_scenarios().get("monte_carlo", {})
    mc_row = [{"id": 1, "runs": mc.get("n"), "seed": mc.get("seed"),
               "service_mean": mc.get("service_mean"), "service_std": None,
               "service_min": mc.get("service_min"), "service_max": mc.get("service_max"),
               "battery_service_mean": None, "objective_mean": None}] if mc else []
    return nodes, arcs, comps, scen, costs, results, mc_row


def main(push: bool = False):
    nodes, arcs, comps, scen, costs, results, mc_row = build_rows()
    parts = ["-- ResiliPlan AI seed data (generated). Apply AFTER 0001_init.sql.",
             "begin;",
             insert_block("nodes", "node_n", nodes),
             insert_block("arcs", ("starting_node_i", "ending_node_j"), arcs),
             insert_block("components", "component_p", comps),
             insert_block("scenarios", "id", scen),
             insert_block("cost_assumptions", "parameter", costs),
             insert_block("scenario_results", "scenario_id", results),
             insert_block("monte_carlo_summary", "id", mc_row),
             "commit;"]
    out = Path(__file__).resolve().parent / "seed.sql"
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  nodes={len(nodes)} arcs={len(arcs)} components={len(comps)} scenarios={len(scen)} "
          f"cost_params={len(costs)} scenario_results={len(results)} mc={len(mc_row)}")

    if push:
        from app.api import supabase_client as sb
        if not sb.enabled():
            print("  --push requested but Supabase not configured (set SUPABASE_URL/KEY).")
            return
        for table, rows in [("nodes", nodes), ("arcs", arcs), ("components", comps),
                            ("scenarios", scen), ("cost_assumptions", costs),
                            ("scenario_results", results), ("monte_carlo_summary", mc_row)]:
            res = sb.upsert(table, rows)
            print(f"  push {table}: {res}")


if __name__ == "__main__":
    main(push="--push" in sys.argv)
