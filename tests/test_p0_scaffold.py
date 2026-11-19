"""P0 / Gate G0 self-test (plain runnable script; no pytest needed).

Verifies:
  1. Shared utilities import.
  2. Raw workbook is present and readable (read-only) and matches audited counts.
  3. save_fig writes a PNG and registers it in figure_index.md.
  4. save_table_image writes a PNG + backing CSV.
  5. The SOLVER (scipy.optimize.milp, HiGHS engine) solves a test MILP to optimality.

Run:
  C:\\Users\\sambi\\miniconda3\\envs\\myenv\\python.exe D:\\SCA\\Project\\tests\\test_p0_scaffold.py
Exit code 0 == G0 technical checks pass.
"""
from __future__ import annotations
import sys
from pathlib import Path

# make `src` importable when run as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import matplotlib.pyplot as plt

from src.utils import (paths, save_fig, save_table_image, remove_figure, get_logger,
                       SEED, set_seeds, read_raw)

log = get_logger("p0_selftest")
failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        log.info("PASS  %s", msg)
    else:
        log.error("FAIL  %s", msg)
        failures.append(msg)


# 1. seeding
check(set_seeds() == SEED, "set_seeds returns SEED")

# 2. raw workbook present + audited counts reproduce
check(paths.RAW_XLSB.exists(), f"raw workbook present at {paths.RAW_XLSB}")
prod = read_raw("products"); bom = read_raw("BOM"); nodes = read_raw("nodes")
arcs = read_raw("arcs"); dem = read_raw("demands")
check(prod.shape == (28049, 3), f"products shape 28049x3 (got {prod.shape})")
check(bom.shape == (87059, 3), f"BOM shape 87059x3 (got {bom.shape})")
check(len(nodes) == 12, f"12 nodes (got {len(nodes)})")
check(len(arcs) == 11, f"11 arcs (got {len(arcs)})")
check(bom["child"].astype(str).nunique() == 49, "49 distinct BOM components")
check(int(dem["period_t"].min()) == 61 and int(dem["period_t"].max()) == 74, "demand periods 61-74")

# 3. save_fig
fig, ax = plt.subplots(figsize=(5, 3))
ax.plot([61, 62, 63], [2000, 2000, 2000], marker="o")
ax.set_title("P0 self-test figure"); ax.set_xlabel("period"); ax.set_ylabel("demand rows")
p = save_fig(fig, "p0_selftest", "P0 scaffold self-test figure (disposable)", phase="P0")
plt.close(fig)
check(p.exists(), f"save_fig wrote PNG at {p}")
check(paths.FIGURE_INDEX.exists() and "p0_selftest" in paths.FIGURE_INDEX.read_text(encoding="utf-8"),
      "figure registered in figure_index.md")

# 4. save_table_image
grp = prod["group_g"].value_counts().rename_axis("group_g").to_frame("n_products")
pt = save_table_image(grp, "p0_selftest_table", "P0 self-test table (product groups)", phase="P0")
check(pt.exists(), f"save_table_image wrote PNG at {pt}")
check((paths.TABLES / "p0_selftest_table.csv").exists(), "backing CSV written for table image")

# 5. SOLVER smoke: maximize 3x+2y s.t. x+y<=10, x<=6, y integer -> x=6,y=4,obj=26
from scipy.optimize import milp, LinearConstraint, Bounds
res = milp(c=np.array([-3.0, -2.0]),
           constraints=LinearConstraint(np.array([[1., 1.], [1., 0.]]), ub=np.array([10., 6.])),
           integrality=np.array([0, 1]),
           bounds=Bounds(lb=np.array([0., 0.]), ub=np.array([np.inf, np.inf])))
check(res.success and abs((-res.fun) - 26.0) < 1e-6 and abs(res.x[0] - 6) < 1e-6 and abs(res.x[1] - 4) < 1e-6,
      f"scipy.optimize.milp (HiGHS) optimal: x={res.x}, obj={-res.fun} (expect 6,4,26)")

# 6. cleanup: dispose of the self-test's throwaway artifacts so the deliverable
#    reports/ tree and figure_index.md list only genuine report figures.
remove_figure("p0_selftest")
remove_figure("p0_selftest_table")
idx_txt = paths.FIGURE_INDEX.read_text(encoding="utf-8") if paths.FIGURE_INDEX.exists() else ""
check("p0_selftest" not in idx_txt, "self-test disposables removed from figure_index.md")
check(not (paths.FIGURES / "p0_selftest.png").exists(), "disposable figure PNG cleaned up")

print("\n" + ("=" * 60))
if failures:
    print(f"G0 SELF-TEST: {len(failures)} FAILURE(S)")
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("G0 SELF-TEST: ALL CHECKS PASSED")
sys.exit(0)
