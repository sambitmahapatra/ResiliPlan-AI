// Typed client for the ResiliPlan FastAPI backend. All shapes mirror app/api/README.md.
const BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} on ${path}`);
  return r.json() as Promise<T>;
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let detail = `${r.status} ${r.statusText}`;
    try {
      const j = await r.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return r.json() as Promise<T>;
}

// ---- types ----
export interface Health { status: string; service: string; version: string; supabase_configured: boolean; }
export interface NodeRow { node_n: string; family: string; role: string; echelon_level: number | null; }
export interface ArcRow { starting_node_i: string; ending_node_j: string; group_g: string; lead_time: number; exceeds_horizon: boolean; }
export interface Network { nodes: NodeRow[]; arcs: ArcRow[]; }
export interface Component {
  component_p: string; group_g: string; origin_node: string | null;
  n_cars_using: number | null; pct_configs_dependent: number | null;
  gross_demand_total: number | null; cum_lead_time: number | null;
  risk_score: number | null; is_direct_car_component: boolean;
}
export interface Scenario { id: string; name: string; nature: string; managerial_question: string; modifications: Record<string, unknown>; is_synthetic: boolean; }
export interface ScenarioResult {
  scenario_id: string; status: string; objective_mu: number; vs_baseline_mu: number;
  service_overall_pct: number; battery_service_pct: number; total_shortage: number;
  expedite_units: number; cost_breakdown: Record<string, number>; service_by_group: Record<string, number>; validated: boolean;
}
export interface CostParam { status: string; parameter: string; scope: string; value: number; unit: string; basis: string; sensitivity_low: number; sensitivity_high: number; }
export interface MonteCarlo { n?: number; seed?: number; service_mean?: number; service_min?: number; service_max?: number; }
export interface DataSummary {
  source_file: string; source_format: string; worksheets: number; horizon: string; status: string;
  tables: { table: string; rows: number | null; description: string; role: string }[];
  validation: Record<string, unknown>;
}
export interface SolveRequest {
  scenario_id?: string;
  modifications?: Record<string, unknown>;
  cost_overrides?: Record<string, number>;
  detail?: boolean;
  persist?: boolean;
}
export interface SolveResult {
  scenario_id: string; is_custom: boolean; scenario_name: string;
  status: string; status_message: string; objective_mu: number | null;
  cost_breakdown: Record<string, number>;
  service: { overall_pct: number; by_group: Record<string, number>; total_demand: number; total_shortage: number };
  expedite_units: number;
  validation: { all_ok: boolean; max_balance_residual: number; max_capacity_violation: number };
  model_size: { variables: number; equality_constraints: number; capacity_constraints: number };
  vs_baseline: { delta_cost_mu: number; delta_service_pp: number } | null;
  recommendations: string[];
  solve_seconds: number;
  assumptions_note: string;
  persisted?: { ok: boolean; id?: string } | null;
  plan?: { shortage_by_component_period: any[]; shipments: any[] };
}
export interface RunRow { id: string; scenario_id: string | null; status: string; objective_mu: number; service_overall_pct: number; created_at: string; }
export interface TablePreview { table: string; columns: string[]; rows: (string | number | null)[][]; preview_rows: number; total_rows: number | null; }

export const api = {
  health: () => get<Health>("/api/health"),
  network: () => get<Network>("/api/network"),
  criticality: () => get<{ components: Component[] }>("/api/criticality"),
  scenarios: () => get<{ scenarios: Scenario[] }>("/api/scenarios"),
  scenarioResults: () => get<{ results: ScenarioResult[]; baseline_objective: number }>("/api/scenarios/results"),
  costAssumptions: () => get<{ status: string; parameters: CostParam[] }>("/api/cost-assumptions"),
  monteCarlo: () => get<MonteCarlo>("/api/monte-carlo"),
  dataSummary: () => get<DataSummary>("/api/data/summary"),
  dataPreview: (table: string, limit = 8) => get<TablePreview>(`/api/data/preview?table=${encodeURIComponent(table)}&limit=${limit}`),
  runs: () => get<{ runs: RunRow[]; note?: string }>("/api/runs"),
  solve: (body: SolveRequest) => post<SolveResult>("/api/solve", body),
  exportScenarioCsvUrl: () => `${BASE}/api/export/scenario-comparison.csv`,
};
