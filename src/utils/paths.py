"""Central project paths for ResiliPlan AI.

Single source of truth for every directory the pipeline reads or writes, so no
script hard-codes an absolute path. Import `paths` and use the constants.
"""
from __future__ import annotations
from pathlib import Path

# .../Project/src/utils/paths.py  -> PROJECT_ROOT = .../Project
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data
DATA            = PROJECT_ROOT / "data"
RAW             = DATA / "raw"
RAW_XLSB        = RAW / "2020_dataset_OfAutomotiveProductionNetwork.xlsb"
CLEAN           = DATA / "clean"
DICTIONARY      = DATA / "dictionary"
ASSUMPTIONS     = DATA / "assumptions"
SCENARIOS       = DATA / "scenarios"

# Source
SRC             = PROJECT_ROOT / "src"

# Reports / outputs
REPORTS         = PROJECT_ROOT / "reports"
FIGURES         = REPORTS / "figures"
TABLES          = REPORTS / "tables"
FIGURE_INDEX    = REPORTS / "figure_index.md"
REPORT_DRAFT    = REPORTS / "report_draft.md"

RESULTS         = PROJECT_ROOT / "results"
LOGS            = RESULTS / "logs"

TESTS           = PROJECT_ROOT / "tests"

_ALL_DIRS = [DATA, RAW, CLEAN, DICTIONARY, ASSUMPTIONS, SCENARIOS,
             REPORTS, FIGURES, TABLES, RESULTS, LOGS, TESTS]


def ensure_dirs() -> None:
    """Create all standard output directories if missing (idempotent)."""
    for d in _ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# Create output dirs on import so utilities never fail on a missing folder.
ensure_dirs()
