import { useState } from "react";
import { Link } from "react-router-dom";
import { MarketingNav } from "../components/MarketingNav";
import { HERO_MODULES } from "../lib/pages";

interface Stage {
  icon: string; title: string; teaser: string; label: string;
  detailTitle: string; detail: string; deliver: string[]; link: string; linkLabel: string;
}

// Eight-stage methodology — copy reflects the COMPLETED backend (not "planned").
const STAGES: Stage[] = [
  { icon: "▤", title: "Understand the source", teaser: "Map nodes, arcs, products, BOM and customer demand.", label: "Source audit",
    detailTitle: "We start from the real automotive network", detail: "The 2020 Automotive Production Network workbook (12 worksheets) is audited: 12 nodes, 11 arcs, 28,049 products, 87,059 BOM links, demand over periods 61–74.",
    deliver: ["Source inventory & column data dictionary", "Node–arc–product relationship checks", "Decision scope and KPI definitions"], link: "/data", linkLabel: "Data Studio" },
  { icon: "◇", title: "Clean & validate", teaser: "Check missing values, keys, quantities and BOM integrity.", label: "Data quality",
    detailTitle: "Every planning input is defensible", detail: "Duplicate keys, referential integrity, BOM cycles, negative quantities and period alignment are all checked. Counts reproduce; 0 missing values; BOM confirmed a DAG (depth 2).",
    deliver: ["Key & referential-integrity tests (all pass)", "BOM consistency & inventory checks", "Versioned, reproducible cleaned tables"], link: "/data", linkLabel: "Data Studio" },
  { icon: "≋", title: "Standardize & structure", teaser: "Align units, periods and product hierarchies.", label: "Data modelling",
    detailTitle: "A consistent, connected model of the network", detail: "Identifiers are canonicalized, periods synchronized, and the BOM is exploded from 28,000 car configs onto the 49 real components — so the full network is modelled exactly.",
    deliver: ["Canonical product, node & arc tables", "Consistent time indices & units", "BOM explosion → component demand"], link: "/network", linkLabel: "Network" },
  { icon: "▥", title: "Explore the network", teaser: "Study demand, bottlenecks and inventory exposure.", label: "Exploratory analysis",
    detailTitle: "Understand why the supply chain is vulnerable", detail: "EDA surfaces the resilience story: seat components have the highest fan-out and longest lead time; battery is the capacity/pipeline chokepoint.",
    deliver: ["Demand & inventory distributions", "BOM fan-out component criticality", "Capacity & lead-time diagnostics"], link: "/network", linkLabel: "Network" },
  { icon: "◈", title: "Engineer scenarios", teaser: "Build disruption tests with justified inputs.", label: "Scenario intelligence",
    detailTitle: "Translate uncertainty into testable what-if cases", detail: "Six synthetic disruptions (supplier, material delay, demand surge, transport, emergency-with-expedite) plus a seeded Monte Carlo. Forecasting is intentionally omitted — the horizon is too short.",
    deliver: ["Documented disruption configurations", "Sensitivity ranges on assumed costs", "Seeded Monte Carlo over demand"], link: "/scenarios", linkLabel: "Scenario Lab" },
  { icon: "∑", title: "Optimize with MILP", teaser: "Solve production, inventory and transport decisions.", label: "Prescriptive engine",
    detailTitle: "Feasible recovery plans via mathematical optimization", detail: "A time-indexed component-layer linear program is solved with HiGHS (via SciPy), minimizing production + transport + holding + shortage cost subject to BOM, capacity, lead-time and demand-balance constraints.",
    deliver: ["Explicit objective, variables & constraints", "Solver status, runtime & reconciled objective", "Production, inventory & material-flow plans"], link: "/planning", linkLabel: "Production Planner" },
  { icon: "◎", title: "Validate & compare", teaser: "Test feasibility, scenarios and cost–service trade-offs.", label: "Decision validation",
    detailTitle: "Validated before any managerial claim", detail: "An independent material-balance check runs on every solve (residual 0). Optimized plans are compared to a defined baseline across cost and service.",
    deliver: ["Independent constraint & balance checks", "Baseline vs. disruption comparison", "Transparent assumptions & service–cost KPIs"], link: "/insights", linkLabel: "Insights" },
  { icon: "✧", title: "Deliver the solution", teaser: "Turn results into a decision workspace.", label: "React + FastAPI",
    detailTitle: "The model, in the hands of a supply-chain manager", detail: "This React application is backed by a FastAPI service running the live solver, with input validation, network visualization, scenario controls, explainable recommendations and downloadable results.",
    deliver: ["Interactive dashboard & scenario lab", "Actionable production & sourcing recommendations", "Downloadable decision reports"], link: "/dashboard", linkLabel: "Dashboard" },
];

