# ResiliPlan AI — Claude Code Frontend Implementation Specification

> **Execution brief / design contract**  
> **Version:** 1.0 — based on the **approved ResiliPlan AI V4 mockup**  ("D:\SCA\Project\resiliplan_mockup")
> **Audience:** Claude Code working inside the existing ResiliPlan AI repository  
> **Mandate:** Build a **real, integrated, production-quality frontend** for the **already implemented analytics/optimization backend** while preserving the V4 mockup's visual design **as closely as technically possible**.  
> **Primary rule:** **The mockup controls appearance; the actual repository and backend control functionality, schemas, calculations, terminology, and supported workflows.**

---

## 0. Read this before editing code

You (Claude Code) are implementing the frontend, **not initiating another analytics project**. The user has already developed the solution and backend. Your job is to inspect the repository, understand what is actually available, then deliver the UI seen in the V4 mockup **connected to real data and services**.

### Non-negotiable hierarchy of truth

1. **Visual source of truth:** `ResiliPlan_AI_Multipage_Mockup_v4.zip`, specifically the extracted `resiliplan_mockup/styles.css` and `resiliplan_mockup/app.js`; plus the V4 desktop and mobile reference screenshots.
2. **Functional source of truth:** Current repository code, existing backend endpoints, models, actual solver outputs, tests, database schema, API documentation, and real workflows.
3. **Domain/source of truth:** Existing ResiliPlan AI documentation, dataset audit, decision model, assumptions, and business logic. An earlier planning document named `ResiliPlan_AI_Problem_Statement_and_Solution_Architecture.md` is helpful context, but **must not override the subsequently completed backend**.
4. **This document:** Design constraints, user-experience requirements, integration rules, priorities, and completion criteria.

If sources conflict, **preserve the V4 look and change its content/controls to fit the actual backend**. Never invent a backend feature or change a solved mathematical model merely to satisfy a decorative mockup.

### The user's exact intent

- The site **must look like Version 4**: premium, understated, airy, polished, pastel-blue-to-pink landing area with gradient typography, cream/white application dashboards, rounded panels, delicate borders, sophisticated charts, subtle animations.
- The V4 **landing page architecture is approved**: short hero headline; **eight direct module links on the hero**; the **eight-stage "What is our solution?" methodology directly below the links, still in the hero**.
- **Do not resurrect** the removed floating dashboard preview, redundant "Explore key capabilities" overlay, an intermediary Platform page, or a prominent "Explore live demo" CTA. Users should go directly to the relevant application screen.
- You may **add, remove, or relabel functional sections as needed** to accurately represent the **already completed** project. But visual change must be surgical; the design language, proportions, patterns, typography, spacing, and overall look should remain faithful to V4.
- All mock/demo statistics and fake calculations must be replaced by **real backend data**, removed, or unmistakably marked as sample/illustrative, as appropriate.
- Build, run, integrate, test, and fix the frontend. **Do not stop at an implementation proposal, screenshots, or unconnected static pages.**

---

## 1. Reference assets — inspect these actual files

**Required files to place in or make accessible to your working repository:**

```text
frontend-reference/
├── ResiliPlan_AI_Multipage_Mockup_v4.zip
├── ResiliPlan_AI_Interactive_Mockup_v4.html
├── ResiliPlan_v4_preview_1440.png
├── ResiliPlan_v4_preview_mobile.png
└── ResiliPlan_AI_Problem_Statement_and_Solution_Architecture.md  # context, if available
```

Extract the ZIP. Its relevant contents are:

```text
resiliplan_mockup/
├── index.html         # landing page entry
├── dashboard.html
├── network.html
├── scenarios.html
├── planning.html
├── data.html
├── insights.html
├── reports.html
├── settings.html
├── platform.html      # obsolete compatibility redirect — DO NOT restore as a page
├── styles.css         # authoritative design tokens, styles and responsive rules
├── app.js             # authoritative markup hierarchy, page details and interactions
└── README.txt
```

`ResiliPlan_AI_Interactive_Mockup_v4.html` is the equivalent standalone preview. Prefer the ZIP's **separate CSS and JS** as your design and markup source: they are easier to inspect, compare, and extract into React components. Keep the standalone HTML for quick browser reference.

**Important:** The mockup code is **plain HTML/CSS/JavaScript** and includes **illustrative application logic**, not real production APIs. **Do not iframe the mockup, preserve fake scenario calculations, or ship its placeholder metrics as real results.** Rebuild the screens as maintainable frontend components while reusing the original design CSS wherever possible.

If the reference files are missing in the repository, seek them from the provided package or the user's handoff. **Do not silently create an unrelated new design from memory.**

### Inspect before building

Read all of:
- `styles.css`: global `:root` tokens, marketing CSS, application CSS, V2/V3 helper rules, and especially the **V4 override block** labeled `/* ===== V4 — direct workspace + methodology on the landing hero ===== */`.
- `app.js`: `home()`, `marketingNav()`, `SOLUTION_STAGES`, `solutionStageDetail()`, `appnav()`, `topbar()`, `dashboard()`, `network()`, `planning()`, `scenarios()`, `data()`, `insights()`, `reports()`, and `settings()`.
- V4 desktop screenshot (**1440 × 3957 px**) for composition and full landing-page content.
- V4 mobile screenshot (**390 × 844 px**) for above-the-fold behavior.
- Current backend source and its tests before drafting API types or building frontend service calls.

Create your own brief `docs/frontend/backend-contract-map.md` documenting which real endpoint/model supports each UI element. Do not assume guessed routes exist.

---

## 2. Execution workflow: inspect, map, implement, verify

Do these steps **in order**; proceed autonomously using the actual repository. Do not require the user to restate information already in project files.

### Phase A — Repository reconnaissance (mandatory)

