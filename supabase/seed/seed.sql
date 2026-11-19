-- ResiliPlan AI seed data (generated). Apply AFTER 0001_init.sql.
begin;
-- nodes (12 rows)
insert into public.nodes (node_n, family, role, echelon_level) values
  ('zp7', 'oem', 'assembly', 1),
  ('zp8', 'oem', 'demand', 0),
  ('seat-supplier_inv', 'seat', 'inv', 2),
  ('seat-supplier_prod', 'seat', 'prod', 3),
  ('seat-supplier_trans', 'seat', 'trans', 4),
  ('battery-supplier_inv', 'battery', 'inv', 2),
  ('battery-supplier_prod', 'battery', 'prod', 3),
  ('battery-supplier_trans', 'battery', 'trans', 4),
  ('gear-supplier_inv', 'gear', 'inv', 2),
  ('gear-supplier_prod', 'gear', 'prod', 3),
  ('engine-supplier_inv', 'engine', 'inv', 2),
  ('engine-supplier_prod', 'engine', 'prod', 3)
on conflict (node_n) do update set family=excluded.family, role=excluded.role, echelon_level=excluded.echelon_level;

-- arcs (11 rows)
insert into public.arcs (starting_node_i, ending_node_j, group_g, lead_time, exceeds_horizon) values
  ('zp7', 'zp8', 'car', 0, false),
  ('gear-supplier_inv', 'zp7', 'gear', 2, false),
  ('engine-supplier_inv', 'zp7', 'engine', 1, false),
  ('gear-supplier_prod', 'gear-supplier_inv', 'gear', 2, false),
  ('engine-supplier_prod', 'engine-supplier_inv', 'engine', 1, false),
  ('battery-supplier_inv', 'zp7', 'battery', 1, false),
  ('seat-supplier_inv', 'zp7', 'seat', 0, false),
  ('battery-supplier_prod', 'battery-supplier_inv', 'battery', 1, false),
  ('seat-supplier_prod', 'seat-supplier_inv', 'seat', 0, false),
  ('seat-supplier_trans', 'seat-supplier_prod', 'seat_componment', 23, true),
  ('battery-supplier_trans', 'battery-supplier_prod', 'battery_componment', 20, true)
on conflict (starting_node_i, ending_node_j) do update set group_g=excluded.group_g, lead_time=excluded.lead_time, exceeds_horizon=excluded.exceeds_horizon;

