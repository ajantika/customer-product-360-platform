"""Customer 360 — product tabs, campaign source, pricing region breakdown, PPTX export."""
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

# ── Header card ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="cust-card" style="display:flex; gap:20px; align-items:flex-start;">
  {theme.avatar(cust['name'])}
  <div style="flex:1;">
    <div style="font-size:1.5rem;font-weight:700;color:#f5f3ff;margin-bottom:6px;">{cust['name']}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
      {theme.status_badge(cust['status'])}
      {theme.campaign_badge(cust.get('marketing_campaign', 'Direct / Organic'))}
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
           <div style="color:#f5f3ff;font-weight:600;">{pd.Timestamp(cust.get('contract_end_date', '2027-12-31')).strftime('%b %Y')}</div></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Products — tabs (metrics + badge only, no duplicate chart) ────────────────
st.subheader("Products")
prod_df = metrics.customer_product_summary(selected_id, subs, usage, products)

if prod_df.empty:
    st.info("No active subscriptions.")
else:
    tabs = st.tabs([row["name"] for _, row in prod_df.iterrows()])
    for tab, (_, row) in zip(tabs, prod_df.iterrows()):
        with tab:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Category",   row["category"])
            c2.metric("Usage",      f"{row['usage']:,.0f} {row['unit']}")
            c3.metric("Plan Limit", f"{row['plan_limit']:,.0f} {row['unit']}")
            c4.metric("Utilization", f"{row['utilization_pct']:.0f}%")
            st.markdown(theme.util_badge(row["utilization_pct"]), unsafe_allow_html=True)

st.markdown("---")

# ── Single MoM chart with product filter ─────────────────────────────────────
left, right = st.columns([3, 2])

with left:
    st.subheader("Month-over-month usage")
    prod_options = ["All products"] + prod_df["name"].tolist() if not prod_df.empty else ["All products"]
    prod_filter  = st.selectbox("Filter by product", prod_options, key="cust360_prod_filter")
    pid = None
    if prod_filter != "All products" and not prod_df.empty:
        pid = prod_df[prod_df["name"] == prod_filter]["product_id"].iloc[0]
    mom = metrics.customer_mom_usage(selected_id, usage, product_id=pid)
    if not mom.empty:
        st.plotly_chart(charts.bar_mom(mom), width="stretch")
    else:
        st.info("No usage history.")

with right:
    st.subheader("Usage by pricing region")
    cru_cust = cru[cru["customer_id"] == selected_id].merge(pricing_regions, on="region_id")
    if not cru_cust.empty:
        tbl = cru_cust[["name", "usage_share"]].copy()
        tbl["Usage %"] = (tbl["usage_share"] * 100).map(lambda x: f"{x:.0f}%")
        tbl = tbl.sort_values("usage_share", ascending=False).rename(columns={"name": "Region"})
        st.dataframe(
            tbl[["Region", "Usage %"]],
            width="stretch", hide_index=True, height=340,
        )
    else:
        st.info("No regional data.")

st.markdown("---")

# ── Ask AI ────────────────────────────────────────────────────────────────────
st.subheader("💬 Ask AI about this customer")
st.caption("Powered by Groq + Llama 3.1")

context = {
    "customer": cust["name"], "region": cust["region"], "industry": cust["industry"],
    "plan_tier": cust["plan_tier"], "mrr_usd": float(cust["mrr_usd"]), "status": cust["status"],
    "acquired_via": cust.get("marketing_campaign", "—"),
    "contract_end": str(cust.get("contract_end_date", "—")),
    "products": [
        f"{r['name']}: {r['utilization_pct']:.0f}% of plan ({r['usage']:,.0f}/{r['plan_limit']:,.0f} {r['unit']})"
        for _, r in prod_df.iterrows()
    ] if not prod_df.empty else [],
}

example_qs = ["Is this customer an upsell candidate?", "What is their churn risk?", "Which product is over-utilized?"]
ec = st.columns(3)
for i, qx in enumerate(example_qs):
    if ec[i].button(qx, key=f"ex_{i}"):
        st.session_state["cust360_q_input"] = qx

q = st.text_input("Ask a question", placeholder="e.g. Should we offer a plan upgrade?", key="cust360_q_input")
if q:
    with st.spinner("Thinking..."):
        st.markdown(f"**Answer:** {llm.ask_about(context, q)}")

st.markdown("---")

# ── Export to Google Slides ───────────────────────────────────────────────────
st.subheader("📊 Export to Google Slides")
st.caption("Download a .pptx → upload to Google Drive → opens as Google Slides automatically.")

if st.button("⬇ Download Customer Deck (.pptx)", type="primary"):
    from lib.export_pptx import customer_deck
    cru_cust2 = cru[cru["customer_id"] == selected_id].merge(pricing_regions, on="region_id")
    region_tbl = pd.DataFrame()
    if not cru_cust2.empty:
        t = cru_cust2[["name", "usage_share"]].copy()
        t["Usage %"] = (t["usage_share"] * 100).map(lambda x: f"{x:.0f}%")
        t = t.sort_values("usage_share", ascending=False)
        region_tbl = t[["name", "Usage %"]].rename(columns={"name": "Region"})
    mom_all = metrics.customer_mom_usage(selected_id, usage)
    with st.spinner("Building deck..."):
        pptx_bytes = customer_deck(cust, prod_df, mom_all, region_tbl)
    st.download_button(
        label="📥 Click here to save",
        data=pptx_bytes,
        file_name=f"{cust['name'].replace(' ', '_')}_Customer_360.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
