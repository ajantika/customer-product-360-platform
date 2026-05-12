"""Plotly chart factories with consistent dark-theme styling."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PRIMARY = "#818cf8"
ACCENT = "#c4b5fd"
OVER = "#f87171"
UNDER = "#fbbf24"
HEALTHY = "#34d399"
BG = "rgba(0,0,0,0)"
GRID = "rgba(255,255,255,0.08)"


def _style(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color="#e5e7eb", family="-apple-system, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def bar_mom(df: pd.DataFrame, title: str = "Month-over-month usage (% of plan)") -> go.Figure:
    df = df.copy()
    df["month_label"] = df["month"].dt.strftime("%b %Y")
    colors = [OVER if v > 100 else UNDER if v < 50 else PRIMARY for v in df["utilization_pct"]]
    fig = go.Figure(go.Bar(
        x=df["month_label"],
        y=df["utilization_pct"],
        marker_color=colors,
        text=[f"{v:.0f}%" for v in df["utilization_pct"]],
        textposition="outside",
    ))
    fig.add_hline(y=100, line_dash="dash", line_color=OVER, opacity=0.5)
    fig.update_layout(title=title, yaxis_title="% of plan", xaxis_title=None)
    return _style(fig, height=360)


def regional_bar(df: pd.DataFrame, value_col: str, title: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df["region"],
        y=df[value_col],
        marker_color=PRIMARY,
        text=[f"{v:,.0f}" if value_col != "adoption_pct" else f"{v:.0f}%" for v in df[value_col]],
        textposition="outside",
    ))
    fig.update_layout(title=title, xaxis_title=None, yaxis_title=None)
    return _style(fig, height=300)


def horizontal_adoption(df: pd.DataFrame, title: str = "Top products by adoption") -> go.Figure:
    df = df.sort_values("adoption_pct").head(8)
    fig = go.Figure(go.Bar(
        x=df["adoption_pct"],
        y=df["name"],
        orientation="h",
        marker_color=ACCENT,
        text=[f"{v:.0f}%" for v in df["adoption_pct"]],
        textposition="outside",
    ))
    fig.update_layout(title=title, xaxis_title="% of active customers", yaxis_title=None)
    return _style(fig, height=320)


def utilization_distribution(values: list[float], title: str = "Customer utilization distribution") -> go.Figure:
    fig = go.Figure(go.Histogram(x=values, nbinsx=30, marker_color=PRIMARY))
    fig.add_vline(x=50, line_dash="dash", line_color=UNDER, opacity=0.6)
    fig.add_vline(x=100, line_dash="dash", line_color=OVER, opacity=0.6)
    fig.update_layout(title=title, xaxis_title="Avg utilization %", yaxis_title="customers")
    return _style(fig, height=300)