-- components (49 rows)
insert into public.components (component_p, group_g, origin_node, n_cars_using, pct_configs_dependent, gross_demand_total, cum_lead_time, risk_score, is_direct_car_component) values
  ('Q4H', 'seat', 'seat-supplier_prod', 12038, 42.99, 12038.0, 0.0, 0.0, true),
  ('componment_seat2', 'seat_componment', 'seat-supplier_trans', 12038, 42.99, 12038.0, 23.0, 276874.0, false),
  ('Q2J', 'seat', 'seat-supplier_prod', 9726, 34.74, 9726.0, 0.0, 0.0, true),
  ('componment_seat1', 'seat_componment', 'seat-supplier_trans', 9726, 34.74, 9726.0, 23.0, 223698.0, false),
  ('G0K', 'gear', 'gear-supplier_prod', 8592, 30.69, 8592.0, 4.0, 34368.0, true),
  ('G1C', 'gear', 'gear-supplier_prod', 6664, 23.8, 6664.0, 4.0, 26656.0, true),
  ('G1D', 'gear', 'gear-supplier_prod', 4210, 15.04, 4210.0, 4.0, 16840.0, true),
  ('Q4P', 'seat', 'seat-supplier_prod', 3823, 13.65, 3823.0, 0.0, 0.0, true),
  ('componment_seat3', 'seat_componment', 'seat-supplier_trans', 3823, 13.65, 3823.0, 23.0, 87929.0, false),
  ('DN4', 'engine', 'engine-supplier_prod', 3710, 13.25, 3710.0, 2.0, 7420.0, true),
  ('DG6', 'engine', 'engine-supplier_prod', 3697, 13.2, 3697.0, 2.0, 7394.0, true),
  ('G1A', 'gear', 'gear-supplier_prod', 3393, 12.12, 3393.0, 4.0, 13572.0, true),
  ('componment_battery1', 'battery_componment', 'battery-supplier_trans', 3003, 10.72, 30030.0, 22.0, 66066.0, false),
  ('componment_battery2', 'battery_componment', 'battery-supplier_trans', 3003, 10.72, 18018.0, 22.0, 66066.0, false),
  ('componment_battery3', 'battery_componment', 'battery-supplier_trans', 3003, 10.72, 12012.0, 22.0, 66066.0, false),
  ('BEV', 'battery', 'battery-supplier_prod', 3003, 10.72, 3003.0, 2.0, 6006.0, true),
  ('D83', 'engine', 'engine-supplier_prod', 3003, 10.72, 3003.0, 2.0, 6006.0, true),
  ('G1Z', 'gear', 'gear-supplier_prod', 3003, 10.72, 3003.0, 4.0, 12012.0, true),
  ('DK8', 'engine', 'engine-supplier_prod', 2828, 10.1, 2828.0, 2.0, 5656.0, true),
  ('Q1A', 'seat', 'seat-supplier_prod', 2413, 8.62, 2413.0, 0.0, 0.0, true),
  ('componment_seat4', 'seat_componment', 'seat-supplier_trans', 2413, 8.62, 2413.0, 23.0, 55499.0, false),
  ('DG8', 'engine', 'engine-supplier_prod', 2127, 7.6, 2127.0, 2.0, 4254.0, true),
  ('D33', 'engine', 'engine-supplier_prod', 1948, 6.96, 1948.0, 2.0, 3896.0, true),
  ('D64', 'engine', 'engine-supplier_prod', 1550, 5.54, 1550.0, 2.0, 3100.0, true),
  ('DQ9', 'engine', 'engine-supplier_prod', 1422, 5.08, 1422.0, 2.0, 2844.0, true),
  ('G0C', 'gear', 'gear-supplier_prod', 1286, 4.59, 1286.0, 4.0, 5144.0, true),
  ('D80', 'engine', 'engine-supplier_prod', 979, 3.5, 979.0, 2.0, 1958.0, true),
  ('DS9', 'engine', 'engine-supplier_prod', 943, 3.37, 943.0, 2.0, 1886.0, true),
  ('DK7', 'engine', 'engine-supplier_prod', 876, 3.13, 876.0, 2.0, 1752.0, true),
  ('DE5', 'engine', 'engine-supplier_prod', 827, 2.95, 827.0, 2.0, 1654.0, true),
  ('D02', 'engine', 'engine-supplier_prod', 596, 2.13, 596.0, 2.0, 1192.0, true),
  ('DP2', 'engine', 'engine-supplier_prod', 558, 1.99, 558.0, 2.0, 1116.0, true),
  ('G0L', 'gear', 'gear-supplier_prod', 537, 1.92, 537.0, 4.0, 2148.0, true),
  ('D2I', 'engine', 'engine-supplier_prod', 530, 1.89, 530.0, 2.0, 1060.0, true),
  ('DE4', 'engine', 'engine-supplier_prod', 480, 1.71, 480.0, 2.0, 960.0, true),
  ('DR8', 'engine', 'engine-supplier_prod', 350, 1.25, 350.0, 2.0, 700.0, true),
  ('DQ4', 'engine', 'engine-supplier_prod', 339, 1.21, 339.0, 2.0, 678.0, true),
  ('G0R', 'gear', 'gear-supplier_prod', 315, 1.12, 315.0, 4.0, 1260.0, true),
  ('D60', 'engine', 'engine-supplier_prod', 249, 0.89, 249.0, 2.0, 498.0, true),
  ('DB8', 'engine', 'engine-supplier_prod', 185, 0.66, 185.0, 2.0, 370.0, true),
  ('DK9', 'engine', 'engine-supplier_prod', 178, 0.64, 178.0, 2.0, 356.0, true),
  ('DN6', 'engine', 'engine-supplier_prod', 140, 0.5, 140.0, 2.0, 280.0, true),
  ('DM4', 'engine', 'engine-supplier_prod', 126, 0.45, 126.0, 2.0, 252.0, true),
  ('DB0', 'engine', 'engine-supplier_prod', 113, 0.4, 113.0, 2.0, 226.0, true),
  ('DF6', 'engine', 'engine-supplier_prod', 73, 0.26, 73.0, 2.0, 146.0, true),
  ('DN1', 'engine', 'engine-supplier_prod', 60, 0.21, 60.0, 2.0, 120.0, true),
  ('DF4', 'engine', 'engine-supplier_prod', 46, 0.16, 46.0, 2.0, 92.0, true),
  ('DE2', 'engine', 'engine-supplier_prod', 41, 0.15, 41.0, 2.0, 82.0, true),
  ('D36', 'engine', 'engine-supplier_prod', 26, 0.09, 26.0, 2.0, 52.0, true)
on conflict (component_p) do update set group_g=excluded.group_g, origin_node=excluded.origin_node, n_cars_using=excluded.n_cars_using, pct_configs_dependent=excluded.pct_configs_dependent, gross_demand_total=excluded.gross_demand_total, cum_lead_time=excluded.cum_lead_time, risk_score=excluded.risk_score, is_direct_car_component=excluded.is_direct_car_component;

