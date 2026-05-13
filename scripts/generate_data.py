"""Generate synthetic SaaS usage data. Run: python scripts/generate_data.py"""
from __future__ import annotations

import calendar
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
    "EMEA":  ["United Kingdom", "Germany", "France", "Spain", "Netherlands", "UAE"],
    "APAC":  ["India", "Japan", "Singapore", "Australia"],
    "LATAM": ["Brazil", "Argentina", "Chile", "Colombia"],
}
REGION_WEIGHTS = {"NAMER": 0.60, "EMEA": 0.20, "APAC": 0.12, "LATAM": 0.08}

INDUSTRIES   = ["FinTech", "Media", "Gaming", "E-commerce", "Healthcare", "EdTech", "Logistics", "AI/ML", "SaaS Tools"]
PLAN_TIERS   = ["Starter", "Growth", "Enterprise"]
PLAN_WEIGHTS = [0.35, 0.45, 0.20]
STATUSES     = ["active", "at_risk", "churned"]
STATUS_W     = [0.78, 0.15, 0.07]

MARKETING_CAMPAIGNS = [
    "Google Ads — SaaS Search",
    "LinkedIn Ads",
    "Content / SEO",
    "Referral Program",
    "Partner Network",
    "Tech Conference",
    "Outbound SDR",
    "Direct / Organic",
]
CAMPAIGN_W = {
    "Starter":    [0.30, 0.10, 0.25, 0.10, 0.05, 0.05, 0.05, 0.10],
    "Growth":     [0.15, 0.20, 0.20, 0.15, 0.10, 0.10, 0.05, 0.05],
    "Enterprise": [0.05, 0.20, 0.10, 0.15, 0.20, 0.15, 0.10, 0.05],
}

PRICING_REGIONS = [
    {"region_id": "R01", "name": "North America",        "price_multiplier": 1.20},
    {"region_id": "R02", "name": "Europe",               "price_multiplier": 1.40},
    {"region_id": "R03", "name": "Asia Pacific",         "price_multiplier": 0.85},
    {"region_id": "R04", "name": "Oceania",              "price_multiplier": 1.80},
    {"region_id": "R05", "name": "Korea",                "price_multiplier": 1.30},
    {"region_id": "R06", "name": "Taiwan",               "price_multiplier": 1.10},
    {"region_id": "R07", "name": "Japan",                "price_multiplier": 1.00},
    {"region_id": "R08", "name": "India",                "price_multiplier": 0.70},
    {"region_id": "R09", "name": "Latin America",        "price_multiplier": 0.80},
    {"region_id": "R10", "name": "Middle East & Africa", "price_multiplier": 0.90},
]
BASE_TO_PRICING = {
    "NAMER": ["R01", "R09", "R02"],
    "EMEA":  ["R02", "R10", "R01"],
    "APAC":  ["R03", "R04", "R05", "R06", "R07", "R08"],
    "LATAM": ["R09", "R01", "R02"],
}

PRODUCTS = [
    {"product_id": "P01", "name": "API Gateway",    "category": "Compute",  "unit": "M Requests",    "list_price_per_unit": 0.40},
    {"product_id": "P02", "name": "Object Storage", "category": "Storage",  "unit": "TB",            "list_price_per_unit": 23.00},
    {"product_id": "P03", "name": "CDN",            "category": "Network",  "unit": "TB Egress",     "list_price_per_unit": 87.00},
    {"product_id": "P04", "name": "Compute",        "category": "Compute",  "unit": "Core-hrs",      "list_price_per_unit": 0.048},
    {"product_id": "P05", "name": "Analytics",      "category": "Data",     "unit": "M Events",      "list_price_per_unit": 1.20},
    {"product_id": "P06", "name": "Identity",       "category": "Security", "unit": "K Users",       "list_price_per_unit": 5.00},
    {"product_id": "P07", "name": "Workflow",       "category": "Platform", "unit": "K Runs",        "list_price_per_unit": 0.15},
    {"product_id": "P08", "name": "Edge Functions", "category": "Compute",  "unit": "M Invocations", "list_price_per_unit": 0.20},
]

# Global customers who have usage across all 10 pricing regions
ALL_REGION_CUSTOMERS = {"OpenAI", "Lumen AI", "Cobalt Cloud"}

