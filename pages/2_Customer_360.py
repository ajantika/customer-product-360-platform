"""Customer 360 — product tabs, campaign source, 10-region pricing breakdown."""
import pandas as pd
import streamlit as st

from lib import charts, data, llm, metrics, theme

d = data.load_all()
customers, products, subs, usage = d["customers"], d["products"], d["subscriptions"], d["usage"]
pricing_regions = d["pricing_regions"]
cru             = d["customer_region_usage"]

st.title("🪪 Customer 360")

default_id  = st.session_state.get("selected_customer_id", customers["customer_id"].iloc[0])
options     = customers.set_index("customer_id")["name"].to_dict()
ids         = list(options.keys())
default_idx = ids.index(default_id) if default_id in ids else 0
selected_id = st.selectbox("Customer", ids, index=default_idx, format_func=lambda x: f"{options[x]}  ({x})")
st.session_state["selected_customer_id"] = selected_id

cust = customers[customers["customer_id"] == selected_id].iloc[0]

st.markdown(f"""
<div class="cust-card" style="display:flex; gap:20px; align-items:flex-start;">
  {theme.avatar(cust['name'])}
  <div style="flex:1;">
    <div style="font-size:1.5rem;font-weight:700;color:#f5f3ff;margin-bottom:6px;">{cust['name']}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
      {theme.status_badge(cust['status'])}
      {theme.campaign_badge(cust['marketing_campaign'])}
    </div>
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:8px;">
      <div><div style="color:#a78bfa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">Region</div>
           <div style="color:#f5f3ff;font-weight:600;">{cust['region']}</div></div>
      <div><div style="color:#a78bfa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">Country</div>
           <div style="color:#f5f3ff;font-weight:600;">{cust['country']}</div></div>
      <div><div style="color:#a78bfa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">Plan</div>
           <div style="color:#f5f3ff;font-weight:600;">{cust['plan_tier']}</div></div>
      <div><div style="color:#a78bfa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">MRR</div>
           <div style="color:#f5f3ff;font-weight:600;">${cust['mrr_usd']:,.0f}</div></div>
      <div><div style="color:#a78bfa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">Contract End</div>
           <div style="color:#f5f3ff;font-weight:600;">{pd.Timestamp(cust['contract_end_date']).strftime('%b %Y')}</div></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Products as tabs
st.subheader("Products")
prod_df = metrics.customer_product_summary(selected_id, subs, usage, products)

if prod_df.empty:
    st.info("No active subscriptions.")
else:
    tabs = st.tabs([row["name"] for _, row in prod_df.iterrows()])
    for tab, (_, row) in zip(tabs, prod_df.iterrows()):
        with tab:
            c1, c2, c3 = st.columns(3)
            c1.metric("Category", row["category"])
            c2.metric("Usage", f"{row['usage']:,.1f} {row['unit']}")
            c3.metric("Plan Limit", f"{row['plan_limit']:,.1f} {row['unit']}")
            st.markdown(theme.util_badge(row["utilization_pct"]), unsafe_allow_html=True)
            mom_p = metrics.customer_mom_usage(selected_id, usage, product_id=row["product_id"])
            if not mom_p.empty:
                st.plotly_chart(charts.bar_mom(mom_p, title=f"{row['name']} — MoM utilization"), width="stretch")

st.markdown("---")

left, right = st.columns([3, 2])

with left:
    st.subheader("Month-over-month usage (all products)")
    mom_all = metrics.customer_mom_usage(selected_id, usage)
    if not mom_all.empty:
        st.plotly_chart(charts.bar_mom(mom_all), width="stretch")

with right:
    st.subheader("Usage by pricing region")
    st.caption("Usage share × price multiplier shows where cost is concentrated.")
    cru_cust = cru[cru["customer_id"] == selected_id].merge(pricing_regions, on="region_id")
    if not cru_cust.empty:
        cru_cust["weighted_mrr"] = cru_cust["usage_share"] * cru_cust["price_multiplier"] * float(cust["mrr_usd"])
        cru_cust = cru_cust.sort_values("weighted_mrr", ascending=False)
        tbl = cru_cust[["name", "usage_share", "price_multiplier", "weighted_mrr"]].copy()
        tbl["Usage %"]      = (tbl["usage_share"] * 100).map(lambda x: f"{x:.0f}%")
        tbl["Price mult."]  = tbl["price_multiplier"].map(lambda x: f"{x:.2f}×")
        tbl["Weighted MRR"] = tbl["weighted_mrr"].map(lambda x: f"${x:,.0f}")
        tbl["Alert"] = cru_cust.apply(
            lambda r: "🔴 High cost" if r["price_multiplier"] >= 1.3 and r["usage_share"] >= 0.20 else "", axis=1
        ).values
        st.dataframe(
            tbl[["name", "Usage %", "Price mult.", "Weighted MRR", "Alert"]].rename(columns={"name": "Region"}),
            width="stretch", hide_index=True, height=300,
        )

st.markdown("---")

st.subheader("💬 Ask AI about this customer")
st.caption("Powered by Groq + Llama 3.1")

context = {
    "customer": cust["name"], "region": cust["region"], "industry": cust["industry"],
    "plan_tier": cust["plan_tier"], "mrr_usd": float(cust["mrr_usd"]), "status": cust["status"],
    "acquired_via": cust["marketing_campaign"], "contract_end": str(cust["contract_end_date"]),
    "products": [
        f"{r['name']}: {r['utilization_pct']:.0f}% of plan ({r['usage']:.1f}/{r['plan_limit']:.1f} {r['unit']})"
        for _, r in prod_df.iterrows()
    ] if not prod_df.empty else [],
}

example_qs = ["Is this customer an upsell candidate?", "What is their churn risk?", "Which product is over-utilized?"]
ec = st.columns(3)
for i, q in enumerate(example_qs):
    if ec[i].button(q, key=f"ex_{i}"):
        st.session_state["cust360_q"] = q

q = st.text_input("Ask a question", value=st.session_state.get("cust360_q", ""),
                  placeholder="e.g. Should we offer a plan upgrade?", key="cust360_q_input")
if q:
    with st.spinner("Thinking..."):
        st.markdown(f"**Answer:** {llm.ask_about(context, q)}")

# ── Export to Slides ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Export to Google Slides")
st.caption("Downloads a .pptx file you can upload to Google Drive — it auto-converts to Google Slides.")

if st.button("⬇ Download Customer Deck (.pptx)", type="primary"):
    from lib.export_pptx import customer_deck
    # Build region table
    cru_cust = cru[cru["customer_id"] == selected_id].merge(pricing_regions, on="region_id")
    region_tbl = None
    if not cru_cust.empty:
        cru_cust["weighted_mrr"] = cru_cust["usage_share"] * cru_cust["price_multiplier"] * float(cust["mrr_usd"])
        cru_cust = cru_cust.sort_values("weighted_mrr", ascending=False)
        tbl = cru_cust[["name", "usage_share", "price_multiplier", "weighted_mrr"]].copy()
        tbl["Usage %"]      = (tbl["usage_share"] * 100).map(lambda x: f"{x:.0f}%")
        tbl["Price mult."]  = tbl["price_multiplier"].map(lambda x: f"{x:.2f}×")
        tbl["Weighted MRR"] = tbl["weighted_mrr"].map(lambda x: f"${x:,.0f}")
        tbl["Alert"]        = cru_cust.apply(
            lambda r: "🔴 High cost" if r["price_multiplier"] >= 1.3 and r["usage_share"] >= 0.20 else "", axis=1
        ).values
        region_tbl = tbl[["name", "Usage %", "Price mult.", "Weighted MRR", "Alert"]].rename(columns={"name": "Region"})

    mom_all = metrics.customer_mom_usage(selected_id, usage)
    with st.spinner("Building deck..."):
        pptx_bytes = customer_deck(cust, prod_df, mom_all, region_tbl if region_tbl is not None else pd.DataFrame())

    st.download_button(
        label="📥 Click here to save the file",
        data=pptx_bytes,
        file_name=f"{cust['name'].replace(' ', '_')}_Customer_360.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
