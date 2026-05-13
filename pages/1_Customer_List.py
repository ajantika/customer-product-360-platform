"""Customer List — rich table with utilization, MRR impact, contract end, acquisition channel."""
import pandas as pd
import streamlit as st

from lib import data, metrics, theme

d = data.load_all()
customers = d["customers"].copy()
usage = d["usage"]

# Defensive: add new columns if old parquet is cached
if "marketing_campaign" not in customers.columns:
    customers["marketing_campaign"] = "Direct / Organic"
if "contract_end_date" not in customers.columns:
    import numpy as np
    customers["contract_end_date"] = pd.to_datetime("2027-12-31")

st.title("👥 Customer List")

f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
sel_region = f1.multiselect("Region",    sorted(customers["region"].unique()),    default=sorted(customers["region"].unique()))
sel_tier   = f2.multiselect("Plan tier", sorted(customers["plan_tier"].unique()), default=sorted(customers["plan_tier"].unique()))
sel_status = f3.multiselect("Status",    sorted(customers["status"].unique()),    default=sorted(customers["status"].unique()))
search     = f4.text_input("Search by name or campaign", "")

df = customers[
    customers["region"].isin(sel_region) &
    customers["plan_tier"].isin(sel_tier) &
    customers["status"].isin(sel_status)
]
if search:
    df = df[
        df["name"].str.contains(search, case=False, na=False) |
        df["marketing_campaign"].str.contains(search, case=False, na=False)
    ]

# Enrich with latest utilization
last_util = metrics.latest_utilization_per_sub(usage)
cust_avg  = last_util.groupby("customer_id")["utilization_pct"].mean().reset_index(name="avg_util")
df = df.merge(cust_avg, on="customer_id", how="left")
df["avg_util"] = df["avg_util"].fillna(0.0)

def util_label(v):
    if v > 100: return "⬆ Over-utilized"
    if v < 50:  return "⬇ Under-utilized"
    return "✓ Healthy"

df["usage_status"] = df["avg_util"].apply(util_label)
df["mrr_impact"]   = df.apply(
    lambda r: round(r["mrr_usd"] * (r["avg_util"] - 100) / 100, 0) if r["avg_util"] > 100
    else (round(-r["mrr_usd"] * (50 - r["avg_util"]) / 100, 0) if r["avg_util"] < 50 else 0.0), axis=1
)

# Summary tiles
t1, t2, t3, t4 = st.columns(4)
t1.metric("Customers shown", f"{len(df):,}")
t2.metric("Active",  f"{len(df[df['status']=='active']):,}")
t3.metric("At risk", f"{len(df[df['status']=='at_risk']):,}")
t4.metric("Churned", f"{len(df[df['status']=='churned']):,}")

st.markdown("---")
st.caption("Click a row → then open **Customer 360** in the sidebar to drill in")

display = df[[
    "customer_id", "name", "region", "country", "industry", "plan_tier",
    "mrr_usd", "avg_util", "usage_status", "mrr_impact",
    "marketing_campaign", "contract_end_date", "status",
]].copy()
display["contract_end_date"] = pd.to_datetime(display["contract_end_date"])
display = display.rename(columns={
    "customer_id": "ID", "name": "Customer", "region": "Region", "country": "Country",
    "industry": "Industry", "plan_tier": "Plan", "mrr_usd": "MRR ($)",
    "avg_util": "Utilization %", "usage_status": "Usage Status", "mrr_impact": "MRR Impact ($)",
    "marketing_campaign": "Acquisition Channel", "contract_end_date": "Contract End", "status": "Status",
})

event = st.dataframe(
    display,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    height=560,
    column_config={
        "MRR ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Utilization %": st.column_config.ProgressColumn(
            "Utilization %", min_value=0, max_value=150, format="%.0f%%"
        ),
        "MRR Impact ($)": st.column_config.NumberColumn(
            "MRR Impact ($)",
            help="Positive = upsell opportunity. Negative = MRR at churn risk.",
            format="$%.0f",
        ),
        "Contract End": st.column_config.DateColumn("Contract End", format="MMM YYYY"),
    },
)

if event and event.selection.rows:
    selected = df.iloc[event.selection.rows[0]]
    st.session_state["selected_customer_id"] = selected["customer_id"]
    st.success(f"Selected **{selected['name']}** — open **Customer 360** in the sidebar.")
