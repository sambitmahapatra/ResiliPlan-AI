# Data Dictionary — ResiliPlan AI

_Generated 2026-11-19 by `src/audit/p1_data_dictionary.py` from the read-only workbook `data/raw/2020_dataset_OfAutomotiveProductionNetwork.xlsb`._

**Source dataset:** Moetz, Quetschlich & Otto (2020), *Optimisation Model for Multi-Item Multi-Echelon Supply Chains with Nested Multi-Level Products*, Mendeley Data, https://doi.org/10.17632/pr3sdy5vp3.1

## Dataset-level notes

- **Scale:** 12 nodes, 11 arcs, 28,049 products, 87,059 BOM rows, 14 periods (61–74).
- **Components:** only **49 distinct components** underlie the 28,000 car configurations (each car = 3–4 components, mean 3.1).
- **BOM shape:** a DAG of max depth 2 (car → component → sub-component) after excluding 49 benign identity rows (mother==child, qty 1, one per component).
- **Demand:** make-to-order — each car config is demanded exactly 1 unit, once; 2,000 configs/period × 14 = 28,000.
- **Costs:** the workbook contains **NO cost data**. All cost/price parameters in the optimization are ASSUMED and disclosed separately (see `data/assumptions/`).
- **Units:** not stated in the source; units below are documented assumptions based on column semantics (quantities = pieces/units, lead times = periods, capacity = flow units/period).
- **Integrity:** no missing values, no duplicate keys, and all cross-table references resolve (see P1 audit tables / figures).


## `products` — 28,049 rows × 3 cols

Master list of every product/SKU in the network and its family (group). Cars are finished vehicle configurations; the other groups are components.

**Primary key:** `product_p`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `product_p` | object | id | 28,049 | 0 | 64001 | Product / SKU identifier (car config id like 64001, or component code like DK8). |
| `group_g` | object | category | 7 | 0 | car | Product family: car, engine, gear, battery, seat, seat_componment, battery_componment. |
| `transportation_size_s` | int64 | size class | 1 | 0 | 0 | Transport size class of the product. Constant 0 across all rows in this dataset (no size differentiation used). |

## `nodes` — 12 rows × 1 cols

The 12 physical locations in the network: OEM assembly (zp7), the customer/demand node (zp8), and prod/inv/trans nodes for each supplier family.

**Primary key:** `node_n`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `node_n` | object | id | 12 | 0 | zp7 | Node identifier. |

## `nodes_inflow` — 44 rows × 2 cols

Which products are produced at / allowed to flow into each supplier production node (component master per supplier).

**Primary key:** `(node_n, product_p)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `node_n` | object | id | 4 | 0 | engine-supplier_prod | Node identifier. |
| `product_p` | object | id | 44 | 0 | DN4 | Product / SKU identifier (car config id like 64001, or component code like DK8). |

## `arcs` — 11 rows × 4 cols

The 11 directed transport links between nodes, each with a transit lead time and the product group it carries.

**Primary key:** `(starting_node_i, ending_node_j)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `starting_node_i` | object | id | 11 | 0 | zp7 | Origin node of the arc. |
| `ending_node_j` | object | id | 8 | 0 | zp8 | Destination node of the arc. |
| `process_lead_time_l_ij` | int64 | periods | 5 | 0 | 0 | Transit/process lead time on the arc, in planning periods (0-23; battery/seat 'trans' arcs exceed the 14-period horizon). |
| `group_g` | object | category | 7 | 0 | car | Product family: car, engine, gear, battery, seat, seat_componment, battery_componment. |

## `capacity_at_arc` — 154 rows × 4 cols

Transport capacity available on each arc in each period.

**Primary key:** `(starting_node_i, ending_node_j, period_t)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `starting_node_i` | object | id | 11 | 0 | gear-supplier_inv | Origin node of the arc. |
| `ending_node_j` | object | id | 8 | 0 | zp7 | Destination node of the arc. |
| `period_t` | int64 | period | 14 | 0 | 61 | Planning period index. Horizon is 61-74 (14 periods); initial-state tables use earlier periods (39-60). |
| `capacity_c_ijt` | int64 | flow units/period | 6 | 0 | 2100 | Transport capacity on arc (i,j) in period t. |

## `max_flow_product_per_arc` — 365 rows × 5 cols

Planned / upper-bound flow of a specific product on an arc in a period.

**Primary key:** `(starting_node_i, ending_node_j, product_p, period_t)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `starting_node_i` | object | id | 2 | 0 | engine-supplier_prod | Origin node of the arc. |
| `ending_node_j` | object | id | 2 | 0 | engine-supplier_inv | Destination node of the arc. |
| `product_p` | object | id | 37 | 0 | DN4 | Product / SKU identifier (car config id like 64001, or component code like DK8). |
| `period_t` | int64 | period | 10 | 0 | 61 | Planning period index. Horizon is 61-74 (14 periods); initial-state tables use earlier periods (39-60). |
| `planned_flow` | int64 | units/period | 180 | 0 | 278 | Planned / upper-bound flow (product- or group-specific) on the arc in the period. |