FEATURE_CUSTOMERS = [
    "OpenAI", "NorthWind Labs", "Acme Robotics", "Quantum Health", "Aurora Streaming",
    "Helix Bio", "PolarBank", "PixelForge Games", "GreenLeaf Logistics", "Lumen AI",
    "BlueRiver Media", "Vertex EdTech", "Stellar Pay", "Cobalt Cloud", "Ironclad Security",
]

N_CUSTOMERS = 200
N_MONTHS    = 24
END_MONTH   = date(2026, 5, 1)


def quarter_end(d: date) -> date:
    month = ((d.month - 1) // 3 + 1) * 3
    year  = d.year + (1 if month > 12 else 0)
    month = month if month <= 12 else month - 12
    last  = calendar.monthrange(year, month)[1]
    return date(year, month, last)


def month_range(end: date, n: int) -> list[date]:
    months = []
    y, m = end.year, end.month
    for _ in range(n):
        months.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return list(reversed(months))


def generate_customers(rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    region_choices   = rng.choice(list(REGION_WEIGHTS.keys()), size=N_CUSTOMERS, p=list(REGION_WEIGHTS.values()))
    plan_choices     = rng.choice(PLAN_TIERS, size=N_CUSTOMERS, p=PLAN_WEIGHTS)
    status_choices   = rng.choice(STATUSES,   size=N_CUSTOMERS, p=STATUS_W)
    feature_idxs     = set(rng.choice(N_CUSTOMERS, size=len(FEATURE_CUSTOMERS), replace=False).tolist())
    feature_iter     = iter(FEATURE_CUSTOMERS)
    rows = []
    for i in range(N_CUSTOMERS):
        region = region_choices[i]
        plan   = plan_choices[i]
        name   = next(feature_iter) if i in feature_idxs else fake.company()
        mrr_params = {"Starter": (900, 350), "Growth": (4500, 1500), "Enterprise": (22000, 8000)}[plan]
        mrr        = max(150.0, round(float(rng.normal(*mrr_params)), 2))
        signup     = END_MONTH - timedelta(days=int(rng.integers(60, 1500)))
        campaign   = rng.choice(MARKETING_CAMPAIGNS, p=CAMPAIGN_W[plan])
        contract_months = int(rng.integers(12, 37))
        contract_end = quarter_end(date(signup.year + (signup.month + contract_months - 1) // 12,
                                        (signup.month + contract_months - 1) % 12 + 1, 1))
        rows.append({
            "customer_id":       f"C{i+1:04d}",
            "name":              name,
            "region":            region,
            "country":           rng.choice(REGIONS[region]),
            "industry":          rng.choice(INDUSTRIES),
            "plan_tier":         plan,
            "mrr_usd":           mrr,
            "signup_date":       signup,
            "contract_end_date": contract_end,
            "marketing_campaign": campaign,
            "status":            status_choices[i],
        })
    return pd.DataFrame(rows)


def generate_customer_region_usage(rng: np.random.Generator, customers: pd.DataFrame) -> pd.DataFrame:
    all_pr_ids = [p["region_id"] for p in PRICING_REGIONS]
    rows = []
    for _, c in customers.iterrows():
        # Global customers get all 10 regions
        if c["name"] in ALL_REGION_CUSTOMERS:
            chosen = all_pr_ids[:]
        else:
            primary = BASE_TO_PRICING[c["region"]]
            extra   = [r for r in all_pr_ids if r not in primary]
            # more regions for larger plans
            n_primary = {"Starter": 2, "Growth": 3, "Enterprise": 4}[c["plan_tier"]]
            n_extra   = {"Starter": 1, "Growth": 2, "Enterprise": 4}[c["plan_tier"]]
            chosen_primary = list(rng.choice(primary, size=min(n_primary, len(primary)), replace=False))
            chosen_extra   = list(rng.choice(extra,   size=min(n_extra,   len(extra)),   replace=False))
            chosen = chosen_primary + chosen_extra
        # primary region gets dominant share
        alpha = [3.0 if r in BASE_TO_PRICING.get(c["region"], []) else 1.0 for r in chosen]
        shares = rng.dirichlet(alpha)
        shares = shares / shares.sum()
        for rid, share in zip(chosen, shares):
            rows.append({"customer_id": c["customer_id"], "region_id": rid, "usage_share": round(float(share), 4)})
    return pd.DataFrame(rows)


def generate_subscriptions(rng: np.random.Generator, customers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, c in customers.iterrows():
        n_prod = {"Starter": int(np.clip(rng.normal(2, 0.8), 1, 8)),
                  "Growth":  int(np.clip(rng.normal(3, 1.0), 1, 8)),
                  "Enterprise": int(np.clip(rng.normal(5, 1.2), 2, 8))}[c["plan_tier"]]
        for pi in rng.choice(len(PRODUCTS), size=n_prod, replace=False):
            p = PRODUCTS[pi]
            tier_mult  = {"Starter": 1.0, "Growth": 4.0, "Enterprise": 18.0}[c["plan_tier"]]
            base_limit = {"M Requests": 50, "TB": 0.5, "TB Egress": 0.2, "Core-hrs": 800,
                          "M Events": 20, "K Users": 10, "K Runs": 50, "M Invocations": 30}[p["unit"]]
            plan_limit = round(base_limit * tier_mult * float(rng.uniform(0.7, 1.3)), 2)
            sub_start  = max(c["signup_date"], END_MONTH - timedelta(days=int(rng.integers(60, 720))))
            rows.append({"customer_id": c["customer_id"], "product_id": p["product_id"],
                         "plan_limit": plan_limit, "start_date": sub_start})
    return pd.DataFrame(rows)


def generate_usage(rng: np.random.Generator, subs: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    months      = month_range(END_MONTH, N_MONTHS)
    cust_status = customers.set_index("customer_id")["status"].to_dict()
    cust_signup = customers.set_index("customer_id")["signup_date"].to_dict()
    rows = []
    for _, s in subs.iterrows():
        cid, pid, plan_limit = s["customer_id"], s["product_id"], s["plan_limit"]
        status, signup, sub_start = cust_status[cid], cust_signup[cid], s["start_date"]
        roll = rng.random()
        if roll < 0.25:
            base_util, trend = float(rng.uniform(1.05, 1.45)), float(rng.uniform(0.005, 0.02))
        elif roll < 0.65:
            base_util, trend = float(rng.uniform(0.10, 0.45)), float(rng.uniform(-0.01, 0.005))
        else:
            base_util, trend = float(rng.uniform(0.55, 0.95)), float(rng.uniform(-0.005, 0.01))
        churn_cutoff = N_MONTHS - 3 if status == "churned" else None
        risk_kink    = N_MONTHS - 6 if status == "at_risk"  else None
        for idx, m in enumerate(months):
            if m < sub_start.replace(day=1) or m < signup.replace(day=1):
                continue
            util = base_util + trend * idx
            if risk_kink and idx > risk_kink:
                util -= 0.04 * (idx - risk_kink)
            if churn_cutoff and idx >= churn_cutoff:
                util = 0.0
            util  = max(0.0, util * float(rng.normal(1.0, 0.06)))
            rows.append({"customer_id": cid, "product_id": pid, "month": m,
                         "usage": round(plan_limit * util, 3), "utilization_pct": round(util * 100.0, 2)})
    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month"])
    return df


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng  = np.random.default_rng(SEED)
    fake = Faker(); Faker.seed(SEED)

    print("Generating customers...")
    customers = generate_customers(rng, fake)
    customers.to_parquet(DATA_DIR / "customers.parquet", index=False)

    print("Generating pricing regions...")
    pricing_regions = pd.DataFrame(PRICING_REGIONS)
    pricing_regions.to_parquet(DATA_DIR / "pricing_regions.parquet", index=False)

    print("Generating customer region usage...")
    cru = generate_customer_region_usage(rng, customers)
    cru.to_parquet(DATA_DIR / "customer_region_usage.parquet", index=False)

    print("Generating products...")
    products = pd.DataFrame(PRODUCTS)
    products.to_parquet(DATA_DIR / "products.parquet", index=False)

    print("Generating subscriptions...")
    subs = generate_subscriptions(rng, customers)
    subs.to_parquet(DATA_DIR / "subscriptions.parquet", index=False)

    print("Generating monthly usage...")
    usage = generate_usage(rng, subs, customers)
    usage.to_parquet(DATA_DIR / "usage_monthly.parquet", index=False)

    print(f"\nDone → {DATA_DIR}/")
    print(f"  customers:            {len(customers):,}")
    print(f"  pricing_regions:      {len(pricing_regions):,}")
    print(f"  customer_region_usage:{len(cru):,}")
    print(f"  products:             {len(products):,}")
    print(f"  subscriptions:        {len(subs):,}")
    print(f"  usage_monthly:        {len(usage):,}")

if __name__ == "__main__":
    main()
