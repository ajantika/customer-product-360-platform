import streamlit as st
from lib import theme

st.set_page_config(page_title="Customer & Product 360", page_icon="🌐", layout="wide")
theme.apply()

pg = st.navigation([
    st.Page("views/overview.py",          title="Overview",       icon="🌐", default=True),
    st.Page("pages/1_Customer_List.py",   title="Customer List",  icon="👥"),
    st.Page("pages/2_Customer_360.py",    title="Customer 360",   icon="🪪"),
    st.Page("pages/3_Product_List.py",    title="Product List",   icon="📦"),
    st.Page("pages/4_Product_360.py",     title="Product 360",    icon="🧊"),
    st.Page("pages/5_Cohorts.py",         title="Cohorts",        icon="🎯"),
])
pg.run()
