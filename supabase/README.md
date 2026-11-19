# ResiliPlan AI — Supabase setup

Postgres schema + seed for the ResiliPlan frontend and API.

## 1. Create the schema
In your Supabase project → **SQL Editor**, run:
1. `migrations/0001_init.sql` — tables, view, indexes, Row-Level-Security policies.
2. `seed/seed.sql` — reference + precomputed data (regenerate anytime with the script below).

Or with the Supabase CLI:
```bash
supabase db push                       # applies migrations/
# then paste seed/seed.sql in the SQL editor, or psql < seed/seed.sql
```

## 2. (Re)generate the seed
`seed/seed.sql` is generated from the cleaned data + phase results:
```powershell
C:\Users\sambi\miniconda3\envs\myenv\python.exe -I D:\SCA\Project\supabase\seed\seed_export.py
# optionally push straight to Supabase (needs SUPABASE_URL + SUPABASE_SERVICE_KEY):
C:\Users\sambi\miniconda3\envs\myenv\python.exe -I D:\SCA\Project\supabase\seed\seed_export.py --push
```

## 3. Tables (what the frontend reads)
| Table | Rows | Purpose |
|---|---|---|
| `nodes` | 12 | network nodes (family, role, echelon) |
| `arcs` | 11 | links + lead time + `exceeds_horizon` |
| `components` | 49 | component criticality (fan-out, lead-time, risk) |
| `scenarios` | 6 | scenario catalog (`modifications` jsonb) |
| `cost_assumptions` | 13 | ASSUMED cost params + basis + ranges |
| `scenario_results` | 6 | precomputed baseline+scenario KPIs |
| `monte_carlo_summary` | 1 | Monte Carlo service distribution |
| `optimization_runs` | — | one row per solve (written by the API) |
| `v_scenario_comparison` | view | scenario comparison vs baseline |

## 4. Keys
- **anon key** → frontend. RLS allows read-all on reference tables and public inserts into
  `optimization_runs`.
- **service_role key** → the API (`SUPABASE_SERVICE_KEY`), server-side only. Bypasses RLS.
  Never ship the service key to the browser.

## 5. Security note
The provided RLS lets anyone read reference data and insert run records — appropriate for a
course/demo app. For production, restrict `optimization_runs` inserts to authenticated users
and add rate limiting.