export default function Home() {
  const [active, setActive] = useState(0);
  const s = STAGES[active];
  return (
    <div className="marketing" id="top">
      <MarketingNav />
      <section className="hero hero-v4">
        <div className="hero-copy">
          <div className="hero-label"><span style={{ color: "#7b71e9" }}>✳</span> MANUFACTURING SUPPLY CHAIN DECISION INTELLIGENCE <span>↗</span></div>
          <h1><span className="gradient-text">Smarter planning.</span> Stronger supply chains.</h1>
          <p>From multi-tier supplier networks to feasible recovery decisions — a working manufacturing analytics workspace with a live optimization engine behind every recommendation.</p>
          <div className="hero-direct-intro"><span className="hero-direct-pulse" />Your workspace, one click away</div>
          <div className="hero-quicknav" aria-label="Direct access to the ResiliPlan workspace">
            <div className="hero-quicknav-heading">
              <span className="hero-quicknav-eyebrow">EXPLORE THE WORKSPACE</span>
              <span className="hero-quicknav-subtitle">Select any module to open it</span>
            </div>
            <div className="hero-quicknav-grid">
              {HERO_MODULES.map((m) => (
                <Link key={m.path} className="hero-quicklink" to={m.path} aria-label={`Open ${m.title}`}>
                  <span className="hero-quickicon" style={{ ["--quick-bg" as any]: m.bg, ["--quick-fg" as any]: m.fg }}>{m.icon}</span>
                  <span className="hero-quickcopy"><strong>{m.title}</strong><small>{m.caption}</small></span>
                  <span className="hero-quickarrow" aria-hidden="true">↗</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
        <div className="marketing-section solution-section solution-in-hero" id="how-it-works">
          <div className="section-container solution-container">
            <div className="solution-head">
              <span className="eyebrow">WHAT IS OUR SOLUTION?</span>
              <h2>From raw data to <span className="gradient-text">better production decisions.</span></h2>
              <p>We clean and structure the automotive manufacturing network, explore risk and bottlenecks, engineer disruption scenarios, then solve a HiGHS optimization model to recommend feasible production, inventory and transportation decisions. Every step is traceable and independently validated.</p>
              <div className="solution-status"><span className="status-light" /> Live optimization backend <span className="status-divider">·</span> HiGHS (via SciPy) MILP engine <span className="status-divider">·</span> Costs assumed &amp; disclosed</div>
            </div>
            <div className="solution-stage-head">
              <div><span className="tiny muted">END-TO-END METHODOLOGY</span><h3>Eight stages. From data cleaning to deployment.</h3></div>
              <span className="stage-hint">Select a stage to explore <span aria-hidden="true">↘</span></span>
            </div>
            <div className="solution-stage-grid" role="group" aria-label="Explore the eight workflow stages">
              {STAGES.map((st, i) => (
                <button key={i} type="button" className={`solution-stage${i === active ? " active" : ""}`}
                  aria-pressed={i === active} onClick={() => setActive(i)}>
                  <span className="stage-top"><span className="stage-number">{String(i + 1).padStart(2, "0")}</span><span className="stage-icon" aria-hidden="true">{st.icon}</span></span>
                  <span className="stage-name">{st.title}</span>
                  <span className="stage-desc">{st.teaser}</span>
                  <span className="stage-foot"><span>{st.label}</span><span aria-hidden="true">↗</span></span>
                </button>
              ))}
            </div>
            <div className="solution-stage-detail" id="solution-stage-detail" aria-live="polite">
              <div className="solution-detail-copy">
                <span className="solution-detail-eyebrow">STAGE {String(active + 1).padStart(2, "0")} / 08 · {s.label}</span>
                <h3>{s.detailTitle}</h3>
                <p>{s.detail}</p>
                <Link className="solution-detail-link" to={s.link}>Explore {s.linkLabel} <span aria-hidden="true">↗</span></Link>
              </div>
              <div className="solution-detail-results">
                <span className="result-kicker">DELIVERED OUTPUTS</span>
                {s.deliver.map((d, j) => (<div className="result-row" key={j}><span className="result-check">✓</span><span>{d}</span></div>))}
                <div className="result-smallprint">Implemented &amp; validated · costs/disruptions are assumed/synthetic</div>
              </div>
            </div>
            <div className="solution-architecture">
              <div className="architecture-label"><span className="eyebrow">HOW IT CONNECTS</span><strong>From source data to recovery decisions</strong></div>
              <div className="architecture-track">
                <div className="architecture-node"><span className="architecture-node-icon">▤</span><b>Manufacturing data</b><small>12 source tables · BOM · demand · inventory</small></div>
                <span className="architecture-arrow" aria-hidden="true">⟶</span>
                <div className="architecture-node"><span className="architecture-node-icon">◈</span><b>Analytics + optimization</b><small>EDA · scenarios · HiGHS MILP</small></div>
                <span className="architecture-arrow" aria-hidden="true">⟶</span>
                <div className="architecture-node"><span className="architecture-node-icon">✧</span><b>Managerial decisions</b><small>Production · shipments · service · trade-offs</small></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="marketing-section marketing-features" id="capabilities">
        <div className="section-container">
          <div className="center">
            <div className="eyebrow">EXPLORE THE CAPABILITIES</div>
            <h2 className="section-h">Every tool you need, <span className="gradient-text">one connected workspace.</span></h2>
            <p className="section-p">Every screen turns network complexity into actions a manufacturing team can execute.</p>
          </div>
          <div className="feature-grid">
            {[
              ["⌁", "Map the full network", "See the 12-node, 11-arc multi-tier network, material flows, lead times and upstream risks.", "/network"],
              ["◈", "Stress-test every scenario", "Simulate supplier delays, demand surges and capacity cuts, then solve for a recovery plan.", "/scenarios"],
              ["▤", "Optimize the production plan", "Cost-aware production, inventory and transport decisions from the live HiGHS solver.", "/planning"],
              ["▣", "Trace the data", "Follow the pipeline from validated source tables to component demand.", "/data"],
              ["✧", "Explain the recommendation", "Translate optimization output into clear trade-offs and prioritized actions.", "/insights"],
              ["▧", "Tell the business story", "Export decision briefs and baseline-vs-scenario comparisons.", "/reports"],
            ].map((f, i) => (
              <Link key={i} className="feature-card" to={f[3] as string}>
                <div className="feature-art"><div className="art-icon" style={{ background: ["linear-gradient(135deg,#f4e6dc,#fff1e5)", "linear-gradient(135deg,#f6d7f0,#f2dcff)", "linear-gradient(135deg,#dceaff,#ecf2ff)"][i % 3] }}>{f[0]}</div></div>
                <h3>{f[1]} ↗</h3><p>{f[2]}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="marketing-section" style={{ background: "#fff" }}>
        <div className="section-container center">
          <div className="eyebrow">THE ENGINE BEHIND THE EXPERIENCE</div>
          <h2 className="section-h">Beautiful on the surface.<br /><span className="gradient-text">Rigorous underneath.</span></h2>
          <p className="section-p">Built on a validated automotive data pipeline, multi-echelon constraints, and a free, open-source optimization stack — solving live in the browser-connected backend.</p>
          <div className="engine-tags"><span>Python + Pandas</span><span>Supply-chain EDA</span><span>HiGHS (SciPy)</span><span>FastAPI</span><span>React + TypeScript</span></div>
          <Link className="btn primary" style={{ marginTop: 27 }} to="/dashboard">Go to the dashboard →</Link>
        </div>
      </section>

      <section className="marketing-section marketing-features" id="faq">
        <div className="section-container" style={{ maxWidth: 760 }}>
          <div className="center"><div className="eyebrow">FAQ</div><h2 className="section-h">Frequently asked questions.</h2></div>
          <div style={{ marginTop: 38 }}><Faq /></div>
        </div>
      </section>

      <section className="cta-section">
        <div className="eyebrow" style={{ color: "#a6aaf7" }}>A NEW STANDARD IN MANUFACTURING PLANNING</div>
        <h2>Make the next decision<br />your best one.</h2>
        <p>Open the workspace, run a disruption scenario, and inspect a solver-verified recovery plan.</p>
        <Link className="btn primary" to="/scenarios">Run a scenario ↗</Link>
      </section>

      <footer className="marketing-footer">
        <div className="footer-grid">
          <div className="logo" style={{ fontSize: 15 }}><div className="logo-symbol"><span>▥</span></div>resiliplan</div>
          <span>© 2026 ResiliPlan AI · Academic project (GIM PGDM-BDA) · Costs &amp; disruptions are assumed/synthetic.</span>
          <Link to="/dashboard">Open workspace ↗</Link>
        </div>
      </footer>
    </div>
  );
}

function Faq() {
  const items: [string, string][] = [
    ["Is this a finished optimization system?", "Yes — this frontend is connected to a working FastAPI backend that runs a real HiGHS optimization on demand. Costs are assumed (the source data has none) and disruptions are synthetic stress tests, both clearly labeled."],
    ["Which dataset is this based on?", "The 2020 Automotive Production Network workbook: products, nodes, arcs, demand, inventory and bill-of-materials, cleaned and validated into versioned tables."],
    ["What is the optimization method?", "A time-indexed, component-layer (mixed-integer) linear program, solved with the open-source HiGHS solver via SciPy. The solution is independently balance-checked on every run."],
    ["Can I upload the Excel workbook here?", "The bundled, validated dataset is used for optimization. Live upload/ingestion of new XLSB files is not part of this build and is shown as unavailable rather than simulated."],
    ["Is this an AI agent?", "No. The decision engine is mathematical optimization. Descriptive analytics support it; no generative or ML prediction is used for the plans."],
  ];
  const [open, setOpen] = useState(0);
  return (
    <>
      {items.map(([q, a], i) => (
        <div key={i} className={`faq-row${open === i ? " open" : ""}`} onClick={() => setOpen(open === i ? -1 : i)}>
          <div className="faq-q">{q}<span className="faq-toggle">{open === i ? "−" : "+"}</span></div>
          <div className="faq-a">{a}</div>
        </div>
      ))}
    </>
  );
}
