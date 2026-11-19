"""Data IO helpers: read the read-only raw workbook, and version clean tables.

The raw .xlsb is NEVER modified (CLAUDE.md rule #4). All cleaned outputs are
versioned CSVs under data/clean/ as <name>.v<version>.csv.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path

import pandas as pd

from . import paths

RAW_SHEETS = [
    "products", "nodes", "nodes_inflow", "arcs", "capacity_at_arc",
    "max_flow_product_per_arc", "max_flow_group_per_arc", "operations",
    "BOM", "demands", "initial_inventories", "initial_flows",
]


@lru_cache(maxsize=None)
def read_raw(sheet: str) -> pd.DataFrame:
    """Read one sheet from the read-only raw .xlsb (cached)."""
    if sheet not in RAW_SHEETS:
        raise ValueError(f"unknown raw sheet {sheet!r}; expected one of {RAW_SHEETS}")
    return pd.read_excel(paths.RAW_XLSB, sheet_name=sheet, engine="pyxlsb")


def read_all_raw() -> dict[str, pd.DataFrame]:
    """Read every raw sheet into a dict {sheet: DataFrame}."""
    return {s: read_raw(s) for s in RAW_SHEETS}


def clean_path(name: str, version: int = 1) -> Path:
    return paths.CLEAN / f"{name}.v{version}.csv"


def save_clean(df: pd.DataFrame, name: str, version: int = 1, index: bool = False) -> Path:
    """Write a cleaned, versioned CSV to data/clean/."""
    paths.CLEAN.mkdir(parents=True, exist_ok=True)
    out = clean_path(name, version)
    df.to_csv(out, index=index)
    return out


def read_clean(name: str, version: int = 1) -> pd.DataFrame:
    return pd.read_csv(clean_path(name, version))
