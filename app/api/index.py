"""ResiliPlan AI — backend API (FastAPI).

Run locally:
  cd D:\\SCA\\Project
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe -m uvicorn app.api.index:app --reload --port 8000
Docs at http://localhost:8000/docs

Deploy: Vercel Python runtime serves this module's `app` (see vercel.json).
Reads clean data from the repo; writes runs to Supabase when SUPABASE_URL/KEY are set.
"""
from __future__ import annotations
import io
import csv
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from app.api import data_access as da
from app.api import model_service as ms
from app.api import supabase_client as sb
from app.api.schemas import SolveRequest

app = FastAPI(
    title="ResiliPlan AI API",
    version="1.0.0",
    description="Prescriptive supply-chain optimization backend. Reference data + an "
                "on-demand HiGHS solve. All costs/disruptions are ASSUMED/synthetic.",
)

# CORS — allow the frontend (Vercel/localhost). Set ALLOWED_ORIGINS (comma-sep) to restrict.
_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _origins == "*" else [o.strip() for o in _origins.split(",")],
    allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Meta
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "resiliplan-api", "version": "1.0.0",
            "supabase_configured": sb.enabled()}


# --------------------------------------------------------------------------- #
# Reference data (frontend may also read these straight from Supabase)
# --------------------------------------------------------------------------- #
@app.get("/api/network")
def network():
    return da.get_network()


@app.get("/api/criticality")
def criticality():
    return {"components": da.get_criticality()}


@app.get("/api/scenarios")
def scenarios():
    return {"scenarios": da.get_scenarios()}


@app.get("/api/scenarios/results")
def scenario_results():
    """Precomputed baseline + 6-scenario comparison (no solve needed)."""
    return {"results": da.scenario_result_rows(),
            "baseline_objective": da.get_precomputed_scenarios().get("baseline_objective")}


@app.get("/api/cost-assumptions")
def cost_assumptions():
    return {"status": "ASSUMED (source workbook has no cost data)",
            "parameters": da.get_cost_assumptions()}


@app.get("/api/monte-carlo")
def monte_carlo():
    return da.get_precomputed_scenarios().get("monte_carlo", {})


@app.get("/api/data/summary")
def data_summary():
    """Real source-table catalog + validation status for Data Studio."""
    return da.get_data_summary()


# --------------------------------------------------------------------------- #
# Solve
# --------------------------------------------------------------------------- #
@app.post("/api/solve")
def solve(req: SolveRequest):
    try:
        result = ms.solve(scenario_id=req.scenario_id, modifications=req.modifications,
                          cost_overrides=req.cost_overrides, detail=req.detail)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"solve failed: {e}")

    result["persisted"] = None
    if req.persist and sb.enabled():
        row = {
            "scenario_id": None if result["is_custom"] else result["scenario_id"],
            "is_custom": result["is_custom"],
            "params": {"modifications": req.modifications, "cost_overrides": req.cost_overrides},
            "status": result["status"], "objective_mu": result["objective_mu"],
            "service_overall_pct": result["service"]["overall_pct"],
            "battery_service_pct": result["service"]["by_group"].get("battery"),
            "total_shortage": result["service"]["total_shortage"],
            "expedite_units": result["expedite_units"],
            "cost_breakdown": result["cost_breakdown"],
            "service_by_group": result["service"]["by_group"],
            "validation": result["validation"], "recommendations": result["recommendations"],
            "solve_seconds": result["solve_seconds"], "created_by": req.created_by,
        }
        result["persisted"] = sb.insert_run(row)
    return result


# --------------------------------------------------------------------------- #
# Run history
# --------------------------------------------------------------------------- #
@app.get("/api/runs")
def runs(limit: int = Query(50, ge=1, le=200)):
    if not sb.enabled():
        return {"runs": [], "note": "Supabase not configured; run history is unavailable."}
    return {"runs": sb.list_runs(limit)}


# --------------------------------------------------------------------------- #
# CSV export (manager download)
# --------------------------------------------------------------------------- #
@app.get("/api/export/scenario-comparison.csv")
def export_scenario_comparison():
    rows = da.scenario_result_rows()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["scenario_id", "status", "objective_mu", "vs_baseline_mu",
                "service_overall_pct", "battery_service_pct", "total_shortage", "expedite_units"])
    for r in rows:
        w.writerow([r["scenario_id"], r["status"], r["objective_mu"], r["vs_baseline_mu"],
                    r["service_overall_pct"], r["battery_service_pct"], r["total_shortage"],
                    r["expedite_units"]])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=scenario_comparison.csv"})


@app.post("/api/export/solve.csv")
def export_solve(req: SolveRequest):
    try:
        result = ms.solve(scenario_id=req.scenario_id, modifications=req.modifications,
                          cost_overrides=req.cost_overrides, detail=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["metric", "value"])
    w.writerow(["scenario", result["scenario_name"]])
    w.writerow(["status", result["status"]])
    w.writerow(["objective_mu", result["objective_mu"]])
    for k, v in result["cost_breakdown"].items():
        w.writerow([f"cost_{k}", v])
    w.writerow(["service_overall_pct", result["service"]["overall_pct"]])
    for g, s in result["service"]["by_group"].items():
        w.writerow([f"service_{g}_pct", s])
    w.writerow(["total_shortage", result["service"]["total_shortage"]])
    w.writerow(["expedite_units", result["expedite_units"]])
    w.writerow(["validated", result["validation"]["all_ok"]])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=solve_result.csv"})


# local dev entrypoint
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.index:app", host="127.0.0.1", port=8000, reload=False)
