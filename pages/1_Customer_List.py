"""Customer List — filterable table with utilization, MRR impact, acquisition channel."""
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

# ── Custom CSS for cleaner filter chips ───────────────────────────────────────
st.markdown("""
<style>
/* Filter container card */
.filter-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem 1.25rem 0.75rem;
    margin-bottom: 1.25rem;
}
.filter-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 0.4rem;
}
/* Override multiselect tag colors to indigo instead of red */
[data-baseweb="tag"] {
    background-color: rgba(99,102,241,0.25) !important;
    border: 1px solid rgba(99,102,241,0.4) !important;
    color: #a5b4fc !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] span { color: #a5b4fc !important; }
[data-baseweb="tag"] button svg { fill: #a5b4fc !important; }
/* Multiselect input box */
[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown('<div class="filter-label">Region</div>', unsafe_allow_html=True)
        sel_region = st.multiselect(
            "Region", sorted(customers["region"].unique()),
            default=sorted(customers["region"].unique()),
            label_visibility="collapsed"
        )
    with f2:
        st.markdown('<div class="filter-label">Plan Tier</div>', unsafe_allow_html=True)
        sel_tier = st.multiselect(
            "Plan tier", sorted(customers["plan_tier"].unique()),
            default=sorted(customers["plan_tier"].unique()),
            label_visibility="collapsed"
        )
    with f3:
        st.markdown('<div class="filter-label">Status</div>', unsafe_allow_html=True)
        sel_status = st.multiselect(
            "Status", sorted(customers["status"].unique()),
            default=sorted(customers["status"].unique()),
            label_visibility="collapsed"
        )
    st.markdown('</div>', unsafe_allow_html=True)

# ── Filter data ───────────────────────────────────────────────────────────────
df = customers[
    customers["region"].isin(sel_region) &
    customers["plan_tier"].isin(sel_tier) &
    customers["status"].isin(sel_status)
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

# ── Summary tiles ─────────────────────────────────────────────────────────────
t1, t2, t3, t4 = st.columns(4)
t1.metric("Customers shown", f"{len(df):,}")
t2.metric("Active",  f"{len(df[df['status']=='active']):,}")
t3.metric("At risk", f"{len(df[df['status']=='at_risk']):,}")
t4.metric("Churned", f"{len(df[df['status']=='churned']):,}")

st.markdown("---")
st.caption("Click a row → then open **Customer 360** in the sidebar to drill in")

# ── Table ─────────────────────────────────────────────────────────────────────
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
