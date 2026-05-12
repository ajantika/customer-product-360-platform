"""Searchable, filterable customer table. Click a row to drill into Customer 360."""
import streamlit as st

from lib import data, theme

st.set_page_config(page_title="Customer List", page_icon="👥", layout="wide")
theme.apply()

d = data.load_all()
customers = d["customers"].copy()

st.title("👥 Customer List")
st.caption(f"{len(customers):,} customers in the platform")

f1, f2, f3, f4 = st.columns(4)
regions = sorted(customers["region"].unique())
tiers = sorted(customers["plan_tier"].unique())
statuses = sorted(customers["status"].unique())

sel_region = f1.multiselect("Region", regions, default=regions)
sel_tier = f2.multiselect("Plan tier", tiers, default=tiers)
sel_status = f3.multiselect("Status", statuses, default=statuses)
search = f4.text_input("Search by name", "")

df = customers[
    customers["region"].isin(sel_region)
    & customers["plan_tier"].isin(sel_tier)
    & customers["status"].isin(sel_status)
]
if search:
    df = df[df["name"].str.contains(search, case=False, na=False)]

st.markdown(f"**{len(df):,} customers match**")

display = df[["customer_id", "name", "region", "country", "industry", "plan_tier", "mrr_usd", "status"]].copy()
display["mrr_usd"] = display["mrr_usd"].map(lambda x: f"${x:,.0f}")
display = display.rename(columns={
    "customer_id": "ID", "name": "Customer", "region": "Region", "country": "Country",
    "industry": "Industry", "plan_tier": "Plan", "mrr_usd": "MRR", "status": "Status",
})

event = st.dataframe(
    display,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    height=520,
)

if event and event.selection.rows:
    row_idx = event.selection.rows[0]
    selected = df.iloc[row_idx]
    st.session_state["selected_customer_id"] = selected["customer_id"]
    st.success(f"Selected **{selected['name']}** — open the **Customer 360** page from the sidebar to drill in.")