-- scenarios (6 rows)
insert into public.scenarios (id, name, nature, managerial_question, modifications, is_synthetic) values
  ('baseline', 'Baseline', 'reference (no disruption)', 'What is the least-cost feasible plan under nominal conditions?', '{}'::jsonb, false),
  ('demand_surge', 'Demand surge (mid-horizon)', 'SYNTHETIC stress test', 'Demand spikes for a block of periods — which orders can still be fulfilled and at what cost?', '{"car_demand_multiplier": [{"periods": [66, 67, 68], "factor": 1.3}]}'::jsonb, true),
  ('emergency_response', 'Battery disruption + expedited recovery', 'SYNTHETIC stress test (policy option on top of supplier disruption)', 'Given the battery disruption, is the premium cost of expedited flow justified by the service improvement?', '{"arc_capacity_multiplier": [{"arc": ["battery-supplier_prod", "battery-supplier_inv"], "factor": 0.5, "periods": [64, 65, 66, 67]}], "enable_expedite": true}'::jsonb, true),
  ('material_delay', 'Gear inbound lead-time increase', 'SYNTHETIC stress test', 'Gear deliveries are delayed — what inventory/shipment adjustments mitigate late arrivals?', '{"arc_lead_time_delta": [{"arc": ["gear-supplier_inv", "zp7"], "delta_periods": 3, "periods": "all"}]}'::jsonb, true),
  ('supplier_disruption', 'Battery supplier capacity reduction', 'SYNTHETIC stress test', 'A battery supplier loses capacity for several periods — which downstream vehicles are affected and how should production adapt?', '{"arc_capacity_multiplier": [{"arc": ["battery-supplier_prod", "battery-supplier_inv"], "factor": 0.5, "periods": [64, 65, 66, 67]}]}'::jsonb, true),
  ('transport_constraint', 'Engine inbound arc capacity cut', 'SYNTHETIC stress test', 'A key inbound transport link is constrained — which material flows should be reprioritised?', '{"arc_capacity_multiplier": [{"arc": ["engine-supplier_inv", "zp7"], "factor": 0.6, "periods": "all"}]}'::jsonb, true)
on conflict (id) do update set name=excluded.name, nature=excluded.nature, managerial_question=excluded.managerial_question, modifications=excluded.modifications, is_synthetic=excluded.is_synthetic;

-- cost_assumptions (13 rows)
insert into public.cost_assumptions (parameter, scope, value, unit, basis, sensitivity_low, sensitivity_high, status) values
  ('prod_cost.car', 'per unit (group=car)', 1000.0, 'MU/unit', 'Final assembly is the most cost-intensive step; anchor value.', 700.0, 1300.0, 'ASSUMED'),
  ('prod_cost.engine', 'per unit (group=engine)', 300.0, 'MU/unit', 'Major powertrain component; ~30% of assembly anchor.', 210.0, 390.0, 'ASSUMED'),
  ('prod_cost.gear', 'per unit (group=gear)', 150.0, 'MU/unit', 'Mechanical sub-assembly; ~15% of anchor.', 105.0, 195.0, 'ASSUMED'),
  ('prod_cost.battery', 'per unit (group=battery)', 250.0, 'MU/unit', 'Battery pack assembly from cells; ~25% of anchor.', 175.0, 325.0, 'ASSUMED'),
  ('prod_cost.seat', 'per unit (group=seat)', 120.0, 'MU/unit', 'Seat assembly from components; ~12% of anchor.', 84.0, 156.0, 'ASSUMED'),
  ('prod_cost.battery_componment', 'per unit', 15.0, 'MU/unit', 'Raw battery cell/module; low unit cost, high multiplicity (20/pack).', 10.0, 20.0, 'ASSUMED'),
  ('prod_cost.seat_componment', 'per unit', 20.0, 'MU/unit', 'Raw seat component (frame/foam/trim).', 14.0, 26.0, 'ASSUMED'),
  ('transport_cost.base', 'per unit shipped on any arc', 2.0, 'MU/unit', 'Fixed handling/loading cost per unit moved.', 1.0, 4.0, 'ASSUMED'),
  ('transport_cost.per_lead_period', 'per unit per lead-time period of the arc', 1.0, 'MU/unit/period', 'Transport cost scales with transit time/distance (lead time as proxy).', 0.5, 2.0, 'ASSUMED'),
  ('holding_cost.rate_per_period', 'fraction of item production cost, per period', 0.02, 'fraction/period', '~2%/period carrying cost (≈ 25-30%/yr typical automotive).', 0.01, 0.04, 'ASSUMED'),
  ('shortage_penalty.car', 'per unfulfilled car per period late', 5000.0, 'MU/car/period', 'Set ABOVE full fulfilment cost so the optimiser prefers to serve demand; proxy for lost-sale + contractual penalty. Dominant term enforcing service.', 3000.0, 10000.0, 'ASSUMED'),
  ('expedite_multiplier', 'multiplier on transport cost for expedited flow', 3.0, 'x', 'Premium (air/priority freight) relative to standard transport.', 2.0, 5.0, 'ASSUMED'),
  ('expedite_lead_reduction', 'periods removed from an arc''s lead time when expedited', 1.0, 'periods', 'Expedited shipments arrive faster by ~1 period (bounded at >=0).', 1.0, 2.0, 'ASSUMED')
