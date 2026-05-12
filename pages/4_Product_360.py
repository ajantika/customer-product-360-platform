"""Product 360 drilldown — mirror of Customer 360 pivoted to a product."""
import streamlit as st

from lib import charts, data, llm, metrics, theme


d = data.load_all()
customers, products, subs, usage = d["customers"], d["products"], d["subscriptions"], d["usage"]

st.title("🧊 Product 360")

default_pid = st.session_state.get("selected_product_id", products["product_id"].iloc[0])
options = products.set_index("product_id")["name"].to_dict()
ids = list(options.keys())
default_idx = ids.index(default_pid) if default_pid in ids else 0
selected_pid = st.selectbox(
    "Product",
    ids,
    index=default_idx,
    format_func=lambda x: f"{options[x]}  ({x})",
)
st.session_state["selected_product_id"] = selected_pid

prod = products[products["product_id"] == selected_pid].iloc[0]

# Header KPIs
adoption = metrics.product_adoption(subs, products, customers)
this_row = adoption[adoption["product_id"] == selected_pid].iloc[0]
last = metrics.latest_utilization_per_sub(usage)
last_this = last[last["product_id"] == selected_pid]
avg_util = last_this["utilization_pct"].mean() if not last_this.empty else 0.0
total_usage = last_this["usage"].sum() if not last_this.empty else 0.0

h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1])
h1.markdown(f"### {prod['name']}")
h1.caption(f"{prod['category']} · {prod['unit']}")
h2.metric("Customers", f"{this_row['customers']:,}")
h3.metric("Adoption", f"{this_row['adoption_pct']:.0f}%")
h4.metric("Avg utilization", f"{avg_util:.0f}%")
h5.metric("Total usage (latest)", f"{total_usage:,.0f}")

st.markdown("---")

left, right = st.columns([1, 2])

with left:
    st.subheader("Regional adoption")
    reg = metrics.product_regional_adoption(selected_pid, subs, customers)
    st.plotly_chart(charts.regional_bar(reg, "adoption_pct", "% of active customers in region"), width="stretch")

with right:
    st.subheader("Aggregate MoM utilization")
    mom = metrics.product_mom_usage(selected_pid, usage)
    if mom.empty:
        st.info("No usage history.")
    else:
        st.plotly_chart(charts.bar_mom(mom, title="Avg utilization across all customers"), width="stretch")

st.markdown("---")

st.subheader("Top customers")
top = metrics.product_top_customers(selected_pid, subs, usage, customers, top_n=10)
if top.empty:
    st.info("No customers using this product yet.")
else:
    disp = top.copy()
    disp["mrr_usd"] = disp["mrr_usd"].map(lambda x: f"${x:,.0f}")
    disp["plan_limit"] = disp["plan_limit"].map(lambda x: f"{x:,.1f}")
    disp["usage"] = disp["usage"].map(lambda x: f"{x:,.1f}")
    disp["utilization_pct"] = disp["utilization_pct"].map(lambda x: f"{x:.0f}%")
    disp = disp.rename(columns={
        "customer_id": "ID", "name": "Customer", "region": "Region", "plan_tier": "Plan",
        "mrr_usd": "MRR", "plan_limit": "Limit", "usage": "Usage", "utilization_pct": "Util",
    })
    st.dataframe(disp, width="stretch", hide_index=True)

st.markdown("---")

st.subheader("💬 Ask AI about this product")
st.caption("Powered by Groq + Llama 3.1.")

context = {
    "product": prod["name"],
    "category": prod["category"],
    "unit": prod["unit"],
    "list_price_per_unit": float(prod["list_price_per_unit"]),
    "customers_count": int(this_row["customers"]),
    "adoption_pct": float(this_row["adoption_pct"]),
    "avg_utilization_pct": float(avg_util),
    "regional_adoption": [
        f"{r['region']}: {r['adoption_pct']:.0f}% ({int(r['customers'])} customers)"
        for _, r in reg.iterrows()
    ],
    "top_customers": [
        f"{r['name']} ({r['region']}): {r['utilization_pct']:.0f}% util, ${r['mrr_usd']:,.0f} MRR"
        for _, r in top.head(5).iterrows()
    ] if not top.empty else [],
    "mom_utilization_last_6_months": [
        f"{m.strftime('%b %Y')}: {v:.0f}%"
        for m, v in zip(mom["month"].tail(6), mom["utilization_pct"].tail(6))
    ] if not mom.empty else [],
}

example_qs = [
    "Which region should we invest in growing for this product?",
    "Are top customers heavily over-utilizing?",
    "Is adoption trending up or down?",
]
ec = st.columns(len(example_qs))
for i, qx in enumerate(example_qs):
    if ec[i].button(qx, key=f"prod_ex_{i}"):
        st.session_state["prod360_q"] = qx

q = st.text_input(
    "Ask a question",
    value=st.session_state.get("prod360_q", ""),
    placeholder="e.g. Where should we focus marketing spend for this product?",
    key="prod360_q_input",
)
if q:
    with st.spinner("Thinking..."):
        answer = llm.ask_about(context, q)
    st.markdown(f"**Answer:** {answer}")
