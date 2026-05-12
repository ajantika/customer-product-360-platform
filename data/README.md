# Data Schema

All four files are written by `scripts/generate_data.py` (seed = 42).

## customers.parquet

| column | type | notes |
|---|---|---|
| customer_id | str | `C0001` … `C0200` |
| name | str | mix of Faker-generated and plausible-but-fake brand names |
| region | str | NAMER · EMEA · APAC · LATAM |
| country | str | one of the countries within `region` |
| industry | str | FinTech, Media, Gaming, etc. |
| plan_tier | str | Starter · Growth · Enterprise |
| mrr_usd | float | monthly recurring revenue, correlated with `plan_tier` |
| signup_date | date | between 60 and ~1500 days before the latest month |
| status | str | active · at_risk · churned (78 / 15 / 7 mix) |

## products.parquet

| column | type | notes |
|---|---|---|
| product_id | str | `P01` … `P08` |
| name | str | API Gateway, Object Storage, CDN, Compute, Analytics, Identity, Workflow, Edge Functions |
| category | str | Compute · Storage · Network · Data · Security · Platform |
| unit | str | api_calls_M · GB · GB_egress · vcpu_hours · events_M · MAU_K · runs_K · invocations_M |
| list_price_per_unit | float | reference price |

## subscriptions.parquet

| column | type | notes |
|---|---|---|
| customer_id | str | FK → customers |
| product_id | str | FK → products |
| plan_limit | float | tier-scaled plan allotment in the product's `unit` |
| start_date | date | when this subscription began |

Average ~3 products per customer; Enterprise customers subscribe to more.

## usage_monthly.parquet

| column | type | notes |
|---|---|---|
| customer_id | str | FK → customers |
| product_id | str | FK → products |
| month | datetime | first of the month, 24 months ending May 2026 |
| usage | float | actual consumption in the product's `unit` |
| utilization_pct | float | 100 × usage / plan_limit |

Distribution by design:
- ~25% over-utilized (>100%)
- ~40% under-utilized (<50%)
- ~35% healthy (50–100%)
- `at_risk` customers bend downward in the last 6 months
- `churned` customers drop to zero in the last 3 months

## Regenerate

```bash
python scripts/generate_data.py
```
