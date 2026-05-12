"""Generate synthetic SaaS usage data for the Customer & Product 360 demo.

Run: python scripts/generate_data.py
Outputs four parquet files into data/.
Seed is fixed (42) so results are reproducible.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

REGIONS = {
    "NAMER": ["United States", "Canada", "Mexico"],
    "EMEA": ["United Kingdom", "Germany", "France", "Spain", "Netherlands", "UAE"],
    "APAC": ["India", "Japan", "Singapore", "Australia"],
    "LATAM": ["Brazil", "Argentina", "Chile", "Colombia"],
}
REGION_WEIGHTS = {"NAMER": 0.60, "EMEA": 0.20, "APAC": 0.12, "LATAM": 0.08}

INDUSTRIES = ["FinTech", "Media", "Gaming", "E-commerce", "Healthcare", "EdTech", "Logistics", "AI/ML", "SaaS Tools"]
PLAN_TIERS = ["Starter", "Growth", "Enterprise"]
PLAN_TIER_WEIGHTS = [0.35, 0.45, 0.20]
STATUSES = ["active", "at_risk", "churned"]
STATUS_WEIGHTS = [0.78, 0.15, 0.07]

PRODUCTS = [
    {"product_id": "P01", "name": "API Gateway", "category": "Compute", "unit": "api_calls_M", "list_price_per_unit": 0.40},
    {"product_id": "P02", "name": "Object Storage", "category": "Storage", "unit": "GB", "list_price_per_unit": 0.023},
    {"product_id": "P03", "name": "CDN", "category": "Network", "unit": "GB_egress", "list_price_per_unit": 0.085},
    {"product_id": "P04", "name": "Compute", "category": "Compute", "unit": "vcpu_hours", "list_price_per_unit": 0.048},
    {"product_id": "P05", "name": "Analytics", "category": "Data", "unit": "events_M", "list_price_per_unit": 1.20},
    {"product_id": "P06", "name": "Identity", "category": "Security", "unit": "MAU_K", "list_price_per_unit": 5.00},
    {"product_id": "P07", "name": "Workflow", "category": "Platform", "unit": "runs_K", "list_price_per_unit": 0.15},
    {"product_id": "P08", "name": "Edge Functions", "category": "Compute", "unit": "invocations_M", "list_price_per_unit": 0.20},
]

# A small set of plausible-but-fake company names sprinkled in alongside Faker output
FEATURE_CUSTOMERS = [
    "OpenAI", "NorthWind Labs", "Acme Robotics", "Quantum Health", "Aurora Streaming",
    "Helix Bio", "PolarBank", "PixelForge Games", "GreenLeaf Logistics", "Lumen AI",
    "BlueRiver Media", "Vertex EdTech", "Stellar Pay", "Cobalt Cloud", "Ironclad Security",
]

N_CUSTOMERS = 200
N_MONTHS = 24
END_MONTH = date(2026, 5, 1)


def month_range(end: date, n: int) -> list[date]:
    months = []
    y, m = end.year, end.month
    for _ in range(n):
        months.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def generate_customers(rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    customers = []
    region_choices = rng.choice(
        list(REGION_WEIGHTS.keys()),
        size=N_CUSTOMERS,
        p=list(REGION_WEIGHTS.values()),
    )
    plan_choices = rng.choice(PLAN_TIERS, size=N_CUSTOMERS, p=PLAN_TIER_WEIGHTS)
    status_choices = rng.choice(STATUSES, size=N_CUSTOMERS, p=STATUS_WEIGHTS)

    feature_idxs = set(rng.choice(N_CUSTOMERS, size=len(FEATURE_CUSTOMERS), replace=False).tolist())
    feature_iter = iter(FEATURE_CUSTOMERS)

    for i in range(N_CUSTOMERS):
        region = region_choices[i]
        country = rng.choice(REGIONS[region])
        plan = plan_choices[i]
        if i in feature_idxs:
            name = next(feature_iter)
        else:
            name = fake.company()
        # MRR roughly correlated with plan tier
        if plan == "Starter":
            mrr = float(rng.normal(900, 350))
        elif plan == "Growth":
            mrr = float(rng.normal(4500, 1500))
        else:
            mrr = float(rng.normal(22000, 8000))
        mrr = max(150.0, round(mrr, 2))

        signup_offset_days = int(rng.integers(60, 1500))
        signup = END_MONTH - timedelta(days=signup_offset_days)

        customers.append({
            "customer_id": f"C{i+1:04d}",
            "name": name,
            "region": region,
            "country": country,
            "industry": rng.choice(INDUSTRIES),
            "plan_tier": plan,
            "mrr_usd": mrr,
            "signup_date": signup,
            "status": status_choices[i],
        })
    return pd.DataFrame(customers)


def generate_subscriptions(rng: np.random.Generator, customers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n_products = len(PRODUCTS)
    for _, c in customers.iterrows():
        # Enterprise customers subscribe to more products on average
        if c["plan_tier"] == "Enterprise":
            k = int(np.clip(rng.normal(5, 1.2), 2, n_products))
        elif c["plan_tier"] == "Growth":
            k = int(np.clip(rng.normal(3, 1.0), 1, n_products))
        else:
            k = int(np.clip(rng.normal(2, 0.8), 1, n_products))
        product_idxs = rng.choice(n_products, size=k, replace=False)
        for pi in product_idxs:
            p = PRODUCTS[pi]
            # plan_limit scales with tier and product
            tier_mult = {"Starter": 1.0, "Growth": 4.0, "Enterprise": 18.0}[c["plan_tier"]]
            base_limit = {
                "api_calls_M": 50, "GB": 500, "GB_egress": 200, "vcpu_hours": 800,
                "events_M": 20, "MAU_K": 10, "runs_K": 50, "invocations_M": 30,
            }[p["unit"]]
            plan_limit = round(base_limit * tier_mult * float(rng.uniform(0.7, 1.3)), 2)
            sub_start = max(c["signup_date"], END_MONTH - timedelta(days=int(rng.integers(60, 720))))
            rows.append({
                "customer_id": c["customer_id"],
                "product_id": p["product_id"],
                "plan_limit": plan_limit,
                "start_date": sub_start,
            })
    return pd.DataFrame(rows)


def generate_usage(rng: np.random.Generator, subs: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    months = month_range(END_MONTH, N_MONTHS)
    cust_status = customers.set_index("customer_id")["status"].to_dict()
    cust_signup = customers.set_index("customer_id")["signup_date"].to_dict()

    rows = []
    for _, s in subs.iterrows():
        cid = s["customer_id"]
        pid = s["product_id"]
        plan_limit = s["plan_limit"]
        sub_start = s["start_date"]
        status = cust_status[cid]
        signup = cust_signup[cid]

        # Per-subscription utilization profile
        roll = rng.random()
        if roll < 0.25:
            base_util = float(rng.uniform(1.05, 1.45))   # over-utilized
            trend = float(rng.uniform(0.005, 0.02))      # growing
        elif roll < 0.65:
            base_util = float(rng.uniform(0.10, 0.45))   # under-utilized
            trend = float(rng.uniform(-0.01, 0.005))     # flat or declining
        else:
            base_util = float(rng.uniform(0.55, 0.95))   # healthy
            trend = float(rng.uniform(-0.005, 0.01))

        # Churned customers go to zero in the most recent ~3 months
        churn_cutoff = N_MONTHS - 3 if status == "churned" else None
        # At_risk customers: trend bends downward in the last 6 months
        risk_kink = N_MONTHS - 6 if status == "at_risk" else None

        for idx, m in enumerate(months):
            if m < sub_start.replace(day=1):
                continue
            if m < signup.replace(day=1):
                continue

            util = base_util + trend * idx
            if risk_kink is not None and idx > risk_kink:
                util -= 0.04 * (idx - risk_kink)
            if churn_cutoff is not None and idx >= churn_cutoff:
                util = 0.0

            # Add noise
            util = util * float(rng.normal(1.0, 0.06))
            util = max(0.0, util)

            usage = round(plan_limit * util, 3)
            rows.append({
                "customer_id": cid,
                "product_id": pid,
                "month": m,
                "usage": usage,
                "utilization_pct": round(util * 100.0, 2),
            })

    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month"])
    return df


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    fake = Faker()
    Faker.seed(SEED)

    print("Generating customers...")
    customers = generate_customers(rng, fake)
    customers.to_parquet(DATA_DIR / "customers.parquet", index=False)

    print("Generating products...")
    products = pd.DataFrame(PRODUCTS)
    products.to_parquet(DATA_DIR / "products.parquet", index=False)

    print("Generating subscriptions...")
    subs = generate_subscriptions(rng, customers)
    subs.to_parquet(DATA_DIR / "subscriptions.parquet", index=False)

    print("Generating monthly usage...")
    usage = generate_usage(rng, subs, customers)
    usage.to_parquet(DATA_DIR / "usage_monthly.parquet", index=False)

    print(f"Done. Files written to {DATA_DIR}/")
    print(f"  customers:     {len(customers):,} rows")
    print(f"  products:      {len(products):,} rows")
    print(f"  subscriptions: {len(subs):,} rows")
    print(f"  usage_monthly: {len(usage):,} rows")


if __name__ == "__main__":
    main()