1. Print the project directory tree, excluding dependencies, generated artifacts, large data, and secrets.
2. Determine the existing frontend framework, build tool, routing, CSS approach, chart library, state manager, package manager, TypeScript usage, lint/test tooling, and deployment conventions.
3. Locate the existing backend (FastAPI if that is what is actually in the repository), Pydantic/OpenAPI schemas if present, solver service, scenario interfaces, dataset services, dashboards/EDA services, report/export routes, authentication, and persistence.
4. Identify a reproducible way to start both backend and frontend locally, including the **correct port and API base URL**. **Do not invent environment variable values.**
5. Discover real API request/response shapes from source, `/openapi.json`, generated clients, tests, or examples; document units, nullability, dates/periods, field enumerations, pagination, statuses, and error bodies.
6. Find existing project terminology: solver objective units, inventory/flow units, customer-service metrics, node IDs, planning horizon, BOM semantics, scenario types, run lifecycle, baseline meaning, and data provenance.
7. Verify whether runs are synchronous or asynchronous, whether a job can be cancelled, and what statuses are actually exposed.
8. Identify unsupported mockup capabilities and select a truthful UI treatment: connect if feasible, otherwise **hide, disable with reason, or show "Not available"**. Never simulate success.
9. Inspect existing frontend files first; **reuse/extend them** if this avoids duplication and disruption. Do not delete working integrations or unrelated modules.
10. Capture baseline screenshots of the V4 mockup and, if applicable, current app at comparable viewport sizes.

### Phase B — Contract and screen mapping

Create a small matrix **before extensive coding**:

| UI screen | Real backend source | Data / actions required | Current availability | Integration plan |
|---|---|---|---|---|
| Dashboard | Confirm from repository | KPIs, trends, alerts, baseline/run | Verified / partial / absent | Typed frontend adapter |
| Network | Confirm | Nodes, arcs, products, flow/capacity, BOM | ... | ... |
| Scenarios | Confirm | Scenario catalog, inputs, solver invocation, run status/results | ... | ... |
| Planning | Confirm | Production, shipments, inventory, orders, cost | ... | ... |
| Data Studio | Confirm | Dataset catalog, upload, validation, audit, EDA | ... | ... |
| Insights | Confirm | Explainable actions, drivers, trace evidence | ... | ... |
| Reports | Confirm | Export types, results, assumptions, run metadata | ... | ... |
| Settings | Confirm | Display preferences, solver config if exposed | ... | ... |

Write down **what is missing**, but do not expand backend scope without a clear need. A narrow adapter or non-breaking endpoint is acceptable only if necessary and consistent with existing architecture; document it.

### Phase C — Component architecture and integration

Use the existing compatible frontend stack where possible. If no established frontend exists, prefer:

