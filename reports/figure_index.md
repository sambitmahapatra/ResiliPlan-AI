# Figure Index — ResiliPlan AI

Every report-bound figure and table-as-image is registered here automatically by `src/utils/figures.py`. Do not edit by hand.

| name | caption | phase | source | saved (UTC) |
|---|---|---|---|---|
| p1_bom_structure | P1 — BOM structure: identity rows, closure, cycles, nesting depth | P1 | p1_data_audit.py | 2026-11-19 09:07:17 |
| p1_count_reproduction | P1 — Reproduction of audited counts (expected vs observed) | P1 | p1_data_audit.py | 2026-11-19 09:07:11 |
| p1_duplicate_keys | P1 — Candidate-key uniqueness (duplicate rows per key) | P1 | p1_data_audit.py | 2026-11-19 09:07:15 |
| p1_missing_values | P1 — Missing-value & dtype summary (all columns) | P1 | p1_data_audit.py | 2026-11-19 09:07:14 |
| p1_period_coverage | P1 — Period coverage by time-indexed table | P1 | p1_data_audit.py | 2026-11-19 09:07:19 |
| p1_products_per_group | P1 — Product count by group | P1 | p1_data_audit.py | 2026-11-19 09:07:22 |
| p1_referential_integrity | P1 — Referential integrity across tables | P1 | p1_data_audit.py | 2026-11-19 09:07:16 |
| p1_rows_per_sheet | P1 — Rows per worksheet (log scale) | P1 | p1_data_audit.py | 2026-11-19 09:07:21 |
| p1_sheet_overview | P1 — Workbook sheet overview (rows, columns) | P1 | p1_data_audit.py | 2026-11-19 09:07:10 |
| p1_value_ranges | P1 — Value ranges & unit sanity for key numeric fields | P1 | p1_data_audit.py | 2026-11-19 09:07:19 |
| p2_clean_manifest | P2 — Cleaned table manifest (data/clean/) | P2 | p2_clean_and_explode.py | 2026-11-19 09:20:58 |
| p2_component_demand_by_group | P2 — Exploded component demand by group × period (gross requirements) | P2 | p2_clean_and_explode.py | 2026-11-19 09:21:02 |
| p2_component_demand_per_period | P2 — Exploded component demand per period (stacked by group) | P2 | p2_clean_and_explode.py | 2026-11-19 09:21:03 |
| p2_connectivity | P2 — Network connectivity proof | P2 | p2_clean_and_explode.py | 2026-11-19 09:20:58 |
| p2_explosion_reconciliation | P2 — BOM explosion reconciliation vs raw car demand | P2 | p2_clean_and_explode.py | 2026-11-19 09:21:04 |
| p2_node_echelons | P2 — Nodes by echelon level (hops to demand node zp8) | P2 | p2_clean_and_explode.py | 2026-11-19 09:20:59 |
| p3_arc_lead_times | P3 — Transport lead time by arc | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:54 |
| p3_arc_utilization_heatmap | P3 — Arc utilization heatmap (static same-period demand/capacity proxy; lead-time shifting, inventory and initial in-transit flows are applied only in the P5 MILP, which may resolve apparent >1.0 pressure) | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:55 |
| p3_arc_utilization_summary | P3 — Arc utilization summary (static same-period proxy; mean/max, periods over capacity). Pressure indicator only — resolved in the P5 MILP. | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:56 |
| p3_component_criticality_top | P3 — Top-15 components by BOM fan-out | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:55 |
| p3_criticality_ranking | P3 — Component criticality ranking (fan-out, demand, lead-time exposure) | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:55 |
| p3_criticality_vs_leadtime | P3 — Criticality vs lead-time risk quadrant | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:55 |
| p3_network_map | P3 — Multi-echelon network map with lead times | P3 | p3_eda_network_criticality.py | 2026-11-19 09:27:54 |
| p4_cost_assumptions | P4 — Assumed cost parameters (ALL ASSUMED; basis + sensitivity ranges) | P4 | p4_cost_and_scenarios.py | 2026-11-19 09:32:37 |
| p4_scenarios_summary | P4 — Disruption scenarios (all SYNTHETIC stress tests) | P4 | p4_cost_and_scenarios.py | 2026-11-19 09:32:37 |
| p5_arc_utilization_actual | P5 — Baseline actual arc utilization (optimized flow / capacity) | P5 | p5_baseline_solve.py | 2026-11-19 11:23:20 |
| p5_baseline_kpis | P5 — Baseline solve KPIs + independent validation | P5 | p5_baseline_solve.py | 2026-11-19 11:23:19 |
| p5_cost_breakdown | P5 — Baseline cost breakdown by category | P5 | p5_baseline_solve.py | 2026-11-19 11:23:19 |
| p5_service_by_group | P5 — Baseline component service level by group | P5 | p5_baseline_solve.py | 2026-11-19 11:23:19 |
| p5_service_by_group_fig | P5 — Baseline service level by group | P5 | p5_baseline_solve.py | 2026-11-19 11:23:19 |
| p5_shortage_by_period | P5 — Baseline shortage by period/group | P5 | p5_baseline_solve.py | 2026-11-19 11:23:19 |
| p6_battery_service_by_scenario | P6 — Battery service by scenario | P6 | p6_scenarios.py | 2026-11-19 11:25:04 |
| p6_cost_by_scenario | P6 — Total cost by scenario (stacked) | P6 | p6_scenarios.py | 2026-11-19 11:25:03 |
| p6_monte_carlo | P6 — Monte Carlo service under demand uncertainty (40 runs, seed 42) | P6 | p6_scenarios.py | 2026-11-19 11:25:12 |
| p6_monte_carlo_summary | P6 — Monte Carlo summary (demand uncertainty) | P6 | p6_scenarios.py | 2026-11-19 11:25:12 |
| p6_scenario_comparison | P6 — Scenario comparison vs baseline (cost, service, disruption premium) | P6 | p6_scenarios.py | 2026-11-19 11:25:02 |
| p6_service_by_group_scenarios | P6 — Component service level % by group × scenario | P6 | p6_scenarios.py | 2026-11-19 11:25:02 |
| p6_service_by_scenario | P6 — Overall service level by scenario | P6 | p6_scenarios.py | 2026-11-19 11:25:02 |
