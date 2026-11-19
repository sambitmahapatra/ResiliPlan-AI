import { useEffect, useState } from "react";
import { api, type SolveResult, type ScenarioResult, type Scenario } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { Raw, compareBars } from "../lib/charts";
import { mu, pct, titleCase } from "../lib/format";

interface Draft { demandSurge: number; gearDelay: number; batteryCapCut: number; expedite: boolean; }
const ZERO: Draft = { demandSurge: 0, gearDelay: 0, batteryCapCut: 0, expedite: false };

function buildMods(d: Draft): Record<string, unknown> {
  const m: Record<string, unknown> = {};
  if (d.demandSurge > 0) m.car_demand_multiplier = [{ periods: [66, 67, 68], factor: 1 + d.demandSurge / 100 }];
  if (d.gearDelay > 0) m.arc_lead_time_delta = [{ arc: ["gear-supplier_inv", "zp7"], delta_periods: d.gearDelay, periods: "all" }];
  if (d.batteryCapCut > 0) m.arc_capacity_multiplier = [{ arc: ["battery-supplier_prod", "battery-supplier_inv"], factor: 1 - d.batteryCapCut / 100, periods: [64, 65, 66, 67] }];
  if (d.expedite) m.enable_expedite = true;
  return m;
}

export default function Scenarios() {
  const scenarios = useApi<{ scenarios: Scenario[] }>(() => api.scenarios(), []);
  const results = useApi<{ results: ScenarioResult[] }>(() => api.scenarioResults(), []);
  const baseline = results.data?.results.find((r) => r.scenario_id === "baseline");

  const [draft, setDraft] = useState<Draft>(ZERO);
  const [presetId, setPresetId] = useState<string | null>("baseline");
  const [result, setResult] = useState<SolveResult | null>(null);
  const [solving, setSolving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);

  async function run() {
    setSolving(true); setError(null);
    try {
      const body = presetId ? { scenario_id: presetId } : { scenario_id: "custom", modifications: buildMods(draft) };
      const res = await api.solve({ ...body, persist: true });
      setResult(res); setDirty(false);
    } catch (e: any) { setError(e?.message || "Solve failed"); }
    finally { setSolving(false); }
  }
  // auto-run baseline once on mount
  useEffect(() => { run(); /* eslint-disable-next-line */ }, []);

  const setLever = (patch: Partial<Draft>) => { setDraft((d) => ({ ...d, ...patch })); setPresetId(null); setDirty(true); };
  const choosePreset = (id: string) => { setPresetId(id); setDraft(ZERO); setDirty(true); };

  return (
    <>
      <PageHead eyebrow="Scenario lab" title="What if? Now you know."
        sub="Configure a disruption, run the real optimizer, and compare a solver-verified recovery plan to baseline."
        actions={<button className="btn" onClick={() => { setDraft(ZERO); setPresetId("baseline"); setDirty(true); }}>↻ &nbsp; Reset</button>} />
      <AssumptionsBanner>Sliders build a real scenario; nothing changes until you click <b>Run optimization</b>. Costs are assumed MU; disruptions are synthetic.</AssumptionsBanner>

      <div className="scenario-layout">
        <div>
          <div className="card">
            <div className="card-header"><div><div className="card-title">Scenario parameters</div><div className="card-sub">Levers map to real solver inputs</div></div><span style={{ fontSize: 17 }}>☷</span></div>
            <Lever label="Demand surge (periods 66–68)" value={`+${draft.demandSurge}%`}>
              <input className="range" type="range" min={0} max={50} step={5} value={draft.demandSurge} onChange={(e) => setLever({ demandSurge: +e.target.value })} />
              <div className="range-labels"><span>0%</span><span>+50%</span></div>
            </Lever>
            <Lever label="Gear inbound lead-time delay" value={`${draft.gearDelay} periods`}>
              <input className="range" type="range" min={0} max={6} step={1} value={draft.gearDelay} onChange={(e) => setLever({ gearDelay: +e.target.value })} />
              <div className="range-labels"><span>None</span><span>6 periods</span></div>
            </Lever>
            <Lever label="Battery supplier capacity cut (p64–67)" value={`−${draft.batteryCapCut}%`}>
              <input className="range" type="range" min={0} max={60} step={10} value={draft.batteryCapCut} onChange={(e) => setLever({ batteryCapCut: +e.target.value })} />
              <div className="range-labels"><span>None</span><span>−60%</span></div>
            </Lever>
            <div className="settings-field" style={{ padding: "6px 0 16px" }}>
              <div><strong style={{ fontSize: 12 }}>Enable expedited freight</strong><p style={{ fontSize: 10, margin: "3px 0 0", color: "#a2a6ab" }}>Premium flow, lead −1, bypasses arc capacity</p></div>
              <button className={`switch${draft.expedite ? " on" : ""}`} onClick={() => setLever({ expedite: !draft.expedite })} aria-label="Toggle expedite" />
            </div>
            <button className="btn primary" style={{ width: "100%" }} onClick={run} disabled={solving}>
              {solving ? <><span className="loading-spinner" /> &nbsp; Solving…</> : "▶   Run optimization"}
            </button>
            {dirty && !solving && <div className="tiny" style={{ color: "#b87831", marginTop: 8, textAlign: "center" }}>Parameters changed — run to update results.</div>}
          </div>

          <div className="card" style={{ marginTop: 17 }}>
            <div className="card-title">Scenario presets</div>
            <div className="card-sub">Pre-built, documented disruptions</div>
            <Gate r={scenarios} skeletonH={120}>
              {(s) => (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 15 }}>
                  {s.scenarios.map((sc) => (
                    <button key={sc.id} className="btn mini" onClick={() => choosePreset(sc.id)}
                      style={{ display: "flex", flexDirection: "column", alignItems: "start", gap: 4, textAlign: "left", fontSize: 10, borderColor: presetId === sc.id ? "#7f85ed" : undefined, background: presetId === sc.id ? "#eceefe" : undefined }}>
                      <b style={{ fontSize: 10.5 }}>{sc.name}</b>
                      <span className="muted" style={{ fontSize: 9 }}>{sc.nature === "reference" ? "baseline" : "synthetic"}</span>
                    </button>
                  ))}
                </div>
              )}
            </Gate>
          </div>
        </div>

        <div>
          {error && <div className="demo-banner" style={{ background: "#fdeeea", borderColor: "#f3cfc8", color: "#b2453f" }}><span>⚠</span><div><b>Solve failed.</b> {error}</div></div>}
          {!result && solving && <div className="card">Running the optimizer…</div>}
          {result && (
            <>
              <div className="stat-grid" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
                <Stat label="Service level" value={pct(result.service.overall_pct)} sub={statusSub(result)} />
                <Stat label="Total cost" value={mu(result.objective_mu)} sub="solver objective" />
                <Stat label="Unmet demand" value={`${Math.round(result.service.total_shortage)} u`} sub="lost-sales" />
              </div>

              <div className="card" style={{ marginBottom: 17 }}>
                <div className="card-header"><div><div className="card-title">Baseline vs. {titleCase(result.scenario_id)}</div><div className="card-sub">Solver-verified service outcomes</div></div>
                  <span className={`pill ${result.status === "optimal" ? "green" : "amber"}`}>{result.status}</span></div>
                <Raw html={compareBars(baseline?.service_overall_pct ?? result.service.overall_pct, result.service.overall_pct)} />
                <div className="between"><div className="chart-key">
                  <span><b className="legend-dot" style={{ background: "#8490e9" }} />Baseline</span>
                  <span><b className="legend-dot" style={{ background: "#eca68e" }} />Scenario</span>
                </div>{result.vs_baseline && <span className="tiny muted">Δcost {mu(result.vs_baseline.delta_cost_mu)} · Δservice {result.vs_baseline.delta_service_pp} pp</span>}</div>
              </div>

              <div className="card" style={{ marginBottom: 17 }}>
                <div className="card-header"><div><div className="card-title">Recommendations</div><div className="card-sub">Derived from the solved plan</div></div><span className="pill purple">solver-verified</span></div>
                {result.recommendations.map((r, i) => (
                  <div className="insight-card" style={{ margin: 0, border: 0, borderTop: i ? "1px solid #f0f1f1" : 0, borderRadius: 0, padding: i ? "13px 0 0" : "0 0 13px" }} key={i}>
                    <div className="insight-icon">✦</div><div><p style={{ margin: 0 }}>{r}</p></div>
                  </div>
                ))}
              </div>

              <div className="card">
                <div className="card-title">Solver &amp; validation</div>
                <div className="card-sub">Transparency for every run</div>
                <div className="metric-pair"><span>Status</span><strong>{result.status_message}</strong></div>
                <div className="metric-pair"><span>Objective (assumed MU)</span><strong>{mu(result.objective_mu)}</strong></div>
                <div className="metric-pair"><span>Independent balance check</span><strong>{result.validation.all_ok ? "✓ passed" : "✗ failed"}</strong></div>
                <div className="metric-pair"><span>Max balance residual</span><strong>{result.validation.max_balance_residual.toExponential(1)}</strong></div>
                <div className="metric-pair"><span>Model size</span><strong>{result.model_size.variables} vars · {result.model_size.equality_constraints} eq</strong></div>
                <div className="metric-pair"><span>Solve time</span><strong>{result.solve_seconds}s</strong></div>
                {result.expedite_units > 0 && <div className="metric-pair"><span>Expedited units</span><strong>{Math.round(result.expedite_units)}</strong></div>}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

function Lever({ label, value, children }: { label: string; value: string; children: React.ReactNode }) {
  return <div className="control-group"><div className="control-head"><span>{label}</span><span>{value}</span></div>{children}</div>;
}
function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return <div className="stat-card"><div className="stat-top">{label}</div><div className="stat-value">{value}</div><div className="tiny muted">{sub}</div></div>;
}
function statusSub(r: SolveResult): string { return r.status === "optimal" ? "optimal, verified" : r.status; }