- React + TypeScript + Vite (or the project's established React framework).
- Existing `styles.css` and its token system as the initial fidelity base; introduce CSS Modules/Tailwind only in a way that does **not** alter the V4 appearance.
- React Router or the router already installed.
- Existing chart/graph library where suitable. Recharts, Plotly, ECharts, Visx, or a compatible D3 layer are all acceptable, **provided output matches V4's visual style**.
- A typed API client (`fetch`, Axios, generated OpenAPI client, or existing API layer).
- TanStack Query or the project's equivalent for server state **if already installed or justified**.
- State for editable scenario drafts separated from state for completed, validated optimization results.

Suggested structure (adapt to the repository, do not blindly overwrite it):

```text
frontend/src/
├── app/
│   ├── App.tsx
│   ├── routes.tsx
│   └── providers.tsx
├── components/
│   ├── marketing/{MarketingNav,Hero,QuickModuleNav,SolutionMethod,FeatureCards,FAQ,Footer}.tsx
│   ├── layout/{Sidebar,Topbar,PageHeader,WorkspaceLayout}.tsx
│   ├── ui/{Button,Card,Badge,MetricCard,EmptyState,ErrorState,Skeleton,Modal}.tsx
│   ├── charts/{TrendChart,Sparkline,DonutChart,CapacityHeatmap,CostBreakdown}.tsx
│   └── network/{SupplyGraph,NodeDetail,ArcDetail}.tsx
├── pages/{Home,Dashboard,Network,Scenarios,Planning,DataStudio,Insights,Reports,Settings}.tsx
├── features/
│   ├── scenarios/{ScenarioForm,ScenarioPresets,ScenarioResults,SolveStatus}.tsx
│   ├── optimization/{ProductionPlan,FlowPlan,InventoryPlan,SolverMetadata}.tsx
│   ├── data/{DatasetCatalog,DataUploader,ValidationResults,DataDictionary}.tsx
│   └── reports/{ReportBuilder,Exports}.tsx
├── services/{api,adapters,queries}.ts
├── types/{domain,api,ui}.ts
├── styles/{tokens,global,marketing,workspace,responsive}.css
└── tests/
```

**Design fidelity matters more than following this precise file tree.** Avoid a complete framework migration if the existing app is already functional and can be styled correctly in place.

---

## 3. Visual design contract — MUST look like V4

### 3.1 Brand and atmosphere

The target is a **premium modern B2B supply-chain decision platform**. Keep it restrained and elegant, not a flashy "AI sci-fi" interface.

Required design characteristics:

- **Landing:** expansive powder-blue/lavender/soft pink **pastel gradient**, very subtle bloom/glow, ample whitespace, centered hero and typography.
- **Workspace:** soft creamy/off-white canvas, white cards, delicate neutral borders, slight elevation, dark charcoal text, muted secondary text.
- **Brand:** `resiliplan` lowercase wordmark, purple-to-coral gradient square mark, indigo brand accents.
- **Typography:** `DM Sans` / `Inter` per V4 source, tight well-controlled hero tracking; smaller precise text on dashboard cards and tables.
- **Components:** gently rounded buttons and cards; fine 1-pixel borders; compact badges; generous content rhythm; consistent icon tiles.
- **Primary actions:** periwinkle/indigo filled buttons; neutral and dark alternatives per reference.
- **Interactions:** subtle hover lift, gentle color/outline transitions, smooth-but-fast feedback, accessible keyboard focus.
- **Data density:** executive dashboard is information-rich without becoming cramped or visually noisy.

### 3.2 Actual V4 color tokens

Read and preserve the exact values from `styles.css`. The main token values present in V4 include:

```css
:root {
  --bg: #f7f8f4;
  --panel: #fff;
  --panel-alt: #fbfaf6;
  --text: #181d22;
  --muted: #7f858e;
  --border: #e7e9e5;
  --blue: #5265ec;
  --blue-soft: #eef0ff;
  --purple: #a65dea;
  --pink: #f3b9d0;
  --coral: #f17f73;
  --green: #1c977b;
  --green-soft: #e5f6ee;
  --orange: #d9924e;
  --danger: #d96362;
  --radius: 17px;
  --sidebar: 244px;
}
```

For the V4 hero specifically:

```css
.hero.hero-v4 {
  background:
    radial-gradient(ellipse at 10% 22%, #d6e6f7 0, transparent 45%),
    radial-gradient(ellipse at 91% 35%, #fce0ea 0, transparent 47%),
    linear-gradient(135deg, #f8f7ff, #fffaf8 68%, #f6f5ff);
}
.gradient-text {
  background: linear-gradient(100deg, #ef8c66, #f06896 35%, #ae5cdb 65%, #5471ee);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
```

**Prefer copying the exact CSS rules** over approximating them by eye. Do not replace this palette with dark navy, saturated purple, neon colors, generic Tailwind dashboard defaults, glassmorphism overload, or stock-template styling.

### 3.3 Layout specifications from the real V4 CSS

- Marketing nav max-width approximately **1170 px**, top header height approximately **87 px**.
- Hero top padding approximately **123 px** on desktop; hero heading `clamp(39px, 4.35vw, 61px)`, line-height about `1.13`, tight letter spacing about `-3.1px`.
- Hero content centered with a max-width about **1060 px**; supporting paragraph maximum about **710 px**.
- Workspace quick-nav maximum width about **1020 px**; on desktop it is an **8-module grid in two rows of four**.
- Quick links are predominantly white, semi-translucent cards with roughly **12 px** corners, **65 px** minimum height, compact tinted icon container and small arrow.
- The hero's methodology section uses a max-width about **1190 px** and begins roughly **35 px** below the quick-nav.
- The **eight methodology cards** form a **four-column × two-row** grid on a wide desktop. Cards have small stage numbers, colored icon squares, concise explanatory text and a small footer label.
- Selected methodology card uses a fine lavender/indigo outline/glow, and its **detail panel appears immediately below** the grid.
- The solution methodology, detail panel and compact architecture strip all remain **inside the same pastel hero region**.
- App sidebar about **244 px**, collapsible; app content with generous white space and tidy compact KPI cards.
- Preserve the V4 exact responsive rules and tighten only where necessary for actual content.

### 3.4 Motion and micro-interactions

Keep the interactions consistent with V4:

- Hover lift for module links, action buttons and cards (typically a few pixels, never jumpy).
- Animated but restrained color/outline transitions.
- Click/select styling for methodology stages, chart range tabs and filters.
- Smooth dropdowns and modals; lightweight loading skeletons and progress.
- Button loading states during real API calls, never fake "run completed" after a timeout.
- Chart hover tooltips and focus states without visual clutter.
- Gentle scroll-to-section navigation for "Our solution", "Features", "Resources".
- Support `prefers-reduced-motion: reduce`; ensure all functionality works without animation.

**Never exchange design fidelity for adding excessive parallax, animation packages, gradient blobs, moving backgrounds or decorative visuals absent from V4.**

### 3.5 Responsive design

Reference sizes to validate:

| Width | Must look/function like |
|---|---|
| 1440 × 900 | Main desktop landing and workspace, same overall alignment and visual hierarchy as V4 |
| 1440 × 3957 (full page) | Complete V4 marketing composition and section ordering |
| 1024 × 768 | Compact desktop/tablet without clipped controls |
| 768 × 1024 | Tablet layouts, usable graphs and cards |
| 390 × 844 | V4 mobile screenshot: centered compact hero, **two-column** module grid, readable first portion of methodology |
| 360–440 px | No horizontal scrolling; navigation and actions remain usable |

On mobile, keep the prominent logo and a small **Open workspace** action as in V4. Hide/collapse desktop marketing nav rather than forcing all desktop links into one row. The sidebar should become a mobile drawer or equivalent accessible navigation.

### 3.6 UI elements explicitly removed by prior approval

**Do not reintroduce these** under any name:

- Decorative hero mock dashboard screenshot/card.
- Floating "Explore key capabilities" selector over a pretend dashboard.
- A required separate "Platform" marketing page between the landing page and app.
- Dual competing hero calls-to-action such as "Explore live demo" and "Discover the platform".
- A second duplicate row of navigation icons when the direct module grid already exists.
- Fake performance claims / unnamed customers / fabricated testimonials.

---

## 4. Landing page: preserve the approved layout and flow

### 4.1 Above the fold

1. Slim, spacious marketing navbar with `resiliplan` wordmark.
2. Desktop links: **Home · Our solution · Features · Resources · Dashboard**; action buttons linking to **Scenario lab** and **Open workspace** where appropriate.
3. Rounded eyebrow pill: **MANUFACTURING SUPPLY CHAIN DECISION INTELLIGENCE**.
4. Hero heading (approved): **“Smarter planning. Stronger supply chains.”** The words **“Smarter planning.”** carry the warm-to-purple-to-blue text gradient; the rest is charcoal.
5. Concise hero description. Update the copy to reflect the **real completed backend** (avoid "planned" if it is now live).
6. Small "Your workspace, one click away" line.
7. Immediately visible **module grid**, navigable without scrolling through a marketing product preview.

The eight hero module links, in V4 order:

| Row / position | Exact V4 label | Caption in mockup | Destination |
|---|---|---|---|
| 1 / 1 | Dashboard | Executive overview | Real overview route |
| 1 / 2 | Network | Supply chain map | Real network route |
| 1 / 3 | Scenarios | Disruption simulator | Real scenarios route |
| 1 / 4 | Planning | Production optimizer | Real planning route |
| 2 / 1 | Data Studio | Datasets & validation | Real data route |
| 2 / 2 | Insights | Decision intelligence | Real insights route |
| 2 / 3 | Reports | Export & summarize | Real reports route |
| 2 / 4 | Settings | Workspace options | Real settings route |

Use the reference's compact **tinted icon square + title + caption + arrow** structure and its hover behavior. Every tile must navigate to a real page, preserving React router/history behavior.

**Allowed adjustment:** Rename or replace a module **only if the real completed solution differs**, maintaining an eight-tile/two-row layout where possible. Do not leave a tile linked to non-existent functionality. If a real important capability requires a ninth module, integrate it carefully in a visually balanced grid and document the variation.

### 4.2 "What is our solution?" — in the same hero

Immediately after the module grid and **within the same background**, retain:

- Eyebrow **WHAT IS OUR SOLUTION?**
- Section title **“From raw data to better production decisions.”** with gradient emphasis.
- Short, correct explanation of the actual workflow: data preparation → analytics → scenario engineering → MILP optimization → validation → actionable decisions.
- A compact, truthful status line. Change mockup phrases like "planned data pipeline" and "solver integration planned" to the real implementation status.
- Eight clickable methodology stages arranged 4×2:

| Stage | V4 title | Meaning |
|---|---|---|
| 01 | Understand the source | Data audit, business problem, nodes/arcs/products/BOM/demand |
| 02 | Clean & validate | Key integrity, missing values, physical consistency and cleaning evidence |
| 03 | Standardize & structure | Canonical units/IDs/periods and BOM-consistent model data |
| 04 | Explore the network | EDA: demand, capacity, lead times, inventory and dependencies |
| 05 | Engineer scenarios | Disruption cases and justified model inputs |
| 06 | Optimize with MILP | Existing real mathematical model and solver |
| 07 | Validate & compare | Constraints, solver status, baseline-vs-scenario outcomes |
| 08 | Deliver the solution | Integrated decision intelligence app / reports |

Each card should show stage number, small colored icon, one-line title, short explanation, an all-caps short label and subtle arrow.

Clicking a card updates a **single detail panel below the grid** with:
- Stage name/number.
- Clear purpose of that stage.
- Actual implemented steps and outcomes.
- Real expected/available artifacts (do not falsely present a missing feature as implemented).
- An **Explore** link to the closest corresponding app screen.

The active state should look like V4, including the slender gradient highlight and selected outline. Preserve stage switching with keyboard support; semantic `<button>` preferred with `aria-pressed`.

Below the detail panel, retain the compact architecture flow (source manufacturing data → analytics/optimization → managerial decisions). Adapt labels to the actual backend, without changing its visual treatment.

### 4.3 Sections following the hero

Preserve the broad V4 sequence and appearance:

1. **Features / capabilities**: clean pale background; six white cards with tinted illustrations and descriptive, business-focused copy.
2. **Technical credibility / engine explanation**: white/light section with disciplined typography, short stack badges, and direct link to a real application page; update text to actual technologies.
3. **FAQ**: concise accordion with correct answers about data, optimization method, supported uploads, solution status and automation/AI claims.
4. **Dark CTA strip**: charcoal/near-black section encouraging people to make a planning decision, linked directly to the actual workspace—not an intermediate Platform page.
5. **Minimal footer**: small `resiliplan` logo, accurate academic/project note, app link.

Copy may change substantially if required by the actual application. **Do not radically alter the layout, add huge new marketing sections or insert generic testimonials**. Keep academic/industry claims evidence-based; no false claims of "real-time", "AI autonomous agent", "guaranteed savings" or deployed customers.

---

## 5. Workspace shell — common to all modules

The application should look like the V4 cream-colored finance-style dashboard inspiration, adapted to manufacturing analytics.

### Sidebar

Keep the narrow, calm left-hand navigation with:

- Brand and small **DECISION INTELLIGENCE** subtitle.
- **Workspace** group: Overview / Supply network / Production planner / Scenario lab.
- **Manage** group: Data studio / Intelligence / Reports / Settings.
- Active link with pale lavender highlighting.
- Subtle hover, clear selected state, and small **LAB** badge on Scenarios if appropriate.
- Real, working sidebar collapse control; preserve state if sensible.
- Small bottom helper/context card and user/project indicator. Never fake a signed-in identity; display real account details only if authentication exists.

### Top bar

Maintain breadcrumb `Workspace / Current page`, compact search affordance, status badge, icon actions, avatar/account indicator. Integrate with real functionality where available.

- Search: implement real navigation search at minimum; data search only if backend supports it. `Ctrl/Cmd + K` may open command palette as in mockup.
- Status: if live backend health is known, use truthful connection/solver status. **Do not say "Demo active" or "Live optimization" if not verified**.
- Notifications: show actual alerts or an honest empty state; never fabricate Tier-1 incidents.
- Theme: functional light/dark toggle if retained; maintain legible chart contrast and controls. **Default light** to match the approved reference.
- Responsive: collapsible sidebar on desktop, mobile menu/drawer and operable close behavior.

### Shared component behavior

- Consistent page headers (title, subtitle, action cluster).
- KPI metric cards with labels, units, comparison periods, change indicators and optional tiny sparklines.
- Card headers with short descriptive subtitles.
- Primary action in indigo; alternate actions neutral/dark.
- Tables: sticky header if needed, row hover, constrained text widths, loading and empty states, accessible horizontal scrolling on small screens.
- Tooltips with full definitions, units, timestamp/horizon and data provenance for calculated metrics.
- Skeletons / spinners matching V4's unobtrusive style.
- No generic alerts or crude browser `alert()` popups; use styled messages and accessible dialog/toast patterns.

---

## 6. Screen-by-screen functional implementation contract

**Core rule for every screen:** preserve the overall V4 layout and visual composition, but map all meaningful data/actions to real backend contracts. Only expose capabilities that exist or are completed as part of the agreed frontend integration.

### 6.1 Dashboard / Overview

**V4 visual anchor:** page heading; top row of **four KPI cards**; left performance time-series panel; right circular fulfilment visual; lower operational dashboards/tables; small filters/range tabs.

Expected sources, **if supported by backend**:

- On-time fulfilment / delivery rate (with definition of denominator and horizon).
- Total objective cost and cost components in the actual model's currency/units.
- Production/capacity utilization by node/period.
- At-risk orders, backorders or unmet-demand units.
- Trend or period-level production/service charts, if backend returns valid time series.
- Baseline versus solved scenario comparison and operational alerts.
- Latest run ID, solver state, planning horizon, timestamp and dataset version.

Rules:

- The mockup contains values such as **96.4%, ₹2.42M, 83.7%, 128** and mock delivery trajectories. They are **NOT source truths** and must not appear as real numbers.
- Derive every KPI from an actual backend response or a fully specified, tested frontend computation from returned raw data. Prefer backend aggregates for consistency.
- Use the backend's true currency; do not assume INR because the mockup uses `₹`.
- If the problem has planning periods rather than dates, label them **Period 61–74** or the actual returned horizon; never silently invent calendar dates.
- Period tabs (`7D`, `14D`, `30D`) only if the dataset supports them. Otherwise replace with meaningful period filters while preserving the same tab visual.
- Include state for **No validated run yet** with a prompt to load data/run a scenario; do not fill gaps with fake statistics.

### 6.2 Supply network

**V4 visual anchor:** wide network diagram with softly colored Tier-2, Tier-1 and OEM nodes, curved/straight connecting arcs, selected-node detail panel, compact legends and operational cards.

Map from real data:

- Nodes (IDs, roles, labels, groups and types where available).
- Directed arcs with transport lead times, capacity, product/group restrictions where available.
- BOM dependency context, not merely pretty arrows.
- Selected scenario's material flows/utilization/constraints if returned by optimizer.
- Selected node information: input/output products, status, inventory, capacity, utilization and dependencies, only where the backend supports those measures.

Interactions:

- Click/focus a node → details panel; click/focus arc → valid transport details.
- Pan/zoom/fit/reset when graph size warrants it; keep the clean reference look rather than a cluttered force-directed spaghetti diagram.
- Filters by node, supplier tier, period, product group, scenario, and bottleneck status **where real fields support them**.
- Responsive graph container; labels never overflow nodes; meaningful legends.
- If full network is very large, group/aggregate only in a manner consistent with BOM/flow semantics, with clear indication of aggregation.

**No hardcoded, imaginary factories, node utilizations, or incidents**. Use actual graph metadata; examples should be explicitly flagged as sample records.

### 6.3 Scenario Lab — core interactive feature

**V4 visual anchor:** parameters/sliders, preset controls, KPI impact cards, comparison chart, recommendation/callout, prominent run button.

Map real backend scenario inputs to appropriate controls:

- Supplier/production capacity reduction.
- Lead-time shift or supplier delay.
- Demand change by relevant product/period.
- Arc/transport capacity reduction.
- Expediting or alternative flow **only if supported in the optimization model**.
- Dataset/run/baseline selection and scenario name.

**Critical implementation distinction:**

1. **Draft scenario state:** user edits inputs/sliders; controls update immediately and show the chosen values.
2. **Solve request:** user clicks **Run optimization** (or real name), triggering backend validation and solving.
3. **Solver state:** show valid statuses returned by backend — queued, running, completed, time-limited, infeasible, failed, cancelled **only if actually supported**.
4. **Solved result:** replace KPI values, plots and recommendations with the **returned** optimization result; never substitute the mockup's heuristic.
5. **Comparison:** compare scenarios against a well-defined baseline sharing a compatible dataset/model/units/horizon.

The mockup's `calc()` is a **fake heuristic** using slider values. `runDemo()` uses a timeout and a toast. **Delete/replace both behaviors.** A slider movement must **not** pretend that the MILP has already reoptimized. If a quick estimate is supported, distinguish **preview estimate** from **solver-confirmed result**.

Advanced UX:

- Config validation with units, ranges and selected node/arc identifiers.
- Presets and reset, aligned to backend-supported fields.
- Run button disabled during incompatible state; spinner/progress with accessible status text.
- Clear error messages and actionable suggestions for timeouts/infeasibility; no made-up plan on solver failure.
- Store/restore scenario state only through supported backend persistence or documented local persistence; show clear indication of where saved data lives.
- Support comparing a baseline and one or more scenarios if the backend provides it.
- Show solver status, objective, objective units, run time, MIP gap (if relevant), and model assumptions in results details.
- Do not expose credential material or internal solver traces to unauthenticated clients.

### 6.4 Production planning / Optimization results

**V4 visual anchor:** operations planning dashboard with production schedule, network/flow summaries, cost breakdown, constraint/capacity views and export actions.

Build directly from solved output:

- Production quantities by node, product and period.
- Inventory positions over time, permitted stock limits, shortages/backorders.
- Material dispatches and arrival dates/periods respecting actual lead times.
- Production and transportation capacity use, binding constraints and bottleneck identification if supported.
- Objective cost components, baseline comparison, recovery actions.
- Orders fulfilled and unmet demand with relevant business definitions.

Interactivity:

- Filters: scenario/run, node, product/group and period.
- Timeline/Gantt-like schedule if backend has activity time indices; otherwise use a faithful table/heatmap layout based on available data.
- Click a product or period to drill down into its relevant BOM/flow context when supported.
- Export filtered results through real backend export or validated client-side generation from returned data.
- No fictitious "optimal" badge unless solver has actually proved optimality.

For huge product sets, use backend pagination / virtualization / filter-first workflows. Avoid rendering tens of thousands of rows or arcs simultaneously.

### 6.5 Data Studio / Data quality / EDA

**V4 visual anchor:** dataset metadata cards, compact source table catalog, file import card, validation checklist and sample data preview.

Source context (verify against actual backend): the original automotive workbook is `2020_dataset_OfAutomotiveProductionNetwork.xlsb` and the planning documents describe 12 worksheets:

`products`, `nodes`, `nodes_inflow`, `arcs`, `capacity_at_arc`, `max_flow_product_per_arc`, `max_flow_group_per_arc`, `operations`, `BOM`, `demands`, `initial_inventories`, `initial_flows`.

Features should be implemented only as supported by existing backend:

- Load bundled sample/validated dataset without requiring user uploads.
- File upload/ingestion with supported type(s): `.xlsb`, `.xlsx`, `.csv`, ZIP or backend-defined format as applicable. Show actual supported formats, not imagined ones.
- Dataset catalog, provenance, time period, schema, row counts and data dictionary.
- Cleaning and validation statuses: missing keys, referential integrity, BOM consistency, temporal alignment, nonnegative quantities, unit compatibility and network connectivity.
- EDA visualizations: demand, capacity, inventory, lead time, product group distribution, BOM depth/dependencies, actual bottlenecks if computed.
- Data preview with pagination, sort/filter, correct handling of large files, and no unbounded browser parsing.
- Validation report export where supported.

**Important:** The V4 mockup only previews **CSV locally**, and does not parse XLSB itself. The production UI must call the **existing server ingestion** when applicable. Do not recreate the complex Python cleaning pipeline in JavaScript or imply that local CSV preview equals validated data ingestion.

For upload errors: show file size/type limits from actual backend, precise row/column messages if returned, and an honest error path. Never announce successful import until server confirms it.

### 6.6 Insights / Explainability

**V4 visual anchor:** prioritized action cards on the left, cost-service trade-off visualization and explanatory cards on the right.

A useful insight must answer:

- **What happened?** Solver-observed shortage, bottleneck, cost driver, lead-time exposure or service drop.
- **Why?** Identify supporting nodes/arcs/products/periods, relevant constraints and assumptions.
- **What should the manager do?** Describe a traceable action from the optimized plan.
- **What is the trade-off?** Cost, service and feasibility implications.
- **How reliable is the claim?** Solver status, scenario inputs, assumed parameters, data quality and known limits.

If the backend exposes rules/insights, render those. If it exposes only numerical results, a deterministic, auditable frontend formatter may convert those into **carefully qualified** managerial summaries; do not introduce speculative generative text or fabricate root causes.

- Replace "High priority" placeholders with a reproducible ranking/threshold if one exists.
- Show Pareto frontier only if the backend actually computes non-dominated points; otherwise use a legitimate cost-service comparison chart.
- Never invent confidence percentages for MILP outcomes.
- Link insights to the appropriate run, network view, planning table or scenario details.

### 6.7 Reports / Exports

**V4 visual anchor:** a clean management brief preview, included-section toggles, metadata/audit panel, export controls.

Produce accurate downloadable outputs supported by backend:

- Executive summary: data source, context, assumptions, selected scenario, important KPIs.
- Baseline versus scenario: cost and service with correct definitions.
- Production schedule and material flow plan where returned.
- Validation: solver status, objective, gap, run time, constraint check, model/data version.
- Assumptions and data limitations.
- Exports: CSV / Excel / PDF only if actually supported (or add faithful browser print output when feasible).

All report options must affect report content. **Do not wire multiple options to the same generic "sample CSV" export.** Avoid spreadsheet-formula injection in CSV outputs, and avoid exporting empty/placeholder data as an actual result.

### 6.8 Settings

**V4 visual anchor:** toggles, preferences, model information card and clean explanatory notices.

- Light/dark mode, collapsible sidebar, reduced motion preference and view density if supported.
- API status / backend connection state from actual health check, where available.
- Model information: **read actual backend metadata**, not hardcoded claims (the project plan proposed Pyomo + HiGHS; verify current backend).
- Solver controls: time limit, allowable gap, scenario defaults, etc. only where exposed and authorized by backend.
- Save settings to app/user storage supported by current project, or local storage for display-only preferences, with transparency.
- No pretend account controls, integrations, notifications, or successful settings-save messages.

---

## 7. Real backend integration — strict rules

### 7.1 No invented contracts

The endpoints below are **capability categories, not prescribed URLs**. Use the repository to map exact methods and paths:

```text
Dataset/catalog:         actual routes for datasets and active dataset metadata
Data validation:         actual routes for upload, audit, validation and EDA
Network:                 actual routes for nodes, arcs, BOM relationships and attributes
Scenarios:               actual routes for scenario inputs, presets, CRUD if available
Optimization:            actual routes for solve submission, status and results
Planning outputs:        actual routes for production/flow/inventory/backorder records
Insights:                actual routes or actual derived summary rules
Reports/exports:         actual routes for CSV/PDF/etc.
Health/configuration:    actual backend health / metadata if supported
```

Do not create a frontend around guessed names like `/api/optimize` unless that path is verified in the repository.

### 7.2 Implement typed adapters

A **view model / adapter layer** should transform raw backend data to stable UI shapes, while preserving provenance and units.

Example **conceptual interface** (illustrative, NOT an assumption about the backend schema):

```ts
type ResultState = 'idle' | 'loading' | 'ready' | 'empty' | 'error';

interface MetricView {
  key: string;
  label: string;
  value: number | string | null;
  unit?: string;
  sourceRunId?: string;
  definition?: string;
  note?: string;
}

interface OptimizationResultView {
  runId: string;
  datasetId: string;
  scenarioId: string;
  solverStatus: string;
  isProvenOptimal: boolean;
  objective?: number | null;
  objectiveUnit?: string;
  mipGap?: number | null;
  runtimeSeconds?: number | null;
  metrics: MetricView[];
  // Actual production/flow/inventory records are mapped separately.
}
```

The concrete TypeScript types **must be derived from actual API schemas**. Do not force the backend into this example if its concepts differ.

### 7.3 Data correctness and governance

- Distinguish **observed data**, **assumed inputs**, **scenario modifications**, **solver outputs**, **post-processed KPIs**, and **UI-only demo/sample data**.
- Maintain units. Never mix individual products, shipment lots, transport capacity units, percentage points and percentage changes.
- Preserve periods and timestamps. Do not map index `61` to "January" unless the backend defines that mapping.
- Preserve numeric precision needed to reconcile totals. Format only at display time; allow users to inspect unrounded exports.
- Treat solver outcomes accurately: optimal, feasible-not-proven-optimal, time limit, infeasible, invalid data, run failed.
- Show the baseline policy/definition when claiming improvements. A reoptimized baseline and a disrupted case must be compared on a defensible basis.
- No synthetic "savings", ROI, service improvement, cost currency or business conclusions presented as factual.
- Prefer backend-computed KPIs; if frontend derives them, unit-test the exact formulas against known cases.

### 7.4 API and job UX

- Centralize API base URL in environment configuration; do not hardcode localhost into production bundles.
- Propagate loading, empty, validation error, authorization error, offline, timeout and server error states consistently.
- For lengthy solves, use actual polling/WebSocket/SSE if the backend provides it. Do not poll endpoints that do not exist.
- Respect cancellation semantics and concurrency. Avoid accidental duplicate solve submissions.
- Keep the last valid result visible (marked as previous scenario) when a new solve fails, or clear results visibly; never silently display stale results as current.
- Use backend-compatible caching keys that include dataset, scenario/run, parameters and horizon when relevant.
- Ensure export operations reference the **correct solved run**.
- Authentication, session tokens, CSRF/CORS policy, permissions and secrets must follow existing backend contracts.

---

## 8. Charts and data visualization — retain V4 appearance

The original mockup uses thin SVG trend lines, small sparklines, clean concentric/donut charts, tasteful horizontal/vertical bars, a light network diagram, capacity/pivot-like views, and responsive tables.

Use the real data while retaining:

- Clear typography, no thick axes or distracting gridlines.
- Indigo/periwinkle as primary series; muted coral/peach as comparison; green for positive, warm orange for warnings.
- Subtle gradients under trends if used in the reference.
- Rounded chart panels and compact legends.
- Hover tooltips explaining metric, period, unit, scenario and source.
- Responsive chart boundaries and axis label truncation.
- When highlighting a capacity problem, use meaningful labels, not an arbitrary alarming shade.

**Never fabricate the time axis** or generate random chart data just to fill a dashboard. If missing, show a beautiful empty state within the existing card geometry.

For network graphs, preserve node roles, directedness, capacities and product/period meaning. V4's manually laid-out SVG is a design example, not proof that the real network has only the visible seven node labels.

---

## 9. Authentication, safety, accessibility and reliability

### Accessibility

- Semantic headings, navigation landmarks and correct tab order.
- Visible keyboard focus for links, buttons, filters, cards and dialog controls.
- Methodology stage selection via real buttons and `aria-pressed`.
- Screen-reader labels for icon-only buttons, status badges, charts and download links.
- Color is never the sole carrier of meaning for KPIs, warnings or validation states.
- Respect `prefers-reduced-motion` and contrast needs.

### Security and correctness

- No API keys, dataset secrets, solver credentials or database service keys in the browser or repository.
- Strictly validate file extension/type/size and rely on server validation for actual acceptance.
- Escape or sanitize backend-supplied strings/labels; do not introduce XSS through SVG or chart tooltips.
- Avoid logging personally identifying data, secrets, request bodies or raw sensitive uploads.
- Confirm that CSV export neutralizes formula-like content where applicable.
- Do not expose administrative backend operations merely because a mockup has a settings tile.

### Performance

- Avoid redundant API requests, excessive chart rerenders and huge browser-side network layouts.
- Use pagination or virtualization for product/BOM datasets and long plan tables.
- Dynamic import heavy chart/network modules where practical.
- Keep first landing-page paint quick and maintain interactions at modest hardware budgets.
- If a solve takes substantial time, show a real progress state and retain navigability.

---

## 10. Visual verification protocol (mandatory)

**This is a pixel-fidelity project**, not an opportunity to explore alternate styles. Use the V4 source and screenshots for structured comparison.

### Test procedure

1. Start the original V4 mockup locally and capture fresh reference shots at the target viewports.
2. Start the integrated frontend with its actual backend and seed/sample dataset.
3. Capture the same regions and viewports for comparison.
4. Compare **header placement, hero height, headline wrapping, gradient locations, module grid rows, methodology card sizing/spacing, selected stage detail panel, section transitions, and footer**.
5. Compare dashboard: sidebar width and active nav, topbar height, KPI row, chart panel widths, card radii, border colors and table density.
6. Fix visible inconsistencies, iterate and verify again.
7. Capture mobile views and verify the two-column module grid, buttons, title wrapping and responsive sidebar.

Use Playwright/Cypress or repository's established browser test framework if available. Automated screenshot diff is useful, but qualitative inspection still matters because dynamic data will change chart shapes and text lengths.

### Design acceptance criteria

- [ ] At 1440 px wide, the landing is immediately recognizable as **V4**, not a new site with similar colors.
- [ ] The approved hero headline and palette, typography and airy centered composition remain.
- [ ] Exactly one prominent direct-workspace navigation system in the hero, with the approved eight V4 modules unless justified by real backend constraints.
- [ ] The eight-step methodology lives **inside the hero**, directly after the module grid.
- [ ] No floating decorative fake dashboard, no overlay capability selector, and no intermediate Platform page.
- [ ] Methodology selection matches the active-card/detail-panel reference visually.
- [ ] Feature cards, technical section, FAQ, dark CTA and footer follow the same visual sequence.
- [ ] App sidebar, topbar, cards, charts, buttons and tables preserve V4 look.
- [ ] Dark mode, if present, is a secondary functional preference; light mode is the reference/default.
- [ ] Mobile has no sideways overflow and retains the V4 visual hierarchy.
- [ ] All interactions are keyboard-usable and responsive.

---

## 11. Functional acceptance criteria

A visually exact site that is not connected to real services **fails** this task.

### Required end-to-end journeys

**Journey A — Evaluation from fresh visit**

1. Open landing page.
2. Read what the solution does.
3. Select a module in the hero (e.g., Dashboard).
4. See the real current dataset/run, a meaningful empty state, or an actionable sample-data load—not fake KPIs.
5. Navigate between modules using sidebar, breadcrumbs/search and browser Back/Forward.

**Journey B — Data to model**

1. Visit Data Studio.
2. Load the sample data or upload a backend-supported dataset.
3. Receive genuine server validation/cleaning outcomes and accurate metadata.
4. Browse the network, exploratory charts or source catalog as supported.

**Journey C — Scenario to recovery decision**

1. Choose baseline or dataset.
2. Modify a supported disruption input.
3. Submit an actual solve request.
4. Observe real backend job status, including valid failure states.
5. See solver-confirmed cost, service, inventories, flows, production and recommendations where available.
6. View baseline comparison and click through to relevant plan/network views.
7. Export an accurate result linked to that run.

**Journey D — Honest failure handling**

- Invalid file → meaningful validation error and no fake success.
- Missing/invalid scenario parameter → visible field error.
- Infeasible model → explicit status and useful explanation, **not** an "optimal" result.
- Solver timeout / non-optimal incumbent → accurate status and gap if available.
- Backend unavailable → graceful recovery state.
- No run yet → clear informative empty state, not illustrative production numbers silently shown as real.

### Functional checklist

- [ ] All primary nav links route to functional screens without `404` or missing assets.
- [ ] Landing anchor links scroll to the actual section and behave with browser navigation.
- [ ] APIs are verified from actual backend source, documented and type-mapped.
- [ ] Dashboard measures are computed from real data with proper units and lineage.
- [ ] Network nodes and arcs come from actual dataset/models.
- [ ] Scenario controls reflect actual supported solver parameters.
- [ ] Scenario run button invokes the backend, not a fake timeout.
- [ ] Solver state and optimality claims are truthful.
- [ ] Planning view reads actual solver decisions.
- [ ] Insights explain actual decisions with traceable supporting evidence.
- [ ] Reports export the right scenario/run and respect chosen sections.
- [ ] Settings persist actual UI preferences.
- [ ] Loading/empty/error/offline states are styled and tested.
- [ ] No mock data without an explicit demo/sample label.
- [ ] No exposed backend credentials or unsafe upload behavior.

---

## 12. Tests and commands

Adapt commands to the repository's actual package manager and tooling. **Do not claim to have run a command unless you actually ran it.**

Minimum verification:

1. Frontend install/build and typecheck/lint.
2. Unit tests for API adapters, KPI mapping, numeric unit formatting, scenario draft-to-request translation, and result-state classification.
3. Component tests for hero module navigation, methodology selection, sidebar/theme/search, filters, dialogs and empty/error states.
4. API integration tests with the actual backend (or backend-defined integration-test fixtures) for key screens.
5. Browser E2E: landing → data → scenario → solve → planning → export.
6. Browser E2E for invalid upload and infeasible/failed/timeout solve responses where such states can be simulated safely in test fixtures.
7. Screenshots and responsive checks at all target viewport widths.
8. Confirm backend tests remain passing (don't alter analytical behavior unexpectedly).

Useful commands to discover rather than assume:

```bash
# Examples only; inspect project structure first.
find . -maxdepth 3 -type f | head -100
# Read package.json / pyproject.toml / README / backend API schemas.
# Use the repository's documented install, dev, test and build commands.
```

Do not use unexplained blanket `npm install latest` or large unrelated dependency upgrades just to implement the UI.

---

## 13. Deliverables and handoff

At the end, provide the user with:

1. **A fully working frontend** integrated into the existing repository, not just sketches or a static HTML page.
2. A concise **implementation summary** mapping each V4 screen to its actual backend sources and noting justified differences from the mockup.
3. A concise **list of changed files**, plus build/test results and any known failures.
4. Clear local start/run instructions and the correct environment variable *names* (never expose values/secrets).
5. Real screenshots of desktop landing, mobile landing, dashboard, scenario lab and at least one solved-result screen.
6. A small `docs/frontend/visual-parity.md` containing reference-to-implementation comparison, changed sections, and why.
7. A small `docs/frontend/api-integration.md` listing only **verified** endpoints, request/response schema names and their UI usage.
8. An honest list of backend capabilities that are not available and the UI treatment chosen (hidden, disabled or informative empty state).

Keep these docs concise and accurate; this main specification is the source for the comprehensive requirements.

---

## 14. Priority and decision rules if trade-offs are necessary

1. **Correct integration, no fabricated results.**
2. **Visual fidelity to approved V4.**
3. **Working core decision flow:** data → scenario → optimization → recovery plan → export.
4. **Accessible navigation and responsive layout.**
5. **Secondary UX polish**, nonessential charts/animations and optional enhancements.

These are **not** permission to redesign. For example:

- If the backend lacks a mock KPI, preserve the card style but replace it with a meaningful real KPI or a designed empty state.
- If the backend uses a different solver, update the technical content and status text but keep the page presentation intact.
- If a real solver requires another scenario field, add it to the V4-styled parameter card rather than replacing the entire page.
- If the original 14-period assumption no longer holds, render the backend's actual horizon and update the relevant labels.
- If backend output contains thousands of product records, use search/pagination/virtualization without changing the broad screen composition.
- If the project now has an extra validated data-cleaning/EDA workflow, connect it within Data Studio or the solution methodology **using matching V4 cards/panels**.
- If the app does not support AI/ML prediction, do not imply ML/AI performs predictions; the brand can remain "ResiliPlan AI" if approved, with honest explanation of optimization and scenario analytics.

## 15. Final instruction to Claude Code

**Implement now, using the actual V4 HTML/CSS/JS as your visual blueprint and the repository's existing backend as your functional blueprint.** First inspect the codebase and map verified interfaces, then build the integrated React (or existing framework) pages, connect all supported functionality, and validate visual parity against the V4 desktop/mobile screenshots.

**The exact V4 appearance is a design constraint, not an inspiration board.** You are allowed to change content and add/remove modules **only to reflect the real finished project**. Never produce a different visual concept, an unconnected static mockup, made-up KPIs, or non-functional controls.

**Definition of done:** A user can open a site that looks like ResiliPlan V4, understand the real data/analytics/optimization methodology immediately from the landing page, jump directly into each functional module, run a real manufacturing disruption/optimization workflow using the existing backend, inspect and export authentic recommendations, and navigate the whole experience with reliable responsive behavior.
