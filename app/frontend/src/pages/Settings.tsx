import { useEffect, useState } from "react";
import { api, type Health } from "../lib/api";
import { useApi } from "../lib/useApi";
import { PageHead, AssumptionsBanner } from "../components/Layout";

function usePref(key: string, cls: string, initial = false) {
  const [on, setOn] = useState(() => { try { return localStorage.getItem(key) === "yes"; } catch { return initial; } });
  useEffect(() => { document.body.classList.toggle(cls, on); try { localStorage.setItem(key, on ? "yes" : "no"); } catch { /**/ } }, [on, cls, key]);
  return [on, setOn] as const;
}

export default function Settings() {
  const health = useApi<Health>(() => api.health(), []);
  const [dark, setDark] = useState(() => { try { return localStorage.getItem("rp-theme") === "dark"; } catch { return false; } });
  const [collapsed, setCollapsed] = usePref("rp-collapse", "collapsed");
  const [reduce, setReduce] = usePref("rp-reduce", "reduce-motion");
  useEffect(() => { document.body.classList.toggle("dark", dark); try { localStorage.setItem("rp-theme", dark ? "dark" : "light"); } catch { /**/ } }, [dark]);

  return (
    <>
      <PageHead eyebrow="Settings" title="A workspace that works your way."
        sub="Display preferences and the real backend configuration." />
      <AssumptionsBanner>Preferences are stored in your browser. Model info below is read from the live backend.</AssumptionsBanner>

      <div className="grid-2-even">
        <div className="card">
          <div className="card-header"><div><div className="card-title">Workspace preferences</div><div className="card-sub">Stored locally in this browser</div></div></div>
          {[["Dark theme", "Switch between calm light and dark palettes", dark, () => setDark((v) => !v)],
            ["Compact sidebar", "Give more space to detailed dashboards", collapsed, () => setCollapsed((v) => !v)],
            ["Reduce motion", "Minimize transitions and animations", reduce, () => setReduce((v) => !v)]].map((x, i) => (
            <div className="settings-field" key={i}>
              <div><strong>{x[0] as string}</strong><p>{x[1] as string}</p></div>
              <button className={`switch${x[2] ? " on" : ""}`} onClick={x[3] as () => void} aria-label={`Toggle ${x[0]}`} />
            </div>
          ))}
        </div>
        <div>
          <div className="card" style={{ marginBottom: 17 }}>
            <div className="card-header"><div><div className="card-title">Optimization configuration</div><div className="card-sub">Actual backend (read-only)</div></div></div>
            {[["Model class", "Component-layer (MI)LP"], ["Solver", "HiGHS (open source, via SciPy)"], ["Planning horizon", "14 periods (61–74)"],
              ["Cost data", "None in source — all ASSUMED"], ["Shortage model", "Lost-sales (no backorder)"]].map((x, i) => (
              <div className="metric-pair" key={i}><span>{x[0]}</span><strong style={{ fontSize: 11 }}>{x[1]}</strong></div>
            ))}
          </div>
          <div className="card">
            <div className="card-header"><div><div className="card-title">Backend connection</div><div className="card-sub">Live health check</div></div></div>
            {health.state === "loading" && <div className="metric-pair"><span>Status</span><strong>Checking…</strong></div>}
            {health.state === "error" && <div className="metric-pair"><span>Status</span><strong style={{ color: "#d76c69" }}>Offline</strong></div>}
            {health.data && <>
              <div className="metric-pair"><span>API</span><strong style={{ color: "#198d6c" }}>{health.data.status}</strong></div>
              <div className="metric-pair"><span>Service</span><strong>{health.data.service} v{health.data.version}</strong></div>
              <div className="metric-pair"><span>Supabase persistence</span><strong>{health.data.supabase_configured ? "configured" : "not configured"}</strong></div>
            </>}
            <p className="notice" style={{ marginTop: 10 }}><b>Live:</b> navigation, network, criticality, scenario solving, baseline comparison, Monte Carlo, CSV export, preferences. <b>Not enabled:</b> live dataset upload/ingestion and user accounts.</p>
          </div>
        </div>
      </div>
    </>
  );
}
