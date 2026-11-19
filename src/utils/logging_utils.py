"""Consistent run logging to console + results/logs/ (CLAUDE.md §7)."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from . import paths


def get_logger(name: str, to_file: bool = True) -> logging.Logger:
    """Return a configured logger that writes to console and (optionally) a file
    under results/logs/<name>.log. Idempotent: won't add duplicate handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if to_file:
        paths.LOGS.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(paths.LOGS / f"{name}.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    logger.propagate = False
    logger.info("logger started (UTC %s)", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return logger
