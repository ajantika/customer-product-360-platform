"""Product List — adoption, MRR, top customers per product (no overlap)."""
import streamlit as st

from lib import data, metrics, theme

d = data.load_all()
customers, products, subs, usage = d["customers"], d["products"], d["subscriptions"], d["usage"]

st.title("📦 Product List")

adoption = metrics.product_adoption(subs, products, customers)

# MRR attribution
last    = metrics.latest_utilization_per_sub(usage)
last_mrr = last.merge(customers[["customer_id", "mrr_usd"]], on="customer_id")
total_use = last_mrr.groupby("customer_id")["usage"].transform("sum").replace(0, 1)
last_mrr["mrr_share"] = last_mrr["mrr_usd"] * (last_mrr["usage"] / total_use)
mrr_by_product = last_mrr.groupby("product_id", as_index=False)["mrr_share"].sum().rename(columns={"mrr_share": "mrr_attributed"})

table = adoption.merge(mrr_by_product, on="product_id", how="left").fillna(0)
display = table[["product_id", "name", "category", "unit", "customers", "adoption_pct", "mrr_attributed"]].rename(columns={
    "product_id": "ID", "name": "Product", "category": "Category", "unit": "Unit",
    "customers": "Customers", "adoption_pct": "Adoption %", "mrr_attributed": "MRR ($)",
})
display["Adoption %"] = display["Adoption %"].map(lambda x: f"{x:.1f}%")
display["MRR ($)"]    = display["MRR ($)"].map(lambda x: f"${x:,.0f}")

event = st.dataframe(display, width="stretch", hide_index=True,
                     on_select="rerun", selection_mode="single-row", height=360)

if event and event.selection.rows:
    selected = table.iloc[event.selection.rows[0]]
    st.session_state["selected_product_id"] = selected["product_id"]
    st.success(f"Selected **{selected['name']}** — open **Product 360** in the sidebar.")

st.markdown("---")
st.subheader("Top customers per product")

# Use tabs instead of expanders to avoid overlap bug
tab_labels = [f"{row['name']}" for _, row in adoption.iterrows()]
tabs = st.tabs(tab_labels)

for tab, (_, p) in zip(tabs, adoption.iterrows()):
    with tab:
        col1, col2 = st.columns([1, 3])
        col1.metric("Adoption", f"{p['adoption_pct']:.0f}%")
        col1.metric("Customers", f"{p['customers']:,}")
        with col2:
            top = metrics.product_top_customers(p["product_id"], subs, usage, customers, top_n=8)
            if top.empty:
                st.write("No customers yet.")
            else:
                top_disp = top.copy()
                top_disp["mrr_usd"]         = top_disp["mrr_usd"].map(lambda x: f"${x:,.0f}")
                top_disp["plan_limit"]       = top_disp["plan_limit"].map(lambda x: f"{x:,.1f}")
                top_disp["usage"]            = top_disp["usage"].map(lambda x: f"{x:,.1f}")
                top_disp["utilization_pct"]  = top_disp["utilization_pct"].map(lambda x: f"{x:.0f}%")
                st.dataframe(top_disp[["name", "region", "plan_tier", "mrr_usd", "utilization_pct"]].rename(
                    columns={"name": "Customer", "region": "Region", "plan_tier": "Plan",
                             "mrr_usd": "MRR", "utilization_pct": "Util %"}
                ), width="stretch", hide_index=True)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Export to Google Slides")
st.caption("Download a .pptx → upload to Google Drive → opens as Google Slides automatically.")
if st.button("⬇ Download Product List deck"):
    from lib.export_pptx import product_list_deck
    pptx_bytes = product_list_deck(table)
    st.download_button("📥 Save .pptx", data=pptx_bytes,
                       file_name="product_list.pptx",
                       mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
