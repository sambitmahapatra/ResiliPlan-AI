"""Deterministic seeding for reproducibility (CLAUDE.md rule #6)."""
from __future__ import annotations

SEED = 42


def set_seeds(seed: int = SEED) -> int:
    """Seed Python's `random` and NumPy. Returns the seed used."""
    import random
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    return seed
