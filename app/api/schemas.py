"""Pydantic request models for the ResiliPlan API."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    scenario_id: Optional[str] = Field(
        default="baseline",
        description="Saved scenario id (baseline, supplier_disruption, material_delay, "
                    "demand_surge, transport_constraint, emergency_response). Ignored "
                    "when 'modifications' is provided (then it labels the custom run).")
    modifications: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom disruption config. Keys: arc_capacity_multiplier, "
                    "arc_lead_time_delta, car_demand_multiplier (lists of {arc/periods, "
                    "factor/delta_periods}), enable_expedite (bool).")
    cost_overrides: Optional[dict[str, Any]] = Field(
        default=None, description="Override ASSUMED cost params (e.g. shortage_penalty_car).")
    detail: bool = Field(default=False, description="Include the full plan (flows/shortages).")
    persist: bool = Field(default=True, description="Store the run in Supabase if configured.")
    created_by: str = Field(default="anon")
