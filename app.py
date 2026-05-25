import streamlit as st
import streamlit.components.v1 as components
from lib import theme

st.set_page_config(page_title="Customer & Product 360", page_icon="🌐", layout="wide")
theme.apply()

# Google Analytics 4 tracking
GA_ID = "G-F5KY3NFBCY"  # Customer 360
if "ga_loaded" not in st.session_state:
    st.session_state.ga_loaded = True
    components.html(f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}');
    </script>
    """, height=0)

st.sidebar.markdown(
    """
    <div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.3);
                border-radius:8px;padding:10px 12px;margin-bottom:8px;font-size:0.75rem;color:#fcd34d;">
    ⚠️ <strong>Demo environment</strong><br>
    Illustrative data only — not production data.
    </div>
    """,
    unsafe_allow_html=True,
)

pg = st.navigation([
    st.Page("views/overview.py",          title="Overview",       icon="🌐", default=True),
    st.Page("pages/2_Customer_360.py",    title="Customer 360",   icon="🪪"),
    st.Page("pages/4_Product_360.py",     title="Product 360",    icon="🧊"),
    st.Page("pages/1_Customer_List.py",   title="Customer List",  icon="👥"),
    st.Page("pages/3_Product_List.py",    title="Product List",   icon="📦"),
    st.Page("pages/5_Cohorts.py",         title="Cohorts",        icon="🎯"),
])
pg.run()
