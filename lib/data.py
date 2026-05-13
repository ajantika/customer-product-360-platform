"""Cached parquet loaders."""
from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

@st.cache_data(show_spinner=False)
def load_customers() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "customers.parquet")

@st.cache_data(show_spinner=False)
def load_products() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "products.parquet")

@st.cache_data(show_spinner=False)
def load_subscriptions() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "subscriptions.parquet")

@st.cache_data(show_spinner=False)
def load_usage() -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / "usage_monthly.parquet")
    df["month"] = pd.to_datetime(df["month"])
    return df

@st.cache_data(show_spinner=False)
def load_pricing_regions() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "pricing_regions.parquet")

@st.cache_data(show_spinner=False)
def load_customer_region_usage() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "customer_region_usage.parquet")

@st.cache_data(show_spinner=False)
def load_all() -> dict:
    return {
        "customers": load_customers(),
        "products":  load_products(),
        "subscriptions": load_subscriptions(),
        "usage":     load_usage(),
        "pricing_regions": load_pricing_regions(),
        "customer_region_usage": load_customer_region_usage(),
    }
