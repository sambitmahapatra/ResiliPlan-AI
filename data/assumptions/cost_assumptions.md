# Cost & Parameter Assumptions — ResiliPlan AI

> **The source workbook contains NO cost data.** Every parameter below is an **ASSUMPTION**, chosen for internally consistent relative magnitudes (not real prices). Optimisation decisions depend on the *ratios* between these costs. Each has a stated basis and a sensitivity range used in P6.

Monetary unit: **MU** (dimensionless currency).

| status | parameter | scope | value | unit | basis | sens. low | sens. high |
|---|---|---|---:|---|---|---:|---:|
| ASSUMED | `prod_cost.car` | per unit (group=car) | 1000.0 | MU/unit | Final assembly is the most cost-intensive step; anchor value. | 700.0 | 1300.0 |
| ASSUMED | `prod_cost.engine` | per unit (group=engine) | 300.0 | MU/unit | Major powertrain component; ~30% of assembly anchor. | 210.0 | 390.0 |
| ASSUMED | `prod_cost.gear` | per unit (group=gear) | 150.0 | MU/unit | Mechanical sub-assembly; ~15% of anchor. | 105.0 | 195.0 |
| ASSUMED | `prod_cost.battery` | per unit (group=battery) | 250.0 | MU/unit | Battery pack assembly from cells; ~25% of anchor. | 175.0 | 325.0 |
| ASSUMED | `prod_cost.seat` | per unit (group=seat) | 120.0 | MU/unit | Seat assembly from components; ~12% of anchor. | 84.0 | 156.0 |
| ASSUMED | `prod_cost.battery_componment` | per unit | 15.0 | MU/unit | Raw battery cell/module; low unit cost, high multiplicity (20/pack). | 10.0 | 20.0 |
| ASSUMED | `prod_cost.seat_componment` | per unit | 20.0 | MU/unit | Raw seat component (frame/foam/trim). | 14.0 | 26.0 |
| ASSUMED | `transport_cost.base` | per unit shipped on any arc | 2.0 | MU/unit | Fixed handling/loading cost per unit moved. | 1.0 | 4.0 |
| ASSUMED | `transport_cost.per_lead_period` | per unit per lead-time period of the arc | 1.0 | MU/unit/period | Transport cost scales with transit time/distance (lead time as proxy). | 0.5 | 2.0 |
| ASSUMED | `holding_cost.rate_per_period` | fraction of item production cost, per period | 0.02 | fraction/period | ~2%/period carrying cost (≈ 25-30%/yr typical automotive). | 0.01 | 0.04 |
| ASSUMED | `shortage_penalty.car` | per unfulfilled car per period late | 5000.0 | MU/car/period | Set ABOVE full fulfilment cost so the optimiser prefers to serve demand; proxy for lost-sale + contractual penalty. Dominant term enforcing service. | 3000.0 | 10000.0 |
| ASSUMED | `expedite_multiplier` | multiplier on transport cost for expedited flow | 3.0 | x | Premium (air/priority freight) relative to standard transport. | 2.0 | 5.0 |
| ASSUMED | `expedite_lead_reduction` | periods removed from an arc's lead time when expedited | 1.0 | periods | Expedited shipments arrive faster by ~1 period (bounded at >=0). | 1.0 | 2.0 |

## How these enter the MILP objective

minimise  Z = production + transport + holding + shortage(+expedite)
- production: Σ prod_cost[group(p)] · produced(p,node,t)
- transport: Σ (transport_base + transport_per_lead·lead(i,j)) · shipped(i,j,p,t)
- holding:   Σ holding_rate · prod_cost[group(p)] · end_inventory(p,node,t)
- shortage:  Σ shortage_penalty_car · backorder(car,t)
- expedite:  Σ (expedite_multiplier−1)·transport · expedited(i,j,p,t)   (scenarios only)

