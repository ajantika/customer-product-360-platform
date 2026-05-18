"""Segmentation: upsell candidates, churn risk, MRR-at-risk."""
import streamlit as st

from lib import data, metrics, theme


d = data.load_all()
customers, usage = d["customers"], d["usage"]

st.title("🎯 Customer Cohorts")
st.caption("Auto-generated segments for sales, customer-success, and finance teams.")

t1, t2, t3 = st.tabs(["⬆️ Upsell candidates", "⚠️ Churn risk", "💸 MRR-at-risk"])


def _format(df):
    if df.empty:
        return df
    out = df.copy()
    if "mrr_usd" in out.columns:
        out["mrr_usd"] = out["mrr_usd"].map(lambda x: f"${x:,.0f}")
    if "utilization_pct" in out.columns:
        out["utilization_pct"] = out["utilization_pct"].map(lambda x: f"{x:.0f}%")
    if "growth" in out.columns:
        out["growth"] = out["growth"].map(lambda x: f"{x:+.1f} pp")
    keep = ["customer_id", "name", "region", "industry", "plan_tier", "mrr_usd", "utilization_pct", "growth", "status"]
    cols = [c for c in keep if c in out.columns]
    return out[cols].rename(columns={
        "customer_id": "ID", "name": "Customer", "region": "Region", "industry": "Industry",
        "plan_tier": "Plan", "mrr_usd": "MRR", "utilization_pct": "Avg util",
        "growth": "MoM Δ (3m vs 3m)", "status": "Status",
    })


with t1:
    st.markdown(
        "**Definition:** Customers averaging **>100% utilization** in the latest month AND showing "
        "**positive utilization growth** in the last 3 months vs the prior 3."
    )
    df = metrics.cohort_upsell(customers, usage)
    st.metric("Customers in cohort", f"{len(df):,}")
    if not df.empty:
        st.metric("Total MRR exposure", f"${df['mrr_usd'].sum():,.0f}")
    st.dataframe(_format(df), width="stretch", hide_index=True, height=420)

with t2:
    st.markdown(
        "**Definition:** Customers averaging **<50% utilization** AND showing "
        "**declining MoM trend** (3m vs prior 3m). Excludes already-churned accounts."
    )
    df = metrics.cohort_churn_risk(customers, usage)
    st.metric("Customers in cohort", f"{len(df):,}")
    if not df.empty:
        st.metric("MRR at stake", f"${df['mrr_usd'].sum():,.0f}")
    st.dataframe(_format(df), width="stretch", hide_index=True, height=420)

with t3:
    st.markdown(
        "**Definition:** Over-utilized customers that are also flagged **at_risk** by account health — "
        "high-MRR accounts that may downgrade or churn if not handled."
    )
    df = metrics.cohort_mrr_at_risk(customers, usage)
    st.metric("Customers in cohort", f"{len(df):,}")
    if not df.empty:
        st.metric("MRR at stake", f"${df['mrr_usd'].sum():,.0f}")
    st.dataframe(_format(df), width="stretch", hide_index=True, height=420)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Export to Google Slides")
st.caption("Download a .pptx → upload to Google Drive → opens as Google Slides automatically.")
if st.button("⬇ Download Cohorts deck"):
    from lib.export_pptx import cohorts_deck
    upsell_df = metrics.cohort_upsell(customers, usage)
    churn_df  = metrics.cohort_churn_risk(customers, usage)
    risk_df   = metrics.cohort_mrr_at_risk(customers, usage)
    pptx_bytes = cohorts_deck(upsell_df, churn_df, risk_df)
    st.download_button("📥 Save .pptx", data=pptx_bytes,
                       file_name="customer_cohorts.pptx",
                       mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
