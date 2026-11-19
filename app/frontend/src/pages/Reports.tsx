import { useState } from "react";
import { api, type ScenarioResult } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { mu, pct, titleCase } from "../lib/format";

const SECTIONS = ["Executive summary", "Baseline & scenario KPIs", "Cost breakdown", "Assumptions & limitations", "Validation evidence"];

export default function Reports() {
  const results = useApi<{ results: ScenarioResult[] }>(() => api.scenarioResults(), []);
  const [on, setOn] = useState<boolean[]>(SECTIONS.map(() => true));
  const toggle = (i: number) => setOn((o) => o.map((v, j) => (j === i ? !v : v)));

  return (
    <>
      <PageHead eyebrow="Reports" title="Every decision, documented."
        sub="Build a management brief from solver-verified results and assumptions."
        actions={<>
          <button className="btn" onClick={() => window.print()}>⎙ &nbsp; Print / PDF</button>
          <a className="btn dark" href={api.exportScenarioCsvUrl()}>↧ &nbsp; Export CSV</a>
        </>} />
      <AssumptionsBanner />

      <Gate r={results} skeletonH={180}>
        {(d) => {
          const base = d.results.find((r) => r.scenario_id === "baseline");
          return (
            <div className="grid-2">
              <div className="card">
                <div className="report-cover">
                  <div className="eyebrow">RESILIPLAN AI · MANAGEMENT BRIEF</div>
                  <h2>Automotive network<br />resilience review</h2>
                  <div className="tiny" style={{ color: "#8b8e9a" }}>14-period horizon (61–74) · solver-verified · costs assumed (MU)</div>
                </div>
                <div className="between" style={{ margin: "19px 0 7px" }}><div><div className="card-title">Report preview</div><div className="card-sub">Sections update with the toggles</div></div></div>
                {on[0] && <Para title="01 · Executive summary">Baseline plan achieves {pct(base?.service_overall_pct)} component service at {mu(base?.objective_mu)}. Battery is the binding chokepoint ({pct(base?.battery_service_pct)}) due to an upstream lead time exceeding the horizon.</Para>}
                {on[1] && (
                  <div className="table-wrap" style={{ marginTop: 10 }}><table className="data-table">
                    <thead><tr><th>Scenario</th><th>Objective</th><th>Service</th><th>Battery</th><th>Validated</th></tr></thead>
                    <tbody>{d.results.map((r) => (
                      <tr key={r.scenario_id}><td><b>{titleCase(r.scenario_id)}</b></td><td>{mu(r.objective_mu)}</td><td>{pct(r.service_overall_pct)}</td><td>{pct(r.battery_service_pct)}</td>
                        <td><span className="small-tag">{r.validated ? "✓" : "—"}</span></td></tr>
                    ))}</tbody>
                  </table></div>
                )}
                {on[2] && base && <Para title="03 · Cost breakdown">{Object.entries(base.cost_breakdown).map(([k, v]) => `${titleCase(k)} ${mu(v)}`).join(" · ")}</Para>}
                {on[3] && <Para title="04 · Assumptions & limitations">All cost coefficients are ASSUMED (source workbook has no costs); disruptions are synthetic; service is lost-sales; the model is a component-layer LP.</Para>}
                {on[4] && <Para title="05 · Validation evidence">Every scenario solved to optimality and passed an independent material-balance check (residual ≈ 0). Solver: HiGHS via SciPy.</Para>}
              </div>
              <div>
                <div className="card" style={{ marginBottom: 17 }}>
                  <div className="card-header"><div><div className="card-title">Report configuration</div><div className="card-sub">Choose what to include</div></div></div>
                  {SECTIONS.map((s, i) => (
                    <label className="settings-field" style={{ cursor: "pointer" }} key={i}>
                      <strong>{s}</strong>
                      <input type="checkbox" checked={on[i]} onChange={() => toggle(i)} style={{ accentColor: "#7778e7" }} />
                    </label>
                  ))}
                  <a className="btn primary" style={{ width: "100%", marginTop: 17, display: "block", textAlign: "center" }} href={api.exportScenarioCsvUrl()}>Download scenario comparison (CSV) ↧</a>
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Audit &amp; reproducibility</div><div className="card-sub">Transparency is part of the product</div></div></div>
                  <div className="notice">Each solve records solver status, objective (assumed MU), independent balance-check residuals, model size and runtime. Disruptions and costs are labeled assumed/synthetic. Dataset is the validated 2020 Automotive Production Network workbook.</div>
                </div>
              </div>
            </div>
          );
        }}
      </Gate>
    </>
  );
}

function Para({ title, children }: { title: string; children: React.ReactNode }) {
  return <div style={{ margin: "12px 0" }}><div className="eyebrow" style={{ marginBottom: 5 }}>{title}</div><p style={{ fontSize: 12, lineHeight: 1.7, color: "#5b6270", margin: 0 }}>{children}</p></div>;
}
