import { Link } from "react-router-dom";
import { api, type ScenarioResult, type Component, type MonteCarlo } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { Raw, donutSvg, CHART_COLORS } from "../lib/charts";
import { fmt, mu, pct, titleCase, HORIZON } from "../lib/format";

export default function Dashboard() {
  const results = useApi<{ results: ScenarioResult[]; baseline_objective: number }>(() => api.scenarioResults(), []);
  const crit = useApi<{ components: Component[] }>(() => api.criticality(), []);
  const mc = useApi<MonteCarlo>(() => api.monteCarlo(), []);

  return (
    <>
      <PageHead eyebrow="Executive overview" title="Supply chain at a glance"
        sub={`Solver-verified baseline plan over ${HORIZON}. Costs are in assumed MU.`}
        actions={<>
          <a className="btn" href={api.exportScenarioCsvUrl()}>↧ &nbsp; Export snapshot</a>
          <Link className="btn dark" to="/scenarios">+ &nbsp; New scenario</Link>
        </>} />
      <AssumptionsBanner />

      <Gate r={results} skeletonH={120}>
        {(d) => {
          const base = d.results.find((r) => r.scenario_id === "baseline");
          if (!base) return <div className="card">No baseline result available.</div>;
          const served = Math.max(0, base.service_overall_pct);
          const groups = Object.entries(base.service_by_group);
          const cost = base.cost_breakdown;
          return (
            <>
              <div className="stat-grid">
                {[
                  ["Component service level", pct(base.service_overall_pct), "solver-verified", CHART_COLORS.engine],
                  ["Total plan cost", mu(base.objective_mu), "baseline optimum", CHART_COLORS.transport],
                  ["Battery service", pct(base.battery_service_pct), "pipeline-constrained", CHART_COLORS.battery],
                  ["Unmet demand", `${fmt(base.total_shortage)} units`, "lost-sales shortage", "#d69bbf"],
                ].map((x, i) => (
                  <div className="stat-card" key={i}>
                    <div className="stat-top"><span>{x[0]}</span><span>◌</span></div>
                    <div className="stat-value mono">{x[1]}</div>
                    <div className="stat-footer"><span>{x[2]}</span></div>
                  </div>
                ))}
              </div>

              <div className="grid-2">
                <div className="card">
                  <div className="card-header">
                    <div><div className="card-title">Service level by component group</div><div className="card-sub">Share of demand met on time, baseline plan</div></div>
                    <Link to="/planning" className="card-link">Production plan ↗</Link>
                  </div>
                  {groups.map(([g, v]) => (
                    <div style={{ margin: "17px 0" }} key={g}>
                      <div className="between" style={{ fontSize: 11, marginBottom: 8 }}><span>{titleCase(g)}</span><b>{pct(v)}</b></div>
                      <div className="progress"><span style={{ width: `${v}%`, background: CHART_COLORS[g] || "#6d80ed" }} /></div>
                    </div>
                  ))}
                  <div className="tiny muted" style={{ marginTop: 6 }}>Battery is the resilience chokepoint — see Insights for the root cause.</div>
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Overall fulfilment</div><div className="card-sub">Baseline, all direct car components</div></div>
                    <Link to="/insights" className="card-link">See insights ↗</Link></div>
                  <Raw html={donutSvg([served, 100 - served], ["#7880eb", "#e7a5aa"], 173, pct(served), "service")} />
                  <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 20, fontSize: 10, color: "#8d939d" }}>
                    <span><b className="legend-dot" style={{ background: "#7880eb" }} />Met on time</span>
                    <span><b className="legend-dot" style={{ background: "#e7a5aa" }} />Unmet (lost sales)</span>
                  </div>
                </div>
              </div>

              <div className="grid-2-even">
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Scenario service comparison</div><div className="card-sub">Overall service across disruption scenarios</div></div>
                    <Link to="/scenarios" className="card-link">Scenario lab ↗</Link></div>
                  {d.results.map((r) => (
                    <div style={{ margin: "14px 0" }} key={r.scenario_id}>
                      <div className="between" style={{ fontSize: 11, marginBottom: 8 }}>
                        <span>{titleCase(r.scenario_id)}</span><b>{pct(r.service_overall_pct)} · {mu(r.objective_mu)}</b>
                      </div>
                      <div className="progress"><span style={{ width: `${r.service_overall_pct}%`, background: r.scenario_id === "baseline" ? "#7dc4ad" : "#e5a381" }} /></div>
                    </div>
                  ))}
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Robustness (Monte Carlo)</div><div className="card-sub">Service under demand uncertainty</div></div><span className="pill purple">seeded</span></div>
                  <Gate r={mc} skeletonH={120}>
                    {(m) => (
                      <div style={{ padding: "6px 2px" }}>
                        <div className="mini-number" style={{ fontSize: 30 }}>{pct(m.service_mean)}</div>
                        <div className="tiny muted" style={{ marginBottom: 14 }}>mean service across {m.n ?? "—"} runs (seed {m.seed ?? "—"})</div>
                        <div className="metric-pair"><span>Best case</span><strong>{pct(m.service_max)}</strong></div>
                        <div className="metric-pair"><span>Worst case</span><strong>{pct(m.service_min)}</strong></div>
                        <div className="notice" style={{ marginTop: 10 }}>Demand scaled by a seeded normal factor; cost/disruption parameters are assumed.</div>
                      </div>
                    )}
                  </Gate>
                </div>
              </div>

              <div className="card">
                <div className="card-header"><div><div className="card-title">Most critical components</div><div className="card-sub">By BOM fan-out — how many car configurations depend on each</div></div>
                  <Link className="card-link" to="/network">Network view ↗</Link></div>
                <Gate r={crit} skeletonH={200}>
                  {(c) => {
                    const top = [...c.components].sort((a, b) => (b.n_cars_using || 0) - (a.n_cars_using || 0)).slice(0, 6);
                    return (
                      <div className="table-wrap"><table className="data-table">
                        <thead><tr><th>Component</th><th>Group</th><th>Origin node</th><th>Configs dependent</th><th>Supply lead (periods)</th><th>Role</th></tr></thead>
                        <tbody>{top.map((x) => (
                          <tr key={x.component_p}>
                            <td><b>{x.component_p}</b></td><td>{titleCase(x.group_g)}</td><td>{x.origin_node || "—"}</td>
                            <td>{fmt(x.n_cars_using)} ({pct(x.pct_configs_dependent)})</td><td>{fmt(x.cum_lead_time)}</td>
                            <td><span className={`small-tag ${x.is_direct_car_component ? "blue" : "warn"}`}>{x.is_direct_car_component ? "Direct" : "Sub-component"}</span></td>
                          </tr>
                        ))}</tbody>
                      </table></div>
                    );
                  }}
                </Gate>
              </div>
            </>
          );
        }}
      </Gate>
    </>
  );
}
