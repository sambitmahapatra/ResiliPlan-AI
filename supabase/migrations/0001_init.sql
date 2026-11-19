-- ============================================================================
-- ResiliPlan AI — Supabase / Postgres schema
-- Apply in the Supabase SQL editor, or via `supabase db push`.
-- Reference tables are read by the frontend directly (supabase-js, anon key).
-- optimization_runs stores each solve (written by the API or the frontend).
-- All ASSUMED cost / disruption data is marked as such in its own columns.
-- ============================================================================

-- Supabase provides gen_random_uuid(); ensure pgcrypto just in case.
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Reference: network
-- ---------------------------------------------------------------------------
create table if not exists public.nodes (
    node_n            text primary key,
    family            text,                 -- engine / gear / battery / seat / oem
    role              text,                 -- prod / inv / trans / assembly / demand
    echelon_level     int                   -- hops to demand node zp8 (0 = zp8)
);

create table if not exists public.arcs (
    id                bigint generated always as identity primary key,
    starting_node_i   text not null references public.nodes(node_n),
    ending_node_j     text not null references public.nodes(node_n),
    group_g           text not null,
    lead_time         int  not null,        -- transport lead time (periods)
    exceeds_horizon   boolean not null default false,   -- lead_time > 14
    unique (starting_node_i, ending_node_j)
);

-- ---------------------------------------------------------------------------
-- Reference: components + criticality (49 rows)
-- ---------------------------------------------------------------------------
create table if not exists public.components (
    component_p             text primary key,
    group_g                 text not null,
    origin_node             text,
    n_cars_using            int,            -- BOM fan-out (configs that need it)
    pct_configs_dependent   numeric,
    gross_demand_total      numeric,
    cum_lead_time           numeric,        -- supply lead time to zp8 (periods)
    risk_score              numeric,
    is_direct_car_component boolean default false  -- {engine,gear,battery,seat}
);

-- ---------------------------------------------------------------------------
-- Reference: scenario catalog (6 rows). modifications is the JSON config.
-- ---------------------------------------------------------------------------
create table if not exists public.scenarios (
    id                   text primary key,
    name                 text not null,
    nature               text not null,     -- 'reference' / 'SYNTHETIC stress test'
    managerial_question  text,
    modifications        jsonb not null default '{}'::jsonb,
    is_synthetic         boolean not null default true
);

-- ---------------------------------------------------------------------------
-- Reference: ASSUMED cost parameters (no cost data in source workbook)
-- ---------------------------------------------------------------------------
create table if not exists public.cost_assumptions (
    parameter         text primary key,
    scope             text,
    value             numeric,
    unit              text,
    basis             text,
    sensitivity_low   numeric,
    sensitivity_high  numeric,
    status            text not null default 'ASSUMED'
);

-- ---------------------------------------------------------------------------
-- Precomputed results for the 6 scenarios (instant display without solving)
-- ---------------------------------------------------------------------------
create table if not exists public.scenario_results (
    scenario_id          text primary key references public.scenarios(id),
    status               text not null,
    objective_mu         numeric,
    vs_baseline_mu       numeric,
    service_overall_pct  numeric,
    battery_service_pct  numeric,
    total_shortage       numeric,
    expedite_units       numeric,
    cost_breakdown       jsonb,             -- {production,transport,holding,shortage,expedite}
    service_by_group     jsonb,             -- {engine:.., gear:.., battery:.., seat:..}
    validated            boolean default false,
    computed_at          timestamptz default now()
);

create table if not exists public.monte_carlo_summary (
    id          int primary key default 1,
    runs        int,
    seed        int,
    service_mean numeric,
    service_std  numeric,
    service_min  numeric,
    service_max  numeric,
    battery_service_mean numeric,
    objective_mean numeric,
    computed_at timestamptz default now()
);

-- ---------------------------------------------------------------------------
-- Operational: one row per solve (API or frontend writes these)
-- ---------------------------------------------------------------------------
create table if not exists public.optimization_runs (
    id                   uuid primary key default gen_random_uuid(),
    scenario_id          text,              -- null for fully custom
    is_custom            boolean not null default false,
    params               jsonb,             -- scenario modifications / cost overrides used
    status               text not null,     -- 'optimal' / 'infeasible' / ...
    objective_mu         numeric,
    service_overall_pct  numeric,
    battery_service_pct  numeric,
    total_shortage       numeric,
    expedite_units       numeric,
    cost_breakdown       jsonb,
    service_by_group     jsonb,
    validation           jsonb,             -- {all_ok, max_balance_residual, ...}
    recommendations      jsonb,             -- array of manager-facing strings
    solve_seconds        numeric,
    created_at           timestamptz not null default now(),
    created_by           text default 'anon'
);
create index if not exists idx_runs_created_at on public.optimization_runs(created_at desc);
create index if not exists idx_runs_scenario on public.optimization_runs(scenario_id);

-- Convenience view: scenario comparison vs baseline
create or replace view public.v_scenario_comparison as
select r.scenario_id, s.name, s.nature,
       r.objective_mu, r.vs_baseline_mu,
       r.service_overall_pct, r.battery_service_pct,
       r.total_shortage, r.expedite_units, r.validated
from public.scenario_results r
join public.scenarios s on s.id = r.scenario_id
order by r.objective_mu;

-- ============================================================================
-- Row Level Security
--   Reference + precomputed tables: readable by anyone (anon, authenticated).
--   optimization_runs: readable by anyone; insertable by anyone (demo app).
--   The API may instead use the service_role key, which bypasses RLS.
-- ============================================================================
alter table public.nodes               enable row level security;
alter table public.arcs                enable row level security;
alter table public.components          enable row level security;
alter table public.scenarios           enable row level security;
alter table public.cost_assumptions    enable row level security;
alter table public.scenario_results    enable row level security;
alter table public.monte_carlo_summary enable row level security;
alter table public.optimization_runs   enable row level security;

do $$
declare t text;
begin
  foreach t in array array['nodes','arcs','components','scenarios','cost_assumptions',
                           'scenario_results','monte_carlo_summary','optimization_runs']
  loop
    execute format('drop policy if exists "read_all" on public.%I;', t);
    execute format('create policy "read_all" on public.%I for select using (true);', t);
  end loop;
end $$;

-- allow public inserts of runs (course/demo app; tighten for production)
drop policy if exists "insert_runs" on public.optimization_runs;
create policy "insert_runs" on public.optimization_runs for insert with check (true);
