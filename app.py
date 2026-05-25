import pathlib
import streamlit as st
from lib import theme

st.set_page_config(page_title="Customer & Product 360", page_icon="🌐", layout="wide")
theme.apply()

# Google Analytics 4 — inject into Streamlit's index.html so Google's crawler can detect the tag
# (components.html puts it in a sandboxed iframe that Google's bot doesn't follow)
GA_ID = "G-F5KY3NFBCY"  # Customer 360

def _inject_ga4():
    ga_script = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}');
    </script>
    """
    try:
        index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
        html = index_path.read_text()
        if "googletagmanager.com" not in html:
            index_path.write_text(html.replace("</head>", ga_script + "</head>"))
    except Exception:
        pass

_inject_ga4()

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
