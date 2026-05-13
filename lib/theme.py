"""Shared dark-theme CSS."""
import streamlit as st

CSS = """
<style>
*, html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: #0d0b1e !important;
    background-image: radial-gradient(ellipse at 60% 0%, #1e1245 0%, #0d0b1e 60%) !important;
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] {
    background: rgba(13,11,30,0.85) !important;
    border-right: 1px solid rgba(129,140,248,0.12) !important;
}
[data-testid="stSidebarNav"] a { color: #a5b4fc !important; }
[data-testid="stSidebarNav"] a:hover { color: #fff !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem !important; max-width: 1300px !important; }
h1 { color: #f5f3ff !important; font-size: 1.9rem !important; font-weight: 700 !important; }
h2 { color: #e9d5ff !important; font-size: 1.3rem !important; font-weight: 600 !important; }
h3 { color: #ddd6fe !important; font-size: 1.1rem !important; }
p, label, span { color: #c4b5fd; }

/* KPI tiles */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.06));
    border: 1px solid rgba(129,140,248,0.22);
    border-radius: 14px; padding: 18px 20px;
}
[data-testid="stMetricValue"] { color: #f5f3ff !important; font-size: 1.7rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #a78bfa !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* Dataframe */
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid rgba(129,140,248,0.15); }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid rgba(129,140,248,0.2) !important; gap: 4px; }
[data-testid="stTabs"] [role="tab"] {
    color: #a78bfa !important; border-radius: 8px 8px 0 0 !important;
    padding: 8px 18px !important; font-weight: 500 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: rgba(99,102,241,0.18) !important; color: #fff !important;
    border-bottom: 2px solid #818cf8 !important;
}

/* Expanders */
[data-testid="stExpander"] { border: 1px solid rgba(129,140,248,0.15) !important; border-radius: 10px !important; margin-bottom: 6px; }
[data-testid="stExpander"] summary { color: #c4b5fd !important; font-weight: 600 !important; }

/* Buttons */
.stButton > button {
    background: rgba(99,102,241,0.16) !important; border: 1px solid rgba(129,140,248,0.35) !important;
    color: #ddd6fe !important; border-radius: 10px !important; font-weight: 600 !important; transition: all 0.15s !important;
}
.stButton > button:hover { background: rgba(99,102,241,0.30) !important; color: white !important; transform: translateY(-1px) !important; }

/* Customer card */
.cust-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.10), rgba(139,92,246,0.05));
    border: 1px solid rgba(129,140,248,0.20); border-radius: 16px; padding: 20px 24px; margin-bottom: 16px;
}
.cust-avatar {
    width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; font-weight: 700; color: white; flex-shrink: 0;
}
.product-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(129,140,248,0.15);
    border-radius: 12px; padding: 14px 16px; height: 100%;
}

/* Badges */
.badge { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
.badge-active   { background: rgba(52,211,153,0.15); color: #6ee7b7; border: 1px solid rgba(52,211,153,0.3); }
.badge-risk     { background: rgba(251,191,36,0.15);  color: #fcd34d; border: 1px solid rgba(251,191,36,0.3); }
.badge-churned  { background: rgba(148,163,184,0.15); color: #cbd5e1; border: 1px solid rgba(148,163,184,0.3); }
.badge-over     { background: rgba(248,113,113,0.15); color: #fca5a5; border: 1px solid rgba(248,113,113,0.3); }
.badge-under    { background: rgba(251,191,36,0.15);  color: #fcd34d; border: 1px solid rgba(251,191,36,0.3); }
.badge-healthy  { background: rgba(52,211,153,0.15);  color: #6ee7b7; border: 1px solid rgba(52,211,153,0.3); }
.badge-campaign { background: rgba(99,102,241,0.15);  color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); }

/* Divider */
hr { border-color: rgba(129,140,248,0.12) !important; margin: 1.5rem 0 !important; }

/* Input */
.stTextInput > div > div > input {
    background: rgba(13,11,30,0.9) !important; border: 1px solid rgba(129,140,248,0.3) !important;
    border-radius: 10px !important; color: #ffffff !important; caret-color: #fff !important;
    -webkit-text-fill-color: #fff !important;
}
.stTextInput > div > div > input:focus { border-color: #818cf8 !important; box-shadow: 0 0 0 3px rgba(129,140,248,0.15) !important; }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {"active": "badge-active", "at_risk": "badge-risk", "churned": "badge-churned"}.get(status, "badge-active")
    label = status.replace("_", " ").title()
    return f'<span class="badge {cls}">{label}</span>'


def util_badge(util_pct: float) -> str:
    if util_pct > 100:
        return f'<span class="badge badge-over">▲ Over by {util_pct:.0f}%</span>'
    if util_pct < 50:
        return f'<span class="badge badge-under">▼ Under {util_pct:.0f}%</span>'
    return f'<span class="badge badge-healthy">✓ Healthy {util_pct:.0f}%</span>'


def campaign_badge(campaign: str) -> str:
    return f'<span class="badge badge-campaign">📣 {campaign}</span>'


def avatar(name: str) -> str:
    initials = "".join(w[0].upper() for w in name.split()[:2])
    return f'<div class="cust-avatar">{initials}</div>'