## `max_flow_group_per_arc` — 20 rows × 5 cols

Planned / upper-bound flow of a product group on an arc in a period.

**Primary key:** `(starting_node_i, ending_node_j, group_g, period_t)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `starting_node_i` | object | id | 2 | 0 | engine-supplier_prod | Origin node of the arc. |
| `ending_node_j` | object | id | 2 | 0 | engine-supplier_inv | Destination node of the arc. |
| `group_g` | object | category | 2 | 0 | engine | Product family: car, engine, gear, battery, seat, seat_componment, battery_componment. |
| `period_t` | int64 | period | 10 | 0 | 61 | Planning period index. Horizon is 61-74 (14 periods); initial-state tables use earlier periods (39-60). |
| `planned_flow` | int64 | units/period | 1 | 0 | 2000 | Planned / upper-bound flow (product- or group-specific) on the arc in the period. |

## `operations` — 15 rows × 7 cols

Manufacturing transformations at a node: input group -> output group with input/output quantities and yield parameters (alpha, beta).

**Primary key:** `(node_n, input_product_group_x, output_product_group_y)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `node_n` | object | id | 12 | 0 | zp7 | Node identifier. |
| `input_product_group_x` | object | category | 7 | 0 | engine | Input product group consumed by the operation. |
| `output_product_group_y` | object | category | 7 | 0 | car | Output product group produced by the operation. |
| `input_quantity_in_nxy` | int64 | units | 2 | 0 | 1 | Units of input group consumed per operation (e.g. 20 battery components -> 1 battery). |
| `output_quantity_out_nxy` | int64 | units | 1 | 0 | 1 | Units of output group produced per operation. |
| `alpha_nxy` | int64 | coef | 1 | 0 | 0 | Operation yield/efficiency parameter alpha (fixed component). |
| `beta_nxy` | int64 | coef | 2 | 0 | 1 | Operation yield/efficiency parameter beta (variable component; 1 = active transformation, 0 = sink/pass-through at zp8). |

## `BOM` — 87,059 rows × 3 cols

Bill of materials: for each parent product (mother) the child components required and the quantity per parent. Includes 49 benign identity rows (mother==child).

**Primary key:** `(mother, child)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `mother` | object | id | 28,049 | 0 | 64001 | Parent product in a BOM relationship. |
| `child` | object | id | 49 | 0 | DK8 | Child component required by the parent. |
| `individual_input_quantity_q_mc` | int64 | units/parent | 4 | 0 | 1 | Quantity of child required per one unit of parent (1-10). |

## `demands` — 28,000 rows × 4 cols

Customer demand: units of each finished car required at the demand node per period. Make-to-order (each config demanded 1 unit, once).

**Primary key:** `(node_n, product_p, period_t)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `node_n` | object | id | 1 | 0 | zp8 | Node identifier. |
| `product_p` | int64 | id | 28,000 | 0 | 64001 | Product / SKU identifier (car config id like 64001, or component code like DK8). |
| `demand_d_npt` | int64 | units | 1 | 0 | 1 | Demand for the product at the node in the period (all = 1 unit). |
| `period_t` | int64 | period | 14 | 0 | 61 | Planning period index. Horizon is 61-74 (14 periods); initial-state tables use earlier periods (39-60). |

## `initial_inventories` — 82 rows × 6 cols

Starting inventory at period 60 per node/product, with safety and maximum stock levels.

**Primary key:** `(node_n, product_p, period_t)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `node_n` | object | id | 5 | 0 | zp7 | Node identifier. |
| `product_p` | object | id | 45 | 0 | BEV | Product / SKU identifier (car config id like 64001, or component code like DK8). |
| `initial_inventory_I_np0` | int64 | units | 72 | 0 | 52 | Inventory on hand at the start (period 60). |
| `safety_stock` | int64 | units | 1 | 0 | 0 | Safety-stock level (mostly 0 in this dataset). |
| `max_inventory` | int64 | units | 1 | 0 | 99999 | Maximum inventory bound (mostly 99999 = effectively uncapped). |
| `period_t` | int64 | period | 1 | 0 | 60 | Planning period index. Horizon is 61-74 (14 periods); initial-state tables use earlier periods (39-60). |

## `initial_flows` — 117 rows × 5 cols

Material already in transit at the start (dispatched in earlier periods, arriving within the horizon) — needed because some lead times exceed 14.

**Primary key:** `(starting_node_i, ending_node_j, product_p, period_t)`

| column | type | unit (assumed) | distinct | missing | example | description |
|---|---|---|---:|---:|---|---|
| `starting_node_i` | object | id | 8 | 0 | battery-supplier_inv | Origin node of the arc. |
| `ending_node_j` | object | id | 6 | 0 | zp7 | Destination node of the arc. |
| `product_p` | object | id | 45 | 0 | BEV | Product / SKU identifier (car config id like 64001, or component code like DK8). |
| `period_t` | int64 | period | 5 | 0 | 60 | Planning period index. Horizon is 61-74 (14 periods); initial-state tables use earlier periods (39-60). |
| `initial_flow` | int64 | units | 99 | 0 | 200 | Units already in transit on the arc at the start. |
