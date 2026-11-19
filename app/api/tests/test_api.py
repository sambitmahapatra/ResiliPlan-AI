"""API smoke/integration test (plain runnable script; uses FastAPI TestClient).

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe D:\\SCA\\Project\\app\\api\\tests\\test_api.py
Exit 0 == all endpoints work. Does not require Supabase (persistence is skipped/none).
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from fastapi.testclient import TestClient
from app.api.index import app

client = TestClient(app)
fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

# health
r = client.get("/api/health"); j = r.json()
check(r.status_code == 200 and j["status"] == "ok", "GET /api/health")

# network
r = client.get("/api/network"); j = r.json()
check(r.status_code == 200 and len(j["nodes"]) == 12 and len(j["arcs"]) == 11, "GET /api/network (12 nodes, 11 arcs)")
check(any(a["exceeds_horizon"] for a in j["arcs"]), "network flags long-lead arcs")

# criticality
r = client.get("/api/criticality"); j = r.json()
check(r.status_code == 200 and len(j["components"]) == 49, "GET /api/criticality (49 components)")

# scenarios
r = client.get("/api/scenarios"); j = r.json()
check(r.status_code == 200 and len(j["scenarios"]) == 6, "GET /api/scenarios (6)")

# precomputed results
r = client.get("/api/scenarios/results"); j = r.json()
check(r.status_code == 200 and len(j["results"]) == 6, "GET /api/scenarios/results (6)")

# cost assumptions
r = client.get("/api/cost-assumptions"); j = r.json()
check(r.status_code == 200 and len(j["parameters"]) == 13 and all(p["status"] == "ASSUMED" for p in j["parameters"]),
      "GET /api/cost-assumptions (13, all ASSUMED)")

# monte carlo
r = client.get("/api/monte-carlo"); j = r.json()
check(r.status_code == 200 and "service_mean" in j, "GET /api/monte-carlo")

# solve baseline
r = client.post("/api/solve", json={"scenario_id": "baseline", "persist": False})
j = r.json()
check(r.status_code == 200 and j["status"] == "optimal" and abs(j["objective_mu"] - 18395031) < 1,
      f"POST /api/solve baseline optimal obj=18,395,031 (got {j.get('objective_mu')})")
check(j["validation"]["all_ok"] and j["validation"]["max_balance_residual"] < 1e-4, "solve validation all_ok")
check(len(j["recommendations"]) >= 1, "solve returns recommendations")

# solve emergency (expedite)
r = client.post("/api/solve", json={"scenario_id": "emergency_response", "persist": False})
j = r.json()
check(r.status_code == 200 and j["expedite_units"] > 0, "POST /api/solve emergency uses expedite")
check(j["service"]["by_group"]["battery"] > 55, "emergency lifts battery service")

# solve CUSTOM scenario
r = client.post("/api/solve", json={"modifications": {"car_demand_multiplier": [{"periods": [66, 67, 68], "factor": 1.3}]}, "persist": False})
j = r.json()
check(r.status_code == 200 and j["is_custom"] and j["status"] == "optimal", "POST /api/solve custom scenario")

# invalid modification -> 422
r = client.post("/api/solve", json={"modifications": {"arc_capacity_multiplier": [{"arc": ["bad", "arc"], "factor": 0.5}]}, "persist": False})
check(r.status_code == 422, "POST /api/solve invalid arc -> 422")

# runs (no supabase)
r = client.get("/api/runs"); check(r.status_code == 200, "GET /api/runs")

# csv exports
r = client.get("/api/export/scenario-comparison.csv")
check(r.status_code == 200 and "scenario_id" in r.text and "text/csv" in r.headers["content-type"],
      "GET scenario-comparison.csv")
r = client.post("/api/export/solve.csv", json={"scenario_id": "baseline"})
check(r.status_code == 200 and "objective_mu" in r.text, "POST solve.csv")

print("\n" + "=" * 56)
if fails:
    print(f"API TEST: {len(fails)} FAILURE(S)"); sys.exit(1)
print("API TEST: ALL CHECKS PASSED"); sys.exit(0)
