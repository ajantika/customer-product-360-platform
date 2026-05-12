"""Shared dark-theme CSS, applied at the top of every page."""
import streamlit as st

CSS = """
<style>
*, html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: #0f0c29 !important;
    background-image: radial-gradient(ellipse at 60% 0%, #2d1f6e 0%, #0f0c29 60%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: rgba(15, 12, 41, 0.7) !important; }
#MainMenu, footer { visibility: hidden; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}
h1, h2, h3, h4 { color: #f5f3ff !important; }
p, label, span, div { color: #d1d5db; }

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(129,140,248,0.18);
    border-radius: 12px;
    padding: 14px 16px;
}
[data-testid="stMetricValue"] { color: #f5f3ff !important; font-size: 1.6rem !important; }
[data-testid="stMetricLabel"] { color: #a78bfa !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.05em; }

div[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
}

.stButton > button {
    background: rgba(99,102,241,0.18) !important;
    border: 1px solid rgba(129,140,248,0.4) !important;
    color: #ddd6fe !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background: rgba(99,102,241,0.32) !important;
    color: white !important;
}

.badge-over { background: rgba(248,113,113,0.18); color: #fca5a5; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.badge-under { background: rgba(251,191,36,0.18); color: #fcd34d; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.badge-healthy { background: rgba(52,211,153,0.18); color: #6ee7b7; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.badge-active { background: rgba(52,211,153,0.18); color: #6ee7b7; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.badge-risk { background: rgba(251,191,36,0.18); color: #fcd34d; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.badge-churned { background: rgba(148,163,184,0.18); color: #cbd5e1; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {"active": "badge-active", "at_risk": "badge-risk", "churned": "badge-churned"}.get(status, "badge-active")
    return f'<span class="{cls}">{status.replace("_", " ")}</span>'


def util_badge(util_pct: float) -> str:
    if util_pct > 100:
        return f'<span class="badge-over">Over by {util_pct:.0f}%</span>'
    if util_pct < 50:
        return f'<span class="badge-under">Under usage {util_pct:.0f}%</span>'
    return f'<span class="badge-healthy">Healthy {util_pct:.0f}%</span>'