on conflict (parameter) do update set scope=excluded.scope, value=excluded.value, unit=excluded.unit, basis=excluded.basis, sensitivity_low=excluded.sensitivity_low, sensitivity_high=excluded.sensitivity_high, status=excluded.status;

-- scenario_results (6 rows)
insert into public.scenario_results (scenario_id, status, objective_mu, vs_baseline_mu, service_overall_pct, battery_service_pct, total_shortage, expedite_units, cost_breakdown, service_by_group, validated) values
  ('baseline', 'optimal', 18395031.0, 0.0, 98.22, 48.32, 1552.0, 0.0, '{"production": 9920000.0, "transport": 370717.0, "expedite": 0, "holding": 344313.9999999998, "shortage": 7760000.0}'::jsonb, '{"battery": 48.32, "engine": 100.0, "gear": 100.0, "seat": 100.0}'::jsonb, true),
  ('supplier_disruption', 'optimal', 18395831.0, 800.0, 98.22, 48.32, 1552.0, 0.0, '{"production": 9920000.0, "transport": 370717.0, "expedite": 0, "holding": 345113.9999999998, "shortage": 7760000.0}'::jsonb, '{"battery": 48.32, "engine": 100.0, "gear": 100.0, "seat": 100.0}'::jsonb, true),
  ('material_delay', 'optimal', 39837879.0, 21442848.0, 93.13, 48.32, 5975.0, 0.0, '{"production": 9256550.0, "transport": 388064.0, "expedite": 0, "holding": 318264.9999999998, "shortage": 29875000.0}'::jsonb, '{"battery": 48.32, "engine": 100.0, "gear": 84.2, "seat": 100.0}'::jsonb, true),
  ('demand_surge', 'optimal', 25088830.9, 6693799.9, 97.08, 45.99, 2704.1, 0.0, '{"production": 10826000.0, "transport": 399117.0, "expedite": 0, "holding": 343213.89999999985, "shortage": 13520500.000000002}'::jsonb, '{"battery": 45.99, "engine": 100.0, "gear": 100.0, "seat": 96.64}'::jsonb, true),
  ('transport_constraint', 'optimal', 44777951.0, 26382920.0, 91.76, 48.32, 7172.0, 0.0, '{"production": 8234000.0, "transport": 336997.0, "expedite": 0, "holding": 346953.9999999998, "shortage": 35860000.0}'::jsonb, '{"battery": 48.32, "engine": 79.93, "gear": 100.0, "seat": 100.0}'::jsonb, true),
  ('emergency_response', 'optimal', 16450508.0, -1944523.0, 98.69, 61.9, 1144.0, 1390.0, '{"production": 10022000.0, "transport": 377335.0, "expedite": 8340.0, "holding": 331172.9999999998, "shortage": 5720000.0}'::jsonb, '{"battery": 61.9, "engine": 100.0, "gear": 100.0, "seat": 100.0}'::jsonb, true)
on conflict (scenario_id) do update set status=excluded.status, objective_mu=excluded.objective_mu, vs_baseline_mu=excluded.vs_baseline_mu, service_overall_pct=excluded.service_overall_pct, battery_service_pct=excluded.battery_service_pct, total_shortage=excluded.total_shortage, expedite_units=excluded.expedite_units, cost_breakdown=excluded.cost_breakdown, service_by_group=excluded.service_by_group, validated=excluded.validated;

-- monte_carlo_summary (1 rows)
insert into public.monte_carlo_summary (id, runs, seed, service_mean, service_std, service_min, service_max, battery_service_mean, objective_mean) values
  (1, 40, 42, 97.73125, NULL, 90.26, 98.62, NULL, NULL)
on conflict (id) do update set runs=excluded.runs, seed=excluded.seed, service_mean=excluded.service_mean, service_std=excluded.service_std, service_min=excluded.service_min, service_max=excluded.service_max, battery_service_mean=excluded.battery_service_mean, objective_mean=excluded.objective_mean;

commit;
