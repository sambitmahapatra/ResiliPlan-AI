"""Figure & table-as-image saving for ResiliPlan AI.

OWNER REQUIREMENT (CLAUDE.md rule #3): every chart, plot, diagram, and results
table bound for the report MUST be written as a PNG into reports/figures/ and
registered in reports/figure_index.md. Use these helpers everywhere; if a result
did not pass through here, it does not count as done.

Public API
----------
save_fig(fig, name, caption, phase, dpi=150) -> Path
save_table_image(df, name, caption, phase, max_rows=40, float_fmt="{:,.3g}") -> Path
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
matplotlib.use("Agg")  # headless; never try to open a window
import matplotlib.pyplot as plt

from . import paths

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

_INDEX_HEADER = (
    "# Figure Index — ResiliPlan AI\n\n"
    "Every report-bound figure and table-as-image is registered here automatically "
    "by `src/utils/figures.py`. Do not edit by hand.\n\n"
    "| name | caption | phase | source | saved (UTC) |\n"
    "|---|---|---|---|---|\n"
)


def _source_script() -> str:
    s = sys.argv[0] if sys.argv and sys.argv[0] else ""
    return Path(s).name if s else "interactive"


def _esc(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _update_index(name: str, caption: str, phase: str, source: str) -> None:
    """Insert/replace the row for `name` in figure_index.md, keeping rows sorted."""
    paths.REPORTS.mkdir(parents=True, exist_ok=True)
    idx = paths.FIGURE_INDEX
    rows: dict[str, str] = {}
    if idx.exists():
        for line in idx.read_text(encoding="utf-8").splitlines():
            ls = line.strip()
            if ls.startswith("|") and not ls.startswith("| name") and not set(ls) <= set("|- "):
                cells = [c.strip() for c in ls.strip("|").split("|")]
                if cells:
                    rows[cells[0]] = line
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rows[name] = f"| {_esc(name)} | {_esc(caption)} | {_esc(phase)} | {_esc(source)} | {utc} |"
    body = "\n".join(rows[k] for k in sorted(rows))
    idx.write_text(_INDEX_HEADER + body + "\n", encoding="utf-8")


def remove_figure(name: str) -> None:
    """Delete a figure's PNG, its backing table CSV (if any), and its index row.

    Use for disposable/self-test artifacts so the deliverable figure_index.md and
    reports/ tree list only genuine report figures."""
    name = name.strip().replace(" ", "_")
    (paths.FIGURES / f"{name}.png").unlink(missing_ok=True)
    (paths.TABLES / f"{name}.csv").unlink(missing_ok=True)
    idx = paths.FIGURE_INDEX
    if not idx.exists():
        return
    rows: dict[str, str] = {}
    for line in idx.read_text(encoding="utf-8").splitlines():
        ls = line.strip()
        if ls.startswith("|") and not ls.startswith("| name") and not set(ls) <= set("|- "):
            cells = [c.strip() for c in ls.strip("|").split("|")]
            if cells and cells[0] != name:
                rows[cells[0]] = line
    body = "\n".join(rows[k] for k in sorted(rows))
    idx.write_text(_INDEX_HEADER + body + ("\n" if body else ""), encoding="utf-8")


def save_fig(fig, name: str, caption: str, phase: str, dpi: int = 150) -> Path:
    """Save a matplotlib Figure as reports/figures/<name>.png and index it.

    Returns the PNG path. Does NOT close the figure (caller decides)."""
    paths.FIGURES.mkdir(parents=True, exist_ok=True)
    name = name.strip().replace(" ", "_")
    out = paths.FIGURES / f"{name}.png"
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    _update_index(name, caption, phase, _source_script())
    return out


def save_table_image(df, name: str, caption: str, phase: str,
                     max_rows: int = 40, float_fmt: str = "{:,.3g}") -> Path:
    """Render a pandas DataFrame to a PNG table (for the report) AND write the full
    backing data to reports/tables/<name>.csv. Returns the PNG path.

    Only the first `max_rows` rows are drawn (with a footnote) so the image stays
    legible; the CSV always holds the complete table.
    """
    import pandas as pd  # local import keeps util import light

    name = name.strip().replace(" ", "_")
    paths.TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(paths.TABLES / f"{name}.csv", index=True)

    shown = df.head(max_rows).copy()
    # pretty-format floats
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]):
            shown[col] = shown[col].map(lambda v: "" if pd.isna(v) else float_fmt.format(v))
    shown = shown.astype(str)

    n_cols = max(len(shown.columns) + 1, 1)
    n_rows = len(shown) + 1
    fig_w = min(max(2.2 * n_cols, 6), 22)
    fig_h = min(max(0.45 * n_rows + 1.1, 2), 26)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")
    ax.set_title(caption, fontsize=12, fontweight="bold", pad=12, loc="left", wrap=True)

    tbl = ax.table(
        cellText=shown.values,
        colLabels=[str(c) for c in shown.columns],
        rowLabels=[str(i) for i in shown.index],
        cellLoc="center", rowLoc="center", loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.3)
    for (r, _c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1f2d3d"); cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f2f5f8")

    if len(df) > max_rows:
        fig.text(0.01, 0.005, f"Showing {max_rows} of {len(df)} rows — full table in "
                              f"reports/tables/{name}.csv", fontsize=8, style="italic")

    out = save_fig(fig, name, caption, phase)
    plt.close(fig)
    return out
