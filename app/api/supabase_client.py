"""Optional Supabase persistence via the PostgREST API (pure httpx — no native deps).

Disabled unless SUPABASE_URL and a key are set in the environment, so the API runs fully
without a database (compute still works; runs just aren't stored). All calls are fail-safe:
errors are swallowed and reported in the return value, never raised to the request.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

import httpx


def _load_dotenv() -> None:
    """Load app/api/.env into os.environ if present (no python-dotenv dependency).

    Keeps Supabase keys in a gitignored file instead of the shell/repo. Existing
    environment variables take precedence over .env values."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)
    except Exception:
        pass


_load_dotenv()

URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
# Tolerate a URL that already includes the PostgREST path (common copy/paste): we append
# /rest/v1 ourselves, so strip a trailing /rest/v1 if present.
if URL.endswith("/rest/v1"):
    URL = URL[: -len("/rest/v1")]
KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")


def enabled() -> bool:
    return bool(URL and KEY)


def _headers() -> dict:
    return {"apikey": KEY, "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json", "Prefer": "return=representation"}


def insert_run(row: dict) -> dict:
    """Insert one optimization_runs row. Returns {ok, id|error}."""
    if not enabled():
        return {"ok": False, "error": "supabase not configured"}
    try:
        with httpx.Client(timeout=10) as c:
            r = c.post(f"{URL}/rest/v1/optimization_runs", headers=_headers(), json=row)
        if r.status_code in (200, 201):
            data = r.json()
            return {"ok": True, "id": (data[0]["id"] if isinstance(data, list) and data else None)}
        return {"ok": False, "error": f"{r.status_code}: {r.text[:200]}"}
    except Exception as e:  # never break the request over persistence
        return {"ok": False, "error": str(e)[:200]}


def list_runs(limit: int = 50) -> list[dict]:
    if not enabled():
        return []
    try:
        with httpx.Client(timeout=10) as c:
            r = c.get(f"{URL}/rest/v1/optimization_runs",
                      headers=_headers(),
                      params={"select": "*", "order": "created_at.desc", "limit": str(limit)})
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def upsert(table: str, rows: list[dict]) -> dict:
    """Upsert rows into a reference table (used by the seed loader)."""
    if not enabled():
        return {"ok": False, "error": "supabase not configured"}
    try:
        headers = _headers() | {"Prefer": "resolution=merge-duplicates,return=minimal"}
        with httpx.Client(timeout=30) as c:
            r = c.post(f"{URL}/rest/v1/{table}", headers=headers, json=rows)
        return {"ok": r.status_code in (200, 201, 204), "status": r.status_code, "text": r.text[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
