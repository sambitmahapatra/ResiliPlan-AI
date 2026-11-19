// Route catalog — single source for sidebar, hero module grid, breadcrumbs, search.
export interface PageDef { path: string; key: string; title: string; icon: string; caption: string; group: "Workspace" | "Manage"; bg: string; fg: string; badge?: string; }

export const PAGES: PageDef[] = [
  { path: "/dashboard", key: "dashboard", title: "Overview",            icon: "▦", caption: "Executive overview",   group: "Workspace", bg: "#e9eefe", fg: "#535fd6" },
  { path: "/network",   key: "network",   title: "Supply network",      icon: "⌁", caption: "Supply chain map",     group: "Workspace", bg: "#e7f4f1", fg: "#14877b" },
  { path: "/planning",  key: "planning",  title: "Production planner",   icon: "▤", caption: "Production optimizer",  group: "Workspace", bg: "#fef0e5", fg: "#c67a3b" },
  { path: "/scenarios", key: "scenarios", title: "Scenario lab",         icon: "◈", caption: "Disruption simulator", group: "Workspace", bg: "#fce6f2", fg: "#ba4b95", badge: "LAB" },
  { path: "/data",      key: "data",      title: "Data studio",          icon: "▣", caption: "Datasets & validation",group: "Manage",    bg: "#e8f0ff", fg: "#4876bc" },
  { path: "/insights",  key: "insights",  title: "Intelligence",         icon: "✧", caption: "Decision intelligence",group: "Manage",    bg: "#f1eaff", fg: "#825ec7" },
  { path: "/reports",   key: "reports",   title: "Reports",              icon: "▧", caption: "Export & summarize",   group: "Manage",    bg: "#eef4e6", fg: "#70943b" },
  { path: "/settings",  key: "settings",  title: "Settings",             icon: "⚙", caption: "Workspace options",    group: "Manage",    bg: "#eff0f4", fg: "#657084" },
];

// Hero grid labels per the V4 spec (slightly different display titles than sidebar).
export const HERO_MODULES = [
  { path: "/dashboard", title: "Dashboard",   icon: "▦", caption: "Executive overview",    bg: "#e9eefe", fg: "#535fd6" },
  { path: "/network",   title: "Network",     icon: "⌁", caption: "Supply chain map",      bg: "#e7f4f1", fg: "#14877b" },
  { path: "/scenarios", title: "Scenarios",   icon: "◈", caption: "Disruption simulator",  bg: "#fce6f2", fg: "#ba4b95" },
  { path: "/planning",  title: "Planning",    icon: "▤", caption: "Production optimizer",   bg: "#fef0e5", fg: "#c67a3b" },
  { path: "/data",      title: "Data Studio", icon: "▣", caption: "Datasets & validation",  bg: "#e8f0ff", fg: "#4876bc" },
  { path: "/insights",  title: "Insights",    icon: "✧", caption: "Decision intelligence",  bg: "#f1eaff", fg: "#825ec7" },
  { path: "/reports",   title: "Reports",     icon: "▧", caption: "Export & summarize",     bg: "#eef4e6", fg: "#70943b" },
  { path: "/settings",  title: "Settings",    icon: "⚙", caption: "Workspace options",      bg: "#eff0f4", fg: "#657084" },
];

export const pageTitleByPath: Record<string, string> = Object.fromEntries(
  PAGES.map((p) => [p.path, p.title === "Overview" ? "Executive overview" : p.title]),
);
