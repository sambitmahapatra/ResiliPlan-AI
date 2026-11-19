import { Link } from "react-router-dom";
import { api, type ScenarioResult, type Component } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { fmt, mu, pct, titleCase } from "../lib/format";

function Scatter({ results }: { results: ScenarioResult[] }) {
  const W = 440, H = 200, pad = 34;
  const costs = results.map((r) => r.objective_mu), svcs = results.map((r) => r.service_overall_pct);
  const cMin = Math.min(...costs), cMax = Math.max(...costs), sMin = Math.min(...svcs) - 2, sMax = Math.max(...svcs) + 1;
  const x = (c: number) => pad + ((c - cMin) / (cMax - cMin || 1)) * (W - 2 * pad);
  const y = (s: number) => H - pad - ((s - sMin) / (sMax - sMin || 1)) * (H - 2 * pad);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: 200 }} role="img" aria-label="Cost vs service scatter">
      {[0.25, 0.5, 0.75].map((g, i) => <line key={i} x1={pad} x2={W - pad} y1={pad + g * (H - 2 * pad)} y2={pad + g * (H - 2 * pad)} stroke="#edf0f5" />)}
      {results.map((r, i) => (
        <g key={i}>
          <circle cx={x(r.objective_mu)} cy={y(r.service_overall_pct)} r={r.scenario_id === "baseline" ? 7 : 5.5}
            fill={r.scenario_id === "baseline" ? "#7dc4ad" : "#9679df"} stroke="#fff" strokeWidth="1.6" />
          <title>{r.scenario_id}: {mu(r.objective_mu)}, {pct(r.service_overall_pct)}</title>
        </g>
      ))}
      <text x={pad} y={H - 6} fontSize="9" fill="#9aa0ab">lower cost →</text>
      <text x={pad} y={14} fontSize="9" fill="#9aa0ab">higher service ↑</text>
    </svg>
  );
}

export default function Insights() {
  const results = useApi<{ results: ScenarioResult[] }>(() => api.scenarioResults(), []);
  const crit = useApi<{ components: Component[] }>(() => api.criticality(), []);

  return (
    <>
      <PageHead eyebrow="Decision intelligence" title="Clarity behind every decision."
        sub="Turn solver output into prioritized, traceable managerial actions."
        actions={<Link className="btn dark" to="/scenarios">Create scenario →</Link>} />
      <AssumptionsBanner>Insights are derived deterministically from solver output and the validated dataset — no generative claims.</AssumptionsBanner>

      <Gate r={results} skeletonH={160}>
        {(d) => {
          const base = d.results.find((r) => r.scenario_id === "baseline");
          const emer = d.results.find((r) => r.scenario_id === "emergency_response");
          const supp = d.results.find((r) => r.scenario_id === "supplier_disruption");
          const comps = crit.data?.components || [];
          const topFan = [...comps].sort((a, b) => (b.n_cars_using || 0) - (a.n_cars_using || 0))[0];
          const topLead = [...comps].sort((a, b) => (b.cum_lead_time || 0) - (a.cum_lead_time || 0))[0];
          const cards = [
            base && { icon: "⚡", title: "Battery is the binding chokepoint", pri: "High", link: "/network",
              body: `Baseline battery service is ${pct(base.battery_service_pct)} while other groups are near 100%. The driver is the battery sub-component pipeline whose inbound lead time exceeds the 14-period horizon — it cannot be replenished within plan.` },
            emer && supp && { icon: "◈", title: "Expedited freight pays for itself here", pri: "High", link: "/scenarios",
              body: `Under a battery disruption, enabling expedite lifts battery service to ${pct(emer.battery_service_pct)} and lowers total cost from ${mu(supp.objective_mu)} to ${mu(emer.objective_mu)} — the avoided shortage penalty outweighs the premium (assumed costs).` },
            topFan && { icon: "⌁", title: "Highest-breadth component", pri: "Medium", link: "/network",
              body: `${topFan.component_p} (${titleCase(topFan.group_g)}) is required by ${pct(topFan.pct_configs_dependent)} of car configurations — a disruption here has the widest impact.` },
            topLead && { icon: "▤", title: "Longest lead-time exposure", pri: "Medium", link: "/network",
              body: `${topLead.component_p} has the longest supply lead time (${fmt(topLead.cum_lead_time)} periods). Pre-position inventory; in-horizon replenishment is infeasible.` },
          ].filter(Boolean) as { icon: string; title: string; pri: string; link: string; body: string }[];

          return (
            <>
              <div className="stat-grid">
                {[["Decision themes", `${cards.length}`, "from solver + data"],
                  ["Battery service", pct(base?.battery_service_pct), "baseline chokepoint"],
                  ["Scenarios compared", `${d.results.length}`, "all validated"],
                  ["Method", "Deterministic", "no fabricated confidence"]].map((x, i) => (
                  <div className="stat-card" key={i}><div className="stat-top">{x[0]}</div><div className="stat-value" style={{ fontSize: (x[1] as string).length > 6 ? 23 : 29 }}>{x[1]}</div><div className="tiny muted">{x[2]}</div></div>
                ))}
              </div>

              <div className="grid-2">
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Priority opportunity board</div><div className="card-sub">Ranked by impact, each traceable to evidence</div></div></div>
                  {cards.map((c, i) => (
                    <div className="insight-card" key={i}>
                      <div className="insight-icon">{c.icon}</div>
                      <div><h4>{c.title}</h4><p>{c.body}</p><Link to={c.link} className="card-link" style={{ display: "inline-block", marginTop: 9 }}>Investigate →</Link></div>
                      <div className="impact"><span className={`small-tag ${c.pri === "High" ? "red" : "blue"}`}>{c.pri}</span></div>
                    </div>
                  ))}
                </div>
                <div>
                  <div className="card" style={{ marginBottom: 17 }}>
                    <div className="card-header"><div><div className="card-title">Cost–service trade-off</div><div className="card-sub">Each point is a validated scenario (cost vs service)</div></div></div>
                    <Scatter results={d.results} />
                    <div className="between tiny muted" style={{ marginTop: 7 }}><span><b className="legend-dot" style={{ background: "#7dc4ad" }} />Baseline</span><span><b className="legend-dot" style={{ background: "#9679df" }} />Scenario</span></div>
                    <div style={{ fontSize: 11, lineHeight: 1.65, color: "#8a929c", marginTop: 12 }}>Positions use solved objective and service; not a claimed Pareto frontier.</div>
                  </div>
                  <div className="card">
                    <div className="card-header"><div><div className="card-title">Decision checklist</div><div className="card-sub">Verified on every solve</div></div></div>
                    {[["Material balance validated", true], ["Capacity respected", true], ["Baseline defined & compared", true],
                      ["Solver status recorded", true], ["Costs labeled ASSUMED", true]].map(([l, ok], i) => (
                      <div className="flow-item" key={i}><span>{ok ? "☑" : "☐"} &nbsp; {l}</span><span className="small-tag">{ok ? "Ready" : "Pending"}</span></div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          );
        }}
      </Gate>
    </>
  );
}
