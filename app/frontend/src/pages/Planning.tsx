import { Link } from "react-router-dom";
import { api, type SolveResult } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { Raw, donutSvg, CHART_COLORS } from "../lib/charts";
import { fmt, mu, pct, titleCase } from "../lib/format";

export default function Planning() {
  const solve = useApi<SolveResult>(() => api.solve({ scenario_id: "baseline", detail: true, persist: false }), []);
  return (
    <>
      <PageHead eyebrow="Production planner" title="Production planning, solved."
        sub="The optimized baseline plan: production, flows, inventory and cost — all solver-verified."
        actions={<Link to="/scenarios" className="btn dark">Run new scenario →</Link>} />
      <AssumptionsBanner />
      <div className="steps">
        {[["01", "Prepare inputs"], ["02", "Validate constraints"], ["03", "Run optimization"], ["04", "Review decisions"]].map((x, i) => (
          <span key={i}>
            <span className={`step ${i < 3 ? "done" : "active"}`}><span className="num">{i < 3 ? "✓" : x[0]}</span>{x[1]}</span>
            {i < 3 && <span className="step-line" />}
          </span>
        ))}
      </div>

      <Gate r={solve} skeletonH={200}>
        {(r) => {
          const cb = r.cost_breakdown;
          const parts = [["production", cb.production], ["transport", cb.transport], ["holding", cb.holding], ["shortage", cb.shortage]] as [string, number][];
          const total = parts.reduce((a, [, v]) => a + v, 0) || 1;
          const ships = (r.plan?.shipments || []).filter((s: any) => s.qty > 0).sort((a: any, b: any) => b.qty - a.qty).slice(0, 14);
          return (
            <>
              <div className="grid-2">
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Cost structure</div><div className="card-sub">Optimized total = {mu(r.objective_mu)} (assumed MU)</div></div><span className="pill">{r.status}</span></div>
                  <div className="flex" style={{ gap: 25, justifyContent: "center", flexWrap: "wrap" }}>
                    <Raw html={donutSvg(parts.map(([, v]) => v), parts.map(([k]) => CHART_COLORS[k]), 150, mu(r.objective_mu).replace(" MU", ""), "MU total")} />
                    <div style={{ minWidth: 170 }}>
                      {parts.map(([k, v]) => (
                        <div className="between" style={{ gap: 30, margin: "12px 0", fontSize: 11 }} key={k}>
                          <span><b className="legend-dot" style={{ background: CHART_COLORS[k] }} />{titleCase(k)}</span>
                          <strong>{pct((v / total) * 100)} · {fmt(v)}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Planning objective &amp; engine</div><div className="card-sub">The real optimization model</div></div></div>
                  <div style={{ padding: 16, background: "#f7f6fc", borderRadius: 11 }}>
                    <div className="eyebrow">MINIMIZE TOTAL COST</div>
                    <h3 style={{ fontSize: 17, margin: "9px 0 4px" }}>Production + Transport<br />+ Holding + Shortage</h3>
                    <div className="tiny muted">s.t. material balance, BOM, capacity, lead-time &amp; demand</div>
                  </div>
                  <div className="metric-pair"><span>Solver</span><strong>HiGHS (via SciPy)</strong></div>
                  <div className="metric-pair"><span>Problem class</span><strong>Component-layer LP</strong></div>
                  <div className="metric-pair"><span>Model size</span><strong>{r.model_size.variables} vars</strong></div>
                  <div className="metric-pair"><span>Balance check</span><strong>{r.validation.all_ok ? "✓ passed" : "✗ failed"}</strong></div>
                  <div className="metric-pair"><span>Solve time</span><strong>{r.solve_seconds}s</strong></div>
                </div>
              </div>

              <div className="grid-2-even">
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Service by component group</div><div className="card-sub">Share of demand met</div></div></div>
                  {Object.entries(r.service.by_group).map(([g, v]) => (
                    <div style={{ marginTop: 15 }} key={g}>
                      <div className="between" style={{ fontSize: 11, marginBottom: 8 }}><span>{titleCase(g)}</span><b>{pct(v)}</b></div>
                      <div className="progress"><span style={{ width: `${v}%`, background: CHART_COLORS[g] || "#6d80ed" }} /></div>
                    </div>
                  ))}
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Constraint checks</div><div className="card-sub">Independently re-derived from the solution</div></div></div>
                  {[["Material balance", r.validation.all_ok], ["Arc capacity respected", r.validation.max_capacity_violation < 1e-4],
                    ["Nonnegative flows & inventory", r.validation.all_ok], ["Demand identity (served + short)", r.validation.all_ok],
                    ["BOM / transform consumption", r.validation.all_ok]].map(([label, ok], i) => (
                    <div className="flow-item" key={i}><span>{ok ? "✓" : "✗"} &nbsp; {label}</span><span className={`small-tag ${ok ? "blue" : "red"}`}>{ok ? "Verified" : "Failed"}</span></div>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="card-header"><div><div className="card-title">Optimized dispatch decisions</div><div className="card-sub">Largest planned shipments from the solved plan (top {ships.length})</div></div><span className="pill">{(r.plan?.shipments || []).length} total flows</span></div>
                <div className="table-wrap"><table className="data-table">
                  <thead><tr><th>Component</th><th>From</th><th>To</th><th>Period</th><th>Quantity</th><th>Mode</th></tr></thead>
                  <tbody>{ships.map((s: any, i: number) => (
                    <tr key={i}><td><b>{s.component}</b></td><td>{s.i}</td><td>{s.j}</td><td>{s.period}</td><td>{fmt(s.qty)}</td>
                      <td><span className={`small-tag ${s.expedited ? "warn" : ""}`}>{s.expedited ? "Expedited" : "Standard"}</span></td></tr>
                  ))}</tbody>
                </table></div>
                {ships.length === 0 && <div className="tiny muted" style={{ marginTop: 10 }}>No nonzero shipments returned for this plan.</div>}
              </div>
            </>
          );
        }}
      </Gate>
    </>
  );
}
