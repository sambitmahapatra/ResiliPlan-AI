# Deployment — Path A (Vercel frontend + Render API + Supabase)

Architecture: **Vercel** serves the React app → calls the **solver API** on **Render** →
which reads the bundled dataset and persists runs to **Supabase**. Reference/precomputed
data also lives in Supabase (already seeded).

```
Browser → Vercel (app/frontend)  →  Render (app/api, FastAPI + HiGHS)  →  Supabase (Postgres)
```

## 1. Deploy the API on Render (do this first — you need its URL)
1. https://render.com → **New → Blueprint** → connect the GitHub repo. Render reads
   `render.yaml` and creates the `resiliplan-api` web service (free plan).
2. In the service's **Environment**, set:
   - `SUPABASE_URL` = `https://thhstssoidktveceuius.supabase.co`
   - `SUPABASE_SERVICE_KEY` = your Supabase **service_role** key (secret)
   - `ALLOWED_ORIGINS` = your Vercel URL once you have it (e.g. `https://resiliplan-ai.vercel.app`); use `*` temporarily if needed.
3. Deploy. Verify: open `https://<your-service>.onrender.com/api/health` → `{"status":"ok", ... "supabase_configured": true}`.

> Free tier sleeps after ~15 min idle; the first request then takes ~30–60s to wake.
> The UI shows a loading state during this, so it degrades gracefully.

## 2. Deploy the frontend on Vercel
1. https://vercel.com → **Add New → Project** → import the repo.
2. **Root Directory = `app/frontend`** (important). Vercel auto-detects Vite via
   `app/frontend/vercel.json` (build `npm run build`, output `dist`, SPA rewrite included).
3. **Environment Variables:**
   - `VITE_API_BASE` = your Render API URL, e.g. `https://resiliplan-api.onrender.com`
   - *(optional, for direct Supabase reads)* `VITE_SUPABASE_URL` = `https://thhstssoidktveceuius.supabase.co`, `VITE_SUPABASE_ANON_KEY` = your anon key
4. Deploy. Open the Vercel URL; the app should load and pull live data from the API.

## 3. Close the CORS loop
Once you have the Vercel URL, set `ALLOWED_ORIGINS` on Render to exactly that origin and
redeploy the API (or leave `*` for a course demo).

## Verify end-to-end
- Vercel URL loads the landing page.
- Dashboard shows real baseline KPIs (service 98.2%, 18,395,031 MU, battery 48.3%).
- Scenario Lab → pick a preset / move a lever → **Run optimization** → solver-verified result.
- Reports → **Export CSV** downloads the scenario comparison.
- A new row appears in Supabase `optimization_runs` after each solve.

## Secrets reminder
- **service_role** key → Render only (server-side). Never in the frontend/Vercel or the repo.
- **anon** key → fine in Vercel frontend env (public by design).
- `.env` files are gitignored; nothing secret is committed.
