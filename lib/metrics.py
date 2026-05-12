"""Aggregations and cohort logic shared across pages."""
import pandas as pd


OVER_THRESHOLD = 100.0
UNDER_THRESHOLD = 50.0


def latest_month(usage: pd.DataFrame) -> pd.Timestamp:
    return usage["month"].max()


def latest_utilization_per_sub(usage: pd.DataFrame) -> pd.DataFrame:
    """One row per (customer_id, product_id) using the most recent month."""
    last = usage["month"].max()
    return usage[usage["month"] == last][["customer_id", "product_id", "usage", "utilization_pct"]].copy()


def customer_status_label(util_pct: float) -> str:
    if util_pct > OVER_THRESHOLD:
        return f"Over by {util_pct:.0f}%"
    if util_pct < UNDER_THRESHOLD:
        return f"Under usage {util_pct:.0f}%"
    return f"Healthy {util_pct:.0f}%"


def kpi_summary(customers: pd.DataFrame, usage: pd.DataFrame) -> dict:
    active = customers[customers["status"] == "active"]
    last_util = latest_utilization_per_sub(usage)
    cust_avg = last_util.groupby("customer_id")["utilization_pct"].mean().reset_index()
    over = (cust_avg["utilization_pct"] > OVER_THRESHOLD).sum()
    under = (cust_avg["utilization_pct"] < UNDER_THRESHOLD).sum()
    total = len(cust_avg) if len(cust_avg) else 1
    return {
        "total_mrr": float(active["mrr_usd"].sum()),
        "active_customers": int(len(active)),
        "pct_over": 100.0 * over / total,
        "pct_under": 100.0 * under / total,
    }


