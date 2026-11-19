import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Network as Net, type Component } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { fmt, pct, titleCase } from "../lib/format";

const FAMILY_COLOR: Record<string, string> = { engine: "#e5b285", gear: "#e5b285", battery: "#b89ef0", seat: "#b89ef0", oem: "#7088ea" };
const roleColor = (role: string, family: string) =>
  role === "demand" ? "#82c4b2" : role === "assembly" ? "#7088ea" : role === "trans" || role === "prod" ? "#b89ef0" : role === "inv" ? "#e5b285" : FAMILY_COLOR[family] || "#8b8df2";

function NetworkMap({ net, selected, onSelect }: { net: Net; selected: string; onSelect: (n: string) => void }) {
  const W = 820, H = 400;
  const pos = useMemo(() => {
    const levels = net.nodes.map((n) => n.echelon_level ?? 0);
    const maxL = Math.max(...levels, 1);
    const fams = Array.from(new Set(net.nodes.filter((n) => n.family !== "oem").map((n) => n.family))).sort();
    const rowGap = fams.length > 1 ? (H - 120) / (fams.length - 1) : 0;
    const colX = (lvl: number) => 80 + ((maxL - lvl) / maxL) * (W - 180);
    const p: Record<string, { x: number; y: number }> = {};
    net.nodes.forEach((n) => {
      const x = colX(n.echelon_level ?? 0);
      let y: number;
      if (n.family === "oem") y = H / 2 + (n.role === "demand" ? 0 : 0);
      else y = 60 + fams.indexOf(n.family) * rowGap;
      p[n.node_n] = { x, y };
    });
    return p;
  }, [net]);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Supply network: 12 nodes, 11 arcs">
      <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#afb7d3" strokeWidth="1.2" /></marker></defs>
      {net.arcs.map((a, i) => {
        const s = pos[a.starting_node_i], t = pos[a.ending_node_j];
        if (!s || !t) return null;
        const px = s.x + 22, qx = t.x - 22;
        const mid = { x: (px + qx) / 2, y: (s.y + t.y) / 2 };
        const long = a.exceeds_horizon;
        return (
          <g key={i}>
            <path d={`M${px},${s.y} C${(px + qx) / 2},${s.y} ${(px + qx) / 2},${t.y} ${qx},${t.y}`} fill="none"
              stroke={long ? "#e8a2a1" : "#b8bfdf"} strokeWidth={long ? 2.6 : 1.8} strokeDasharray={long ? "6 5" : "0"} markerEnd="url(#arrow)" />
            <text x={mid.x} y={mid.y - 5} textAnchor="middle" fontSize="8.5" fontWeight="700" fill={long ? "#cf6f6e" : "#9aa0b4"}>L={a.lead_time}</text>
          </g>
        );
      })}
      {net.nodes.map((n) => {
        const p = pos[n.node_n]; if (!p) return null;
        const c = roleColor(n.role, n.family); const sel = n.node_n === selected;
        return (
          <g key={n.node_n} style={{ cursor: "pointer" }} onClick={() => onSelect(n.node_n)} tabIndex={0}
             onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onSelect(n.node_n); }}>
            <circle cx={p.x} cy={p.y} r={sel ? 26 : 22} fill={c} opacity={sel ? 0.28 : 0.15} />
            <circle cx={p.x} cy={p.y} r="17" fill="white" stroke={c} strokeWidth={sel ? 3 : 2.2} />
            <circle cx={p.x} cy={p.y} r="5.5" fill={c} />
            <text x={p.x} y={p.y + 34} textAnchor="middle" fontSize="9.5" fontWeight="700" fill="currentColor">{n.node_n}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function Network() {
  const net = useApi<Net>(() => api.network(), []);
  const crit = useApi<{ components: Component[] }>(() => api.criticality(), []);
  const [selected, setSelected] = useState("zp7");

  return (
    <>
      <PageHead eyebrow="Supply network" title="The whole network. One clear view."
        sub="Explore supplier dependencies, material flows and lead-time exposure. Click any node."
        actions={<Link className="btn primary" to="/scenarios">Stress-test network ↗</Link>} />
      <AssumptionsBanner>The topology, lead times and component criticality are real (from the validated dataset).</AssumptionsBanner>

      <Gate r={net} skeletonH={120}>
        {(n) => {
          const sel = n.nodes.find((x) => x.node_n === selected) || n.nodes[0];
          const inArcs = n.arcs.filter((a) => a.ending_node_j === sel.node_n);
          const outArcs = n.arcs.filter((a) => a.starting_node_i === sel.node_n);
          const comps = crit.data?.components.filter((c) => c.origin_node === sel.node_n) || [];
          return (
            <>
              <div className="stat-grid">
                {[["Network nodes", `${n.nodes.length}`, "Physical locations"],
                  ["Transport arcs", `${n.arcs.length}`, "Directed connections"],
                  ["Products", "28,049", "28,000 cars · 49 components"],
                  ["Longest lead arc", `${Math.max(...n.arcs.map((a) => a.lead_time))}`, "periods (exceeds horizon)"]].map((x, i) => (
                  <div className="stat-card" key={i}><div className="stat-top">{x[0]}<span>◌</span></div><div className="stat-value">{x[1]}</div><div className="tiny muted">{x[2]}</div></div>
                ))}
              </div>

              <div className="grid-2" style={{ gridTemplateColumns: "1.9fr .85fr" }}>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Manufacturing dependency map</div><div className="card-sub">Click a node to inspect its role and lead-time exposure</div></div><span className="pill green">● &nbsp; Network connected</span></div>
                  <div className="network-map"><NetworkMap net={n} selected={selected} onSelect={setSelected} /></div>
                  <div className="network-legend">
                    <span><b style={{ background: "#b89ef0" }} />Supplier prod/trans</span>
                    <span><b style={{ background: "#e5b285" }} />Supplier inventory</span>
                    <span><b style={{ background: "#7088ea" }} />OEM assembly</span>
                    <span><b style={{ background: "#82c4b2" }} />Customer</span>
                    <span style={{ marginLeft: "auto" }}>Dashed coral = lead time &gt; horizon</span>
                  </div>
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Node intelligence</div><div className="card-sub">Selected location</div></div><span>⌁</span></div>
                  <div className="eyebrow">{titleCase(sel.family)} · {titleCase(sel.role)}</div>
                  <h2 style={{ margin: "12px 0", fontSize: 20 }}>{sel.node_n}</h2>
                  <span className="pill purple">Echelon {sel.echelon_level ?? "—"} from demand</span>
                  <div className="node-detail"><strong>Role</strong><p>{roleDescription(sel.role)}</p></div>
                  <div className="metric-pair"><span>Inbound arcs</span><strong>{inArcs.length}</strong></div>
                  <div className="metric-pair"><span>Outbound arcs</span><strong>{outArcs.length}</strong></div>
                  <div className="metric-pair"><span>Components originating here</span><strong>{comps.length}</strong></div>
                  {inArcs.map((a, i) => (<div className="flow-item" key={i}><span>{a.starting_node_i} → here</span><span className={`pill${a.exceeds_horizon ? " amber" : ""}`}>lead {a.lead_time}</span></div>))}
                  <Link to="/planning" className="btn primary" style={{ marginTop: 14, width: "100%" }}>Review production plan →</Link>
                </div>
              </div>

              <div className="grid-2-even">
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Component criticality</div><div className="card-sub">Top components by BOM fan-out (real)</div></div></div>
                  <Gate r={crit} skeletonH={160}>
                    {(c) => {
                      const top = [...c.components].sort((a, b) => (b.n_cars_using || 0) - (a.n_cars_using || 0)).slice(0, 6);
                      const max = top[0]?.n_cars_using || 1;
                      return <>{top.map((x) => (
                        <div style={{ marginTop: 15 }} key={x.component_p}>
                          <div className="between" style={{ fontSize: 11, marginBottom: 8 }}><span>{x.component_p} <span className="muted">({titleCase(x.group_g)})</span></span><b>{pct(x.pct_configs_dependent)}</b></div>
                          <div className="progress"><span style={{ width: `${((x.n_cars_using || 0) / max) * 100}%` }} /></div>
                        </div>
                      ))}</>;
                    }}
                  </Gate>
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Longest-lead supply arcs</div><div className="card-sub">Where upstream disruptions cannot be recovered in-horizon</div></div></div>
                  {[...n.arcs].sort((a, b) => b.lead_time - a.lead_time).slice(0, 5).map((a, i) => (
                    <div className="flow-item" key={i}>
                      <span><b>{a.starting_node_i}</b><div className="tiny muted" style={{ marginTop: 3 }}>→ {a.ending_node_j} · {titleCase(a.group_g)}</div></span>
                      <span className={`pill${a.exceeds_horizon ? " amber" : ""}`}>{a.lead_time} periods</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          );
        }}
      </Gate>
    </>
  );
}

function roleDescription(role: string): string {
  return { assembly: "OEM assembly: combines engine, gear, battery and seat components into finished vehicles to meet demand.",
    demand: "Customer/demand node where finished-vehicle orders are fulfilled.",
    prod: "Supplier production node that sources or transforms components.",
    inv: "Supplier inventory node that holds and forwards components toward assembly.",
    trans: "Upstream transport node for raw sub-components (long inbound lead time)." }[role] || "Network node.";
}
