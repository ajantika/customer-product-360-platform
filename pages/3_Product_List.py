"""All products with adoption %, MRR contribution, and top customers."""
import streamlit as st

from lib import data, metrics, theme


d = data.load_all()
customers, products, subs, usage = d["customers"], d["products"], d["subscriptions"], d["usage"]

st.title("📦 Product List")

adoption = metrics.product_adoption(subs, products, customers)

# MRR per product (proportional split by usage share within the customer)
last = metrics.latest_utilization_per_sub(usage)
last_mrr = last.merge(customers[["customer_id", "mrr_usd"]], on="customer_id")
total_use = last_mrr.groupby("customer_id")["usage"].transform("sum").replace(0, 1)
last_mrr["mrr_share"] = last_mrr["mrr_usd"] * (last_mrr["usage"] / total_use)
mrr_by_product = last_mrr.groupby("product_id", as_index=False)["mrr_share"].sum().rename(columns={"mrr_share": "mrr_attributed"})

table = adoption.merge(mrr_by_product, on="product_id", how="left").fillna(0)
display = table[["product_id", "name", "category", "unit", "customers", "adoption_pct", "mrr_attributed"]].copy()
display = display.rename(columns={
    "product_id": "ID", "name": "Product", "category": "Category", "unit": "Unit",
    "customers": "Customers", "adoption_pct": "Adoption %", "mrr_attributed": "MRR attributed",
})
display["Adoption %"] = display["Adoption %"].map(lambda x: f"{x:.1f}%")
display["MRR attributed"] = display["MRR attributed"].map(lambda x: f"${x:,.0f}")

event = st.dataframe(
    display,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    height=420,
)

if event and event.selection.rows:
    row_idx = event.selection.rows[0]
    selected = table.iloc[row_idx]
    st.session_state["selected_product_id"] = selected["product_id"]
    st.success(f"Selected **{selected['name']}** — open the **Product 360** page from the sidebar to drill in.")

st.markdown("---")
st.subheader("Top customers per product")

for _, p in adoption.iterrows():
    with st.expander(f"{p['name']}  —  {p['adoption_pct']:.0f}% adoption, {p['customers']} customers"):
        top = metrics.product_top_customers(p["product_id"], subs, usage, customers, top_n=5)
        if top.empty:
            st.write("No customers yet.")
        else:
            top_disp = top.copy()
            top_disp["mrr_usd"] = top_disp["mrr_usd"].map(lambda x: f"${x:,.0f}")
            top_disp["plan_limit"] = top_disp["plan_limit"].map(lambda x: f"{x:,.1f}")
            top_disp["usage"] = top_disp["usage"].map(lambda x: f"{x:,.1f}")
            top_disp["utilization_pct"] = top_disp["utilization_pct"].map(lambda x: f"{x:.0f}%")
            st.dataframe(top_disp, width="stretch", hide_index=True)