def mrr_by_region(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers[customers["status"] == "active"].groupby("region", as_index=False)["mrr_usd"].sum()
    return df.sort_values("mrr_usd", ascending=False)


def product_adoption(subs: pd.DataFrame, products: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    n_active = len(customers[customers["status"] == "active"])
    n_active = max(n_active, 1)
    counts = subs.groupby("product_id")["customer_id"].nunique().reset_index(name="customers")
    counts["adoption_pct"] = 100.0 * counts["customers"] / n_active
    return counts.merge(products, on="product_id").sort_values("adoption_pct", ascending=False)


def customer_product_summary(customer_id: str, subs: pd.DataFrame, usage: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Per-product latest utilization for a single customer."""
    sub = subs[subs["customer_id"] == customer_id]
    last = latest_utilization_per_sub(usage)
    last = last[last["customer_id"] == customer_id]
    df = sub.merge(last, on=["customer_id", "product_id"], how="left").merge(products, on="product_id")
    df["utilization_pct"] = df["utilization_pct"].fillna(0.0)
    df["status_label"] = df["utilization_pct"].apply(customer_status_label)
    return df[["product_id", "name", "category", "unit", "plan_limit", "usage", "utilization_pct", "status_label"]]


def customer_mom_usage(customer_id: str, usage: pd.DataFrame, product_id: str | None = None) -> pd.DataFrame:
    df = usage[usage["customer_id"] == customer_id]
    if product_id:
        df = df[df["product_id"] == product_id]
    g = df.groupby("month", as_index=False)["utilization_pct"].mean()
    return g.sort_values("month")


def product_top_customers(product_id: str, subs: pd.DataFrame, usage: pd.DataFrame, customers: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    last = latest_utilization_per_sub(usage)
    last = last[last["product_id"] == product_id]
    df = last.merge(customers, on="customer_id").merge(
        subs[subs["product_id"] == product_id][["customer_id", "plan_limit"]],
        on="customer_id",
    )
    df = df.sort_values("usage", ascending=False).head(top_n)
    return df[["customer_id", "name", "region", "plan_tier", "mrr_usd", "plan_limit", "usage", "utilization_pct"]]


def product_regional_adoption(product_id: str, subs: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    sub = subs[subs["product_id"] == product_id]
    df = sub.merge(customers[["customer_id", "region"]], on="customer_id")
    region_counts = df.groupby("region", as_index=False)["customer_id"].nunique().rename(columns={"customer_id": "customers"})
    total_by_region = customers[customers["status"] == "active"].groupby("region", as_index=False)["customer_id"].nunique().rename(columns={"customer_id": "total"})
    out = region_counts.merge(total_by_region, on="region", how="right").fillna(0)
    out["adoption_pct"] = 100.0 * out["customers"] / out["total"].replace(0, 1)
    return out.sort_values("adoption_pct", ascending=False)


def product_mom_usage(product_id: str, usage: pd.DataFrame) -> pd.DataFrame:
    df = usage[usage["product_id"] == product_id]
    g = df.groupby("month", as_index=False)["utilization_pct"].mean()
    return g.sort_values("month")


def cohort_upsell(customers: pd.DataFrame, usage: pd.DataFrame) -> pd.DataFrame:
    """Over-utilized customers with positive MoM growth — candidates for plan upgrade."""
    last = latest_utilization_per_sub(usage)
    cust_avg = last.groupby("customer_id", as_index=False)["utilization_pct"].mean()
    over = cust_avg[cust_avg["utilization_pct"] > OVER_THRESHOLD]["customer_id"].tolist()

    months = sorted(usage["month"].unique())
    if len(months) < 4:
        return pd.DataFrame()
    recent_3 = months[-3:]
    prior_3 = months[-6:-3]
    recent = usage[usage["month"].isin(recent_3)].groupby("customer_id")["utilization_pct"].mean()
    prior = usage[usage["month"].isin(prior_3)].groupby("customer_id")["utilization_pct"].mean()
    growth = (recent - prior).reset_index(name="growth")
    growing = growth[growth["growth"] > 0]["customer_id"].tolist()

    cohort_ids = set(over) & set(growing)
    df = customers[customers["customer_id"].isin(cohort_ids) & (customers["status"] == "active")].copy()
    df = df.merge(cust_avg, on="customer_id").merge(growth, on="customer_id")
    return df.sort_values("utilization_pct", ascending=False)


def cohort_churn_risk(customers: pd.DataFrame, usage: pd.DataFrame) -> pd.DataFrame:
    """Under-utilized customers with declining MoM — churn risk."""
    last = latest_utilization_per_sub(usage)
    cust_avg = last.groupby("customer_id", as_index=False)["utilization_pct"].mean()
    under = cust_avg[cust_avg["utilization_pct"] < UNDER_THRESHOLD]["customer_id"].tolist()

    months = sorted(usage["month"].unique())
    if len(months) < 4:
        return pd.DataFrame()
    recent_3 = months[-3:]
    prior_3 = months[-6:-3]
    recent = usage[usage["month"].isin(recent_3)].groupby("customer_id")["utilization_pct"].mean()
    prior = usage[usage["month"].isin(prior_3)].groupby("customer_id")["utilization_pct"].mean()
    growth = (recent - prior).reset_index(name="growth")
    declining = growth[growth["growth"] < 0]["customer_id"].tolist()

    cohort_ids = set(under) & set(declining)
    df = customers[customers["customer_id"].isin(cohort_ids) & (customers["status"] != "churned")].copy()
    df = df.merge(cust_avg, on="customer_id").merge(growth, on="customer_id")
    return df.sort_values("growth")


def cohort_mrr_at_risk(customers: pd.DataFrame, usage: pd.DataFrame) -> pd.DataFrame:
    """Over-utilized + status flagged at_risk — high-MRR accounts that may downgrade or leave."""
    last = latest_utilization_per_sub(usage)
    cust_avg = last.groupby("customer_id", as_index=False)["utilization_pct"].mean()
    over = cust_avg[cust_avg["utilization_pct"] > OVER_THRESHOLD]["customer_id"].tolist()
    df = customers[customers["customer_id"].isin(over) & (customers["status"] == "at_risk")].copy()
    df = df.merge(cust_avg, on="customer_id")
    return df.sort_values("mrr_usd", ascending=False)
