"""Customer 360 drilldown — matches the sketch."""
import pandas as pd
import streamlit as st

from lib import charts, data, llm, metrics, theme

st.set_page_config(page_title="Customer 360", page_icon="🪪", layout="wide")
theme.apply()

d = data.load_all()
customers, products, subs, usage = d["customers"], d["products"], d["subscriptions"], d["usage"]

st.title("🪪 Customer 360")

# Customer picker (defaults to selection from Customer List, otherwise first customer)
default_id = st.session_state.get("selected_customer_id", customers["customer_id"].iloc[0])
options = customers.set_index("customer_id")["name"].to_dict()
ids = list(options.keys())
default_idx = ids.index(default_id) if default_id in ids else 0
selected_id = st.selectbox(
    "Customer",
    ids,
    index=default_idx,
    format_func=lambda x: f"{options[x]}  ({x})",
)
st.session_state["selected_customer_id"] = selected_id

cust = customers[customers["customer_id"] == selected_id].iloc[0]

# Header
h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1])
h1.markdown(f"### {cust['name']}")
h1.markdown(theme.status_badge(cust["status"]), unsafe_allow_html=True)
h2.metric("Region", cust["region"])
h3.metric("Plan", cust["plan_tier"])
h4.metric("MRR", f"${cust['mrr_usd']:,.0f}")
h5.metric("Industry", cust["industry"])

st.markdown("---")

# Products panel
prod_df = metrics.customer_product_summary(selected_id, subs, usage, products)
st.subheader("Products")
if prod_df.empty:
    st.info("No active subscriptions found.")
else:
    cols = st.columns(min(3, len(prod_df)))
    for i, (_, row) in enumerate(prod_df.iterrows()):
        with cols[i % len(cols)]:
            st.markdown(f"**{row['name']}**  \n_{row['category']}_")
            st.markdown(theme.util_badge(row["utilization_pct"]), unsafe_allow_html=True)
            st.caption(f"Usage {row['usage']:,.1f} / Limit {row['plan_limit']:,.1f} {row['unit']}")
            st.markdown("---")

# Two-up: regional distribution + MoM trend
left, right = st.columns([1, 2])

with left:
    st.subheader("Distribution by region")
    # For demo: this customer's usage as a share of the totals in each region
    cust_usage_last = usage[
        (usage["customer_id"] == selected_id)
        & (usage["month"] == metrics.latest_month(usage))
    ]
    region_share = pd.DataFrame({
        "region": [cust["region"]],
        "share_pct": [100.0],
    })
    # If we want a richer view, show the customer vs others in their region by usage
    same_region = customers[customers["region"] == cust["region"]]["customer_id"].tolist()
    region_total_usage = usage[
        usage["customer_id"].isin(same_region) & (usage["month"] == metrics.latest_month(usage))
    ]["usage"].sum()
    cust_total_usage = cust_usage_last["usage"].sum()
    pct = 100.0 * cust_total_usage / region_total_usage if region_total_usage else 0.0
    st.metric(f"Share of {cust['region']} usage (latest month)", f"{pct:.2f}%")

    # Show usage split across this customer's regions of operation (proxy: just home region for now)
    by_region = pd.DataFrame({
        "region": [cust["region"]],
        "share_pct": [100.0],
    })
    st.plotly_chart(
        charts.regional_bar(by_region, "share_pct", "Account region footprint"),
        width="stretch",
    )

with right:
    st.subheader("Month-over-month usage")
    prod_filter = st.selectbox(
        "Filter by product",
        ["All products"] + prod_df["name"].tolist() if not prod_df.empty else ["All products"],
        key="cust360_prod_filter",
    )
    pid = None
    if prod_filter != "All products" and not prod_df.empty:
        pid = prod_df[prod_df["name"] == prod_filter]["product_id"].iloc[0]
    mom = metrics.customer_mom_usage(selected_id, usage, product_id=pid)
    if mom.empty:
        st.info("No usage history available.")
    else:
        st.plotly_chart(charts.bar_mom(mom), width="stretch")

st.markdown("---")

# Ask AI panel
st.subheader("💬 Ask AI about this customer")
st.caption("Powered by Groq + Llama 3.1. Add your `GROQ_API_KEY` to `.streamlit/secrets.toml` to enable.")

context = {
    "customer": cust["name"],
    "region": cust["region"],
    "country": cust["country"],
    "industry": cust["industry"],
    "plan_tier": cust["plan_tier"],
    "mrr_usd": float(cust["mrr_usd"]),
    "status": cust["status"],
    "products": [
        f"{r['name']}: {r['utilization_pct']:.0f}% of plan ({r['usage']:.1f}/{r['plan_limit']:.1f} {r['unit']})"
        for _, r in prod_df.iterrows()
    ] if not prod_df.empty else [],
    "mom_avg_utilization_last_6_months": [
        f"{m.strftime('%b %Y')}: {v:.0f}%"
        for m, v in zip(metrics.customer_mom_usage(selected_id, usage)["month"].tail(6),
                         metrics.customer_mom_usage(selected_id, usage)["utilization_pct"].tail(6))
    ],
}

example_qs = [
    "Is this customer a candidate for upsell?",
    "What's their biggest risk product?",
    "How has their usage trended in the last 6 months?",
]
ec = st.columns(len(example_qs))
for i, q in enumerate(example_qs):
    if ec[i].button(q, key=f"ex_{i}"):
        st.session_state["cust360_q"] = q

q = st.text_input(
    "Ask a question",
    value=st.session_state.get("cust360_q", ""),
    placeholder="e.g. Should we offer this customer a plan upgrade?",
    key="cust360_q_input",
)
if q:
    with st.spinner("Thinking..."):
        answer = llm.ask_about(context, q)
    st.markdown(f"**Answer:** {answer}")
