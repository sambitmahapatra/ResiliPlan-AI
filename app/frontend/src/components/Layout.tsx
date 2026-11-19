import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { PAGES, pageTitleByPath } from "../lib/pages";
import { api } from "../lib/api";

function Brand() {
  return (
    <Link className="logo" to="/">
      <div className="logo-symbol"><span>▥</span></div>
      <span className="brand-word">resili<span style={{ color: "#7770d5" }}>plan</span>
        <small style={{ fontSize: 9, color: "#999", letterSpacing: 1, display: "block", fontWeight: 700 }}>DECISION INTELLIGENCE</small>
      </span>
    </Link>
  );
}

export function Sidebar({ mobileOpen }: { mobileOpen: boolean }) {
  const loc = useLocation();
  const groups: ("Workspace" | "Manage")[] = ["Workspace", "Manage"];
  return (
    <aside className={`sidebar${mobileOpen ? " mobile-open" : ""}`} id="sidebar">
      <Brand />
      <button className="sidebar-toggle" title="Collapse sidebar"
        onClick={() => document.body.classList.toggle("collapsed")}>‹</button>
      {groups.map((g) => (
        <React.Fragment key={g}>
          <div className="sidenav-section" style={g === "Manage" ? { marginTop: 27 } : undefined}>{g}</div>
          <nav className="sidenav">
            {PAGES.filter((p) => p.group === g).map((p) => (
              <Link key={p.key} to={p.path} className={loc.pathname === p.path ? "active" : ""} title={p.title}>
                <span className="navicon">{p.icon}</span>
                <span className="nav-label">{p.title}</span>
                {p.badge && <span className="nav-badge">{p.badge}</span>}
              </Link>
            ))}
          </nav>
        </React.Fragment>
      ))}
      <div className="sidebar-bottom">
        <div style={{ padding: 12, background: "linear-gradient(120deg,#efeeff,#f8f4f5)", borderRadius: 12, margin: "0 5px" }} className="nav-label">
          <div style={{ fontSize: 11, fontWeight: 800 }}>⌘ &nbsp;Planning workspace</div>
          <p style={{ fontSize: 10, lineHeight: 1.6, color: "#8e91a1" }}>HiGHS optimization via SciPy · live backend.</p>
          <Link to="/" style={{ fontSize: 10, color: "#606ade", fontWeight: 800 }}>About the solution ↗</Link>
        </div>
        <div className="profile">
          <div className="avatar">RP</div>
          <div className="profile-copy"><b>Planning analyst</b><span>ResiliPlan workspace</span></div>
        </div>
      </div>
    </aside>
  );
}

export function Topbar({ onMobileMenu }: { onMobileMenu: () => void }) {
  const loc = useLocation();
  const title = pageTitleByPath[loc.pathname] || "Workspace";
  const [health, setHealth] = useState<"loading" | "ok" | "down">("loading");
  useEffect(() => { api.health().then(() => setHealth("ok")).catch(() => setHealth("down")); }, []);
  const toggleTheme = () => {
    document.body.classList.toggle("dark");
    try { localStorage.setItem("rp-theme", document.body.classList.contains("dark") ? "dark" : "light"); } catch { /**/ }
  };
  return (
    <div className="topbar">
      <div className="flex gap10">
        <button className="btn circle mini" id="mobile-menu" onClick={onMobileMenu}>☰</button>
        <div className="crumb">Workspace &nbsp;/&nbsp; <strong>{title}</strong></div>
      </div>
      <div className="top-actions">
        <button className="search-trigger" onClick={() => alert("Use the sidebar to navigate between modules.")}>
          <span>⌕ &nbsp; <span className="text-search">Search modules…</span></span><span className="kbd">⌘ K</span>
        </button>
        {health === "ok" && <span className="pill green"><span className="dot pulse" /> Backend connected</span>}
        {health === "down" && <span className="pill amber"><span className="dot" /> Backend offline</span>}
        {health === "loading" && <span className="pill"><span className="dot" /> Checking…</span>}
        <button className="btn circle mini" title="Toggle theme" onClick={toggleTheme}>◐</button>
        <div className="avatar" style={{ width: 32, height: 32, fontSize: 10 }}>RP</div>
      </div>
    </div>
  );
}

export function PageHead({ eyebrow, title, sub, actions }: { eyebrow: string; title: string; sub: string; actions?: React.ReactNode }) {
  return (
    <div className="page-head">
      <div>
        <div className="eyebrow">ResiliPlan / {eyebrow}</div>
        <h1>{title}</h1>
        <p>{sub}</p>
      </div>
      <div className="page-actions">{actions}</div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => { setMobileOpen(false); window.scrollTo(0, 0); }, [loc.pathname]);
  useEffect(() => { try { if (localStorage.getItem("rp-theme") === "dark") document.body.classList.add("dark"); } catch { /**/ } }, []);
  return (
    <div className="app">
      <Sidebar mobileOpen={mobileOpen} />
      <main className="app-main">
        <Topbar onMobileMenu={() => setMobileOpen((v) => !v)} />
        <div className="work-area reveal">
          {children}
          <div style={{ textAlign: "center", color: "#a7abb2", fontSize: 10, margin: "35px 0 0" }}>
            RESILIPLAN AI · DECISION INTELLIGENCE WORKSPACE · COSTS &amp; DISRUPTIONS ARE ASSUMED/SYNTHETIC
          </div>
        </div>
      </main>
    </div>
  );
}

/** Small reusable banner noting ASSUMED parameters (honesty, not a "demo" label). */
export function AssumptionsBanner({ children }: { children?: React.ReactNode }) {
  return (
    <div className="demo-banner">
      <span style={{ fontSize: 15 }}>ⓘ</span>
      <div>{children ?? <>Cost figures are in <b>MU</b> (assumed, dimensionless — the source data has no costs); disruption scenarios are synthetic stress tests. All results are solver-verified.</>}</div>
    </div>
  );
}
