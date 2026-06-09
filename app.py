import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide", page_title="NIFTY 100 Scanner", page_icon="📈")

# ─── GLOBAL THEME INJECTION ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root palette ── */
:root {
    --bg-base:       #0A0C10;
    --bg-surface:    #10141C;
    --bg-card:       #151A24;
    --bg-elevated:   #1C2232;
    --border:        #1F2A3C;
    --border-bright: #2E3D56;

    --text-primary:  #E8EDF5;
    --text-secondary:#8A9ABB;
    --text-muted:    #4A5A78;

    --green:         #00E5A0;
    --green-dim:     #003D2B;
    --red:           #FF4D6A;
    --red-dim:       #3D0012;
    --amber:         #F5A623;
    --amber-dim:     #3D2800;
    --blue-accent:   #3B82F6;
    --blue-dim:      #0D2045;

    --font-ui:       'Space Grotesk', sans-serif;
    --font-mono:     'JetBrains Mono', monospace;
}

/* ── Base reset ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Header ── */
[data-testid="stHeader"] {
    background-color: var(--bg-base) !important;
}

/* ── Page title ── */
h1 {
    font-family: var(--font-ui) !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
    padding: 0.5rem 0 0.2rem !important;
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 1.2rem !important;
}

/* ── Subheaders ── */
h2, h3 {
    font-family: var(--font-ui) !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin-top: 1.4rem !important;
    margin-bottom: 0.6rem !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="metric-container"] label {
    font-family: var(--font-ui) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 1.6rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
iframe[title="st_aggrid"] { background: var(--bg-card); }

/* Streamlit native dataframe cells */
[data-testid="stDataFrame"] table {
    background: var(--bg-card) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.78rem !important;
}
[data-testid="stDataFrame"] th {
    background: var(--bg-elevated) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-ui) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--border-bright) !important;
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stDataFrame"] td {
    color: var(--text-primary) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0.5rem 0.8rem !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background: var(--bg-elevated) !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 6px !important;
    font-family: var(--font-ui) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="stButton"] > button:hover {
    background: var(--blue-dim) !important;
    border-color: var(--blue-accent) !important;
    color: var(--blue-accent) !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label {
    font-family: var(--font-ui) !important;
    font-size: 0.82rem !important;
    color: var(--text-secondary) !important;
}
[data-testid="stRadio"] [data-baseweb="radio"] input:checked + div {
    border-color: var(--blue-accent) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
    font-size: 0.82rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--bg-surface) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: var(--font-ui) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.7rem 1.2rem !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--blue-accent) !important;
    border-bottom-color: var(--blue-accent) !important;
    background: transparent !important;
}

/* ── Sidebar labels ── */
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
    font-family: var(--font-ui) !important;
    font-size: 0.82rem !important;
    color: var(--text-secondary) !important;
}
[data-testid="stSidebar"] strong {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] code {
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    background: var(--bg-elevated) !important;
    color: var(--green) !important;
    padding: 0.15rem 0.4rem !important;
    border-radius: 4px !important;
    border: 1px solid var(--border) !important;
}

/* ── Info / alert boxes ── */
[data-testid="stAlert"] {
    background: var(--blue-dim) !important;
    border: 1px solid var(--blue-accent) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
    font-size: 0.82rem !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 1.2rem 0 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] p {
    font-family: var(--font-ui) !important;
    font-size: 0.82rem !important;
    color: var(--text-secondary) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
""", unsafe_allow_html=True)

# ─── CUSTOM HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; padding:0.2rem 0 1.2rem;">
    <div style="
        background: linear-gradient(135deg, #1C2E4A 0%, #0D2045 100%);
        border: 1px solid #3B82F6;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 1.3rem;
        line-height:1;
    ">📈</div>
    <div>
        <div style="
            font-family:'Space Grotesk',sans-serif;
            font-weight:700;
            font-size:1.25rem;
            letter-spacing:-0.02em;
            color:#E8EDF5;
            line-height:1.2;
        ">NIFTY 100 Blue-Chip Scanner</div>
        <div style="
            font-family:'JetBrains Mono',monospace;
            font-size:0.7rem;
            color:#4A5A78;
            letter-spacing:0.06em;
            text-transform:uppercase;
        ">Multi-Timeframe · Structural · Live</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── INITIALIZATION ────────────────────────────────────────────────────────────
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

def fetch_india_vix(kite):
    try:
        vix_data = kite.ltp("NSE:INDIA VIX")
        return float(vix_data["NSE:INDIA VIX"]["last_price"])
    except Exception:
        return 14.5

def load_metadata():
    csv_path = "stock_metadata.csv"
    nifty100_universe = {
        "ADANIENT": {"Industry": "Metals & Mining", "Promoter": 72.6, "PE": 45.2, "Ind_PE": 24.1, "PB": 4.2, "ROCE": 12.5},
        "ADANIPORTS": {"Industry": "Infrastructure / Services", "Promoter": 65.3, "PE": 33.1, "Ind_PE": 28.5, "PB": 3.9, "ROCE": 14.8},
        "APOLLOHOSP": {"Industry": "Healthcare", "Promoter": 29.3, "PE": 78.4, "Ind_PE": 38.2, "PB": 9.1, "ROCE": 16.2},
        "ASIANPAINT": {"Industry": "Consumer Durables", "Promoter": 52.6, "PE": 55.4, "Ind_PE": 51.2, "PB": 14.2, "ROCE": 34.1},
        "AXISBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 14.1, "Ind_PE": 15.2, "PB": 2.1, "ROCE": 11.2},
        "BAJAJ-AUTO": {"Industry": "Automobile", "Promoter": 55.0, "PE": 31.2, "Ind_PE": 26.4, "PB": 8.4, "ROCE": 30.5},
        "BAJFINANCE": {"Industry": "Financial Services", "Promoter": 54.7, "PE": 28.3, "Ind_PE": 22.1, "PB": 5.8, "ROCE": 17.4},
        "BAJAJFINSV": {"Industry": "Financial Services", "Promoter": 60.7, "PE": 33.4, "Ind_PE": 22.1, "PB": 4.1, "ROCE": 14.9},
        "BEL": {"Industry": "Capital Goods", "Promoter": 51.1, "PE": 42.6, "Ind_PE": 35.4, "PB": 7.8, "ROCE": 26.3},
        "BHARTIARTL": {"Industry": "Telecommunication", "Promoter": 53.1, "PE": 52.1, "Ind_PE": 41.3, "PB": 8.9, "ROCE": 18.2},
        "BPCL": {"Industry": "Oil & Gas", "Promoter": 53.0, "PE": 11.4, "Ind_PE": 12.8, "PB": 1.7, "ROCE": 22.1},
        "BRITANNIA": {"Industry": "FMCG", "Promoter": 50.5, "PE": 54.3, "Ind_PE": 44.2, "PB": 28.1, "ROCE": 48.6},
        "CIPLA": {"Industry": "Healthcare", "Promoter": 33.4, "PE": 29.6, "Ind_PE": 31.4, "PB": 4.3, "ROCE": 21.3},
        "COALINDIA": {"Industry": "Oil & Gas", "Promoter": 63.1, "PE": 9.2, "Ind_PE": 12.8, "PB": 3.4, "ROCE": 54.2},
        "DRREDDY": {"Industry": "Healthcare", "Promoter": 26.7, "PE": 18.9, "Ind_PE": 31.4, "PB": 3.1, "ROCE": 24.5},
        "EICHERMOT": {"Industry": "Automobile", "Promoter": 49.2, "PE": 29.1, "Ind_PE": 26.4, "PB": 7.2, "ROCE": 27.8},
        "GRASIM": {"Industry": "Construction Materials", "Promoter": 42.7, "PE": 44.1, "Ind_PE": 32.1, "PB": 1.9, "ROCE": 9.4},
        "HCLTECH": {"Industry": "Information Technology", "Promoter": 60.8, "PE": 25.4, "Ind_PE": 28.2, "PB": 6.1, "ROCE": 28.9},
        "HDFCBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 18.2, "Ind_PE": 15.2, "PB": 2.6, "ROCE": 12.1},
        "HDFCLIFE": {"Industry": "Financial Services", "Promoter": 50.4, "PE": 61.2, "Ind_PE": 55.4, "PB": 4.8, "ROCE": 14.2},
        "HINDALCO": {"Industry": "Metals & Mining", "Promoter": 34.6, "PE": 16.3, "Ind_PE": 18.4, "PB": 1.8, "ROCE": 13.1},
        "HINDUNILVR": {"Industry": "FMCG", "Promoter": 61.9, "PE": 56.2, "Ind_PE": 44.2, "PB": 11.4, "ROCE": 39.5},
        "ICICIBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 17.4, "Ind_PE": 15.2, "PB": 3.1, "ROCE": 13.4},
        "INDUSINDBK": {"Industry": "Financial Services", "Promoter": 16.5, "PE": 13.2, "Ind_PE": 15.2, "PB": 1.8, "ROCE": 11.7},
        "INFY": {"Industry": "Information Technology", "Promoter": 14.8, "PE": 24.1, "Ind_PE": 28.2, "PB": 7.4, "ROCE": 37.2},
        "INDIGO": {"Industry": "Infrastructure / Services", "Promoter": 57.3, "PE": 21.4, "Ind_PE": 25.1, "PB": 5.2, "ROCE": 22.4},
        "ITC": {"Industry": "FMCG", "Promoter": 0.0, "PE": 26.4, "Ind_PE": 44.2, "PB": 7.9, "ROCE": 38.7},
        "JSWSTEEL": {"Industry": "Metals & Mining", "Promoter": 44.8, "PE": 27.2, "Ind_PE": 18.4, "PB": 3.2, "ROCE": 14.1},
        "JIOFIN": {"Industry": "Financial Services", "Promoter": 47.1, "PE": 120.5, "Ind_PE": 22.1, "PB": 2.1, "ROCE": 6.2},
        "KOTAKBANK": {"Industry": "Financial Services", "Promoter": 25.9, "PE": 19.1, "Ind_PE": 15.2, "PB": 2.9, "ROCE": 12.8},
        "LT": {"Industry": "Construction", "Promoter": 0.0, "PE": 36.4, "Ind_PE": 31.2, "PB": 4.8, "ROCE": 15.1},
        "M&M": {"Industry": "Automobile", "Promoter": 19.3, "PE": 28.4, "Ind_PE": 26.4, "PB": 4.9, "ROCE": 19.2},
        "MARUTI": {"Industry": "Automobile", "Promoter": 58.2, "PE": 27.5, "Ind_PE": 26.4, "PB": 5.1, "ROCE": 21.4},
        "MAXHEALTH": {"Industry": "Healthcare", "Promoter": 23.1, "PE": 68.2, "Ind_PE": 38.2, "PB": 8.4, "ROCE": 15.5},
        "NESTLEIND": {"Industry": "FMCG", "Promoter": 62.8, "PE": 74.2, "Ind_PE": 44.2, "PB": 21.4, "ROCE": 58.1},
        "NTPC": {"Industry": "Power", "Promoter": 51.1, "PE": 17.5, "Ind_PE": 19.4, "PB": 2.4, "ROCE": 11.9},
        "ONGC": {"Industry": "Oil & Gas", "Promoter": 58.9, "PE": 8.1, "Ind_PE": 12.8, "PB": 1.1, "ROCE": 14.5},
        "POWERGRID": {"Industry": "Power", "Promoter": 51.3, "PE": 16.2, "Ind_PE": 19.4, "PB": 2.9, "ROCE": 12.4},
        "RELIANCE": {"Industry": "Oil & Gas", "Promoter": 50.3, "PE": 26.1, "Ind_PE": 12.8, "PB": 2.4, "ROCE": 10.2},
        "SBILIFE": {"Industry": "Financial Services", "Promoter": 55.4, "PE": 78.1, "Ind_PE": 55.4, "PB": 9.5, "ROCE": 13.1},
        "SBIN": {"Industry": "Financial Services", "Promoter": 57.5, "PE": 10.4, "Ind_PE": 15.2, "PB": 1.6, "ROCE": 11.8},
        "SHRIRAMFIN": {"Industry": "Financial Services", "Promoter": 25.4, "PE": 14.8, "Ind_PE": 22.1, "PB": 2.2, "ROCE": 15.4},
        "SUNPHARMA": {"Industry": "Healthcare", "Promoter": 54.5, "PE": 36.2, "Ind_PE": 31.4, "PB": 4.9, "ROCE": 17.2},
        "TATACONSUM": {"Industry": "FMCG", "Promoter": 34.4, "PE": 64.1, "Ind_PE": 44.2, "PB": 4.1, "ROCE": 9.8},
        "TATAMOTORS": {"Industry": "Automobile", "Promoter": 46.4, "PE": 11.5, "Ind_PE": 26.4, "PB": 3.2, "ROCE": 20.1},
        "TATASTEEL": {"Industry": "Metals & Mining", "Promoter": 33.2, "PE": 38.4, "Ind_PE": 18.4, "PB": 1.7, "ROCE": 10.5},
        "TCS": {"Industry": "Information Technology", "Promoter": 72.4, "PE": 29.5, "Ind_PE": 28.2, "PB": 12.8, "ROCE": 51.4},
        "TECHM": {"Industry": "Information Technology", "Promoter": 35.1, "PE": 48.2, "Ind_PE": 28.2, "PB": 3.8, "ROCE": 15.9},
        "TITAN": {"Industry": "Consumer Durables", "Promoter": 52.9, "PE": 82.1, "Ind_PE": 51.2, "PB": 19.4, "ROCE": 25.1},
        "TRENT": {"Industry": "Retail", "Promoter": 37.0, "PE": 145.2, "Ind_PE": 68.4, "PB": 28.4, "ROCE": 24.3},
        "ULTRACEMCO": {"Industry": "Construction Materials", "Promoter": 60.0, "PE": 41.2, "Ind_PE": 32.1, "PB": 4.7, "ROCE": 13.8},
        "UPL": {"Industry": "Chemicals", "Promoter": 32.4, "PE": 22.1, "Ind_PE": 19.5, "PB": 1.5, "ROCE": 11.1},
        "WIPRO": {"Industry": "Information Technology", "Promoter": 72.9, "PE": 23.4, "Ind_PE": 28.2, "PB": 3.4, "ROCE": 21.2},
        # ── Nifty 100 additions ──────────────────────────────────────────────
        "ABB": {"Industry": "Capital Goods", "Promoter": 75.0, "PE": 62.4, "Ind_PE": 35.4, "PB": 14.2, "ROCE": 28.6},
        "ADANIGREEN": {"Industry": "Power", "Promoter": 56.3, "PE": 185.2, "Ind_PE": 19.4, "PB": 22.1, "ROCE": 8.4},
        "ADANIPOWER": {"Industry": "Power", "Promoter": 74.2, "PE": 14.6, "Ind_PE": 19.4, "PB": 4.8, "ROCE": 22.1},
        "AMBUJACEM": {"Industry": "Construction Materials", "Promoter": 63.2, "PE": 38.1, "Ind_PE": 32.1, "PB": 3.4, "ROCE": 10.2},
        "ATGL": {"Industry": "Oil & Gas", "Promoter": 74.8, "PE": 68.4, "Ind_PE": 12.8, "PB": 8.9, "ROCE": 18.4},
        "AUROPHARMA": {"Industry": "Healthcare", "Promoter": 51.8, "PE": 22.4, "Ind_PE": 31.4, "PB": 3.2, "ROCE": 19.5},
        "BAJAJHLDNG": {"Industry": "Financial Services", "Promoter": 57.2, "PE": 18.4, "Ind_PE": 22.1, "PB": 2.8, "ROCE": 14.1},
        "BANKBARODA": {"Industry": "Financial Services", "Promoter": 63.9, "PE": 6.8, "Ind_PE": 15.2, "PB": 1.1, "ROCE": 9.8},
        "BERGEPAINT": {"Industry": "Consumer Durables", "Promoter": 74.9, "PE": 52.1, "Ind_PE": 51.2, "PB": 12.4, "ROCE": 28.9},
        "BOSCHLTD": {"Industry": "Automobile", "Promoter": 70.5, "PE": 38.2, "Ind_PE": 26.4, "PB": 6.8, "ROCE": 22.4},
        "CANBK": {"Industry": "Financial Services", "Promoter": 62.9, "PE": 7.2, "Ind_PE": 15.2, "PB": 1.0, "ROCE": 9.1},
        "CHOLAFIN": {"Industry": "Financial Services", "Promoter": 51.4, "PE": 28.6, "Ind_PE": 22.1, "PB": 4.8, "ROCE": 16.2},
        "COLPAL": {"Industry": "FMCG", "Promoter": 51.0, "PE": 48.6, "Ind_PE": 44.2, "PB": 18.4, "ROCE": 52.1},
        "CUMMINSIND": {"Industry": "Capital Goods", "Promoter": 51.0, "PE": 44.2, "Ind_PE": 35.4, "PB": 9.8, "ROCE": 30.1},
        "DABUR": {"Industry": "FMCG", "Promoter": 67.9, "PE": 46.2, "Ind_PE": 44.2, "PB": 9.6, "ROCE": 24.8},
        "DLABLS": {"Industry": "Healthcare", "Promoter": 74.9, "PE": 46.8, "Ind_PE": 31.4, "PB": 7.2, "ROCE": 22.1},
        "DLF": {"Industry": "Real Estate", "Promoter": 74.9, "PE": 52.4, "Ind_PE": 38.6, "PB": 4.2, "ROCE": 9.8},
        "FEDERALBNK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 10.4, "Ind_PE": 15.2, "PB": 1.4, "ROCE": 11.2},
        "GAIL": {"Industry": "Oil & Gas", "Promoter": 51.9, "PE": 12.4, "Ind_PE": 12.8, "PB": 1.6, "ROCE": 14.8},
        "GODREJCP": {"Industry": "FMCG", "Promoter": 63.2, "PE": 42.6, "Ind_PE": 44.2, "PB": 8.4, "ROCE": 21.4},
        "GODREJPROP": {"Industry": "Real Estate", "Promoter": 58.5, "PE": 68.4, "Ind_PE": 38.6, "PB": 5.8, "ROCE": 8.6},
        "HAL": {"Industry": "Capital Goods", "Promoter": 71.6, "PE": 38.4, "Ind_PE": 35.4, "PB": 9.2, "ROCE": 28.4},
        "HAVELLS": {"Industry": "Capital Goods", "Promoter": 59.6, "PE": 64.2, "Ind_PE": 35.4, "PB": 12.8, "ROCE": 24.6},
        "HEROMOTOCO": {"Industry": "Automobile", "Promoter": 34.6, "PE": 20.4, "Ind_PE": 26.4, "PB": 5.2, "ROCE": 32.8},
        "ICICIlombard": {"Industry": "Financial Services", "Promoter": 51.9, "PE": 38.2, "Ind_PE": 55.4, "PB": 6.4, "ROCE": 15.8},
        "ICICIPRU": {"Industry": "Financial Services", "Promoter": 74.0, "PE": 72.4, "Ind_PE": 55.4, "PB": 8.2, "ROCE": 12.4},
        "IDBI": {"Industry": "Financial Services", "Promoter": 94.7, "PE": 14.8, "Ind_PE": 15.2, "PB": 1.8, "ROCE": 10.4},
        "IDFCFIRSTB": {"Industry": "Financial Services", "Promoter": 36.6, "PE": 22.4, "Ind_PE": 15.2, "PB": 1.6, "ROCE": 9.8},
        "IGL": {"Industry": "Oil & Gas", "Promoter": 45.0, "PE": 22.8, "Ind_PE": 12.8, "PB": 4.2, "ROCE": 21.4},
        "IOC": {"Industry": "Oil & Gas", "Promoter": 51.5, "PE": 6.8, "Ind_PE": 12.8, "PB": 1.0, "ROCE": 18.2},
        "IRCTC": {"Industry": "Infrastructure / Services", "Promoter": 67.4, "PE": 48.6, "Ind_PE": 25.1, "PB": 14.8, "ROCE": 38.4},
        "IRFC": {"Industry": "Financial Services", "Promoter": 86.4, "PE": 28.4, "Ind_PE": 22.1, "PB": 4.2, "ROCE": 6.8},
        "LTIM": {"Industry": "Information Technology", "Promoter": 74.3, "PE": 34.6, "Ind_PE": 28.2, "PB": 8.4, "ROCE": 32.4},
        "LTTS": {"Industry": "Information Technology", "Promoter": 74.2, "PE": 32.8, "Ind_PE": 28.2, "PB": 6.8, "ROCE": 28.6},
        "LUPIN": {"Industry": "Healthcare", "Promoter": 47.0, "PE": 28.4, "Ind_PE": 31.4, "PB": 4.6, "ROCE": 18.4},
        "MARICO": {"Industry": "FMCG", "Promoter": 59.4, "PE": 44.8, "Ind_PE": 44.2, "PB": 14.6, "ROCE": 42.8},
        "MCDOWELL-N": {"Industry": "FMCG", "Promoter": 56.0, "PE": 62.4, "Ind_PE": 44.2, "PB": 8.4, "ROCE": 22.6},
        "MOTHERSON": {"Industry": "Automobile", "Promoter": 58.3, "PE": 38.6, "Ind_PE": 26.4, "PB": 4.8, "ROCE": 14.2},
        "MPHASIS": {"Industry": "Information Technology", "Promoter": 55.6, "PE": 28.4, "Ind_PE": 28.2, "PB": 5.8, "ROCE": 24.6},
        "MRF": {"Industry": "Automobile", "Promoter": 27.8, "PE": 24.6, "Ind_PE": 26.4, "PB": 3.4, "ROCE": 16.8},
        "MUTHOOTFIN": {"Industry": "Financial Services", "Promoter": 73.4, "PE": 18.4, "Ind_PE": 22.1, "PB": 3.6, "ROCE": 18.2},
        "NMDC": {"Industry": "Metals & Mining", "Promoter": 60.8, "PE": 9.4, "Ind_PE": 18.4, "PB": 2.2, "ROCE": 28.4},
        "NYKAA": {"Industry": "Retail", "Promoter": 52.6, "PE": 148.6, "Ind_PE": 68.4, "PB": 18.4, "ROCE": 8.6},
        "OBEROIRLTY": {"Industry": "Real Estate", "Promoter": 67.7, "PE": 28.6, "Ind_PE": 38.6, "PB": 4.8, "ROCE": 18.4},
        "OFSS": {"Industry": "Information Technology", "Promoter": 72.8, "PE": 32.4, "Ind_PE": 28.2, "PB": 8.6, "ROCE": 38.4},
        "PAGEIND": {"Industry": "Consumer Durables", "Promoter": 59.0, "PE": 64.8, "Ind_PE": 51.2, "PB": 28.4, "ROCE": 58.6},
        "PAYTM": {"Industry": "Financial Services", "Promoter": 19.4, "PE": 0.0, "Ind_PE": 22.1, "PB": 2.8, "ROCE": -4.2},
        "PEL": {"Industry": "Financial Services", "Promoter": 43.8, "PE": 18.4, "Ind_PE": 22.1, "PB": 1.6, "ROCE": 8.4},
        "PERSISTENT": {"Industry": "Information Technology", "Promoter": 31.1, "PE": 58.4, "Ind_PE": 28.2, "PB": 12.4, "ROCE": 28.6},
        "PETRONET": {"Industry": "Oil & Gas", "Promoter": 50.0, "PE": 12.8, "Ind_PE": 12.8, "PB": 2.8, "ROCE": 24.6},
        "PFC": {"Industry": "Financial Services", "Promoter": 55.9, "PE": 8.6, "Ind_PE": 22.1, "PB": 1.6, "ROCE": 8.2},
        "PIDILITIND": {"Industry": "Chemicals", "Promoter": 70.7, "PE": 72.4, "Ind_PE": 19.5, "PB": 18.4, "ROCE": 32.4},
        "PIIND": {"Industry": "Chemicals", "Promoter": 52.0, "PE": 28.6, "Ind_PE": 19.5, "PB": 4.8, "ROCE": 18.6},
        "PNB": {"Industry": "Financial Services", "Promoter": 73.2, "PE": 8.4, "Ind_PE": 15.2, "PB": 0.9, "ROCE": 8.6},
        "POLYCAB": {"Industry": "Capital Goods", "Promoter": 67.7, "PE": 42.6, "Ind_PE": 35.4, "PB": 8.4, "ROCE": 24.8},
        "RECLTD": {"Industry": "Financial Services", "Promoter": 52.6, "PE": 9.2, "Ind_PE": 22.1, "PB": 1.8, "ROCE": 8.6},
        "SIEMENS": {"Industry": "Capital Goods", "Promoter": 75.0, "PE": 72.8, "Ind_PE": 35.4, "PB": 14.8, "ROCE": 22.4},
        "SRF": {"Industry": "Chemicals", "Promoter": 50.6, "PE": 38.4, "Ind_PE": 19.5, "PB": 5.8, "ROCE": 14.8},
        "TORNTPHARM": {"Industry": "Healthcare", "Promoter": 71.3, "PE": 38.6, "Ind_PE": 31.4, "PB": 8.4, "ROCE": 22.4},
        "TORNTPOWER": {"Industry": "Power", "Promoter": 72.8, "PE": 28.4, "Ind_PE": 19.4, "PB": 4.8, "ROCE": 14.6},
        "TVSMOTOR": {"Industry": "Automobile", "Promoter": 57.4, "PE": 42.8, "Ind_PE": 26.4, "PB": 12.4, "ROCE": 26.8},
        "UNIONBANK": {"Industry": "Financial Services", "Promoter": 74.8, "PE": 6.8, "Ind_PE": 15.2, "PB": 0.9, "ROCE": 8.8},
        "VEDL": {"Industry": "Metals & Mining", "Promoter": 56.4, "PE": 12.4, "Ind_PE": 18.4, "PB": 2.8, "ROCE": 18.4},
        "VOLTAS": {"Industry": "Capital Goods", "Promoter": 30.3, "PE": 68.4, "Ind_PE": 35.4, "PB": 8.6, "ROCE": 14.2},
        "ZOMATO": {"Industry": "Infrastructure / Services", "Promoter": 0.0, "PE": 248.6, "Ind_PE": 25.1, "PB": 8.4, "ROCE": 4.2},
        "ZYDUSLIFE": {"Industry": "Healthcare", "Promoter": 74.9, "PE": 28.4, "Ind_PE": 31.4, "PB": 4.8, "ROCE": 18.6},
    }

    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if not df.empty and ("Ticker" in df.columns or "Symbol" in df.columns):
                rename_map = {
                    "Symbol": "Ticker", "Promoter Holding (%)": "Promoter_Percent",
                    "Promoter Holding": "Promoter_Percent", "Stock PE": "Stock_PE",
                    "PE": "Stock_PE", "Industry PE": "Industry_PE", "Price to Book": "PB", "P/B": "PB"
                }
                df = df.rename(columns=rename_map)
                df = df[df["Ticker"].isin(nifty100_universe.keys())]
                return df
        except Exception as e:
            st.error(f"⚠️ CSV parsing error: {e}")

    fallback_data = [{
        "Ticker": ticker, "Industry": data["Industry"], "Promoter_Percent": data["Promoter"],
        "Stock_PE": data["PE"], "Industry_PE": data["Ind_PE"], "PB": data["PB"], "ROCE": data["ROCE"]
    } for ticker, data in nifty100_universe.items()]
    return pd.DataFrame(fallback_data)

# ─── TECHNICAL METRICS ENGINE ──────────────────────────────────────────────────
def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def calculate_session_pivots(df_1d):
    if len(df_1d) < 2:
        return 0.0, 0.0, 0.0
    prev_day = df_1d.iloc[-2]
    high_val = float(prev_day['high'])
    low_val = float(prev_day['low'])
    close_val = float(prev_day['close'])
    p = (high_val + low_val + close_val) / 3.0
    r1 = p + 0.382 * (high_val - low_val)
    s1 = p - 0.382 * (high_val - low_val)
    return round(p, 2), round(r1, 2), round(s1, 2)

def get_last_crossover_details(df):
    if len(df) < 2: return 0.0, "No Cross", 0
    df = df.copy().dropna(subset=['VWMA_9', 'VWMA_26']).reset_index(drop=True)
    df['diff'] = df['VWMA_9'] - df['VWMA_26']
    df['sign'] = (df['diff'] > 0).astype(int)
    crosses = df[df['sign'] != df['sign'].shift(1)].iloc[1:]
    if not crosses.empty:
        last_cross_row = crosses.iloc[-1]
        bars_ago = len(df) - 1 - crosses.index[-1]
        c_type = "🔥 Bullish" if last_cross_row['VWMA_9'] > last_cross_row['VWMA_26'] else "❄️ Bearish"
        return round(last_cross_row['VWMA_9'], 2), c_type, int(bars_ago)
    return 0.0, "No Cross", 0

# ─── DATA COMPILER ─────────────────────────────────────────────────────────────
def execute_parallel_scan(meta_df, token_lookup, kite, india_vix):
    scan_results = []

    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token: return None
        try:
            hist_1d = kite.historical_data(token, from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="day")
            hist_15m = kite.historical_data(token, from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="15minute")
            if not hist_1d or not hist_15m: return None

            df_1d = calculate_indicators(pd.DataFrame(hist_1d))
            df_15m = calculate_indicators(pd.DataFrame(hist_15m))
            p_val, r1_val, s1_val = calculate_session_pivots(df_1d)

            timeframes = {"15M": df_15m, "1D": df_1d}
            stock_data = {
                "Stock Name": symbol,
                "Industry": row.get("Industry", "Blue-Chip Core"),
                "Promoter Holding (%)": row.get("Promoter_Percent", 0.0),
                "Stock PE": row.get("Stock_PE", 0.0),
                "Industry PE": row.get("Industry_PE", 0.0),
                "PB": row.get("PB", 0.0),
                "ROCE": row.get("ROCE", 0.0),
                "LTP": round(float(df_15m.iloc[-1]['close']), 2)
            }

            for tf_suffix, df_tf in timeframes.items():
                latest = df_tf.iloc[-1]
                ltp = round(float(latest['close']), 2)
                v9 = float(latest['VWMA_9'])
                v26 = float(latest['VWMA_26'])
                rsi = float(latest['RSI'])
                cross_val, cross_type, periods_ago = get_last_crossover_details(df_tf)

                signal = "⚪ NEUTRAL"
                target_val = 0.0
                sl_val = 0.0

                if india_vix < 15.0:
                    if ltp > (1.01 * v9) and v9 > v26:
                        signal = "🟢 BUY"
                        target_val = round(ltp * 1.015, 2)
                        sl_val = round(ltp * 0.99, 2)
                    elif ltp < (0.99 * v9) and v9 < v26:
                        signal = "🔴 SELL"
                        target_val = round(ltp * 0.985, 2)
                        sl_val = round(ltp * 1.01, 2)
                else:
                    mid_r1_p = (r1_val + p_val) / 2.0
                    mid_s1_p = (s1_val + p_val) / 2.0
                    is_bullish = ("Bullish" in cross_type or (v9 > v26)) and rsi > 50
                    is_bearish = ("Bearish" in cross_type or (v9 < v26)) and rsi < 50
                    if is_bullish:
                        if ltp <= mid_r1_p:
                            signal = "🟢 BUY"
                            target_val = r1_val
                            target_dist = r1_val - ltp
                            sl_val = round(ltp - (target_dist / 1.5), 2)
                    elif is_bearish:
                        if ltp >= mid_s1_p:
                            signal = "🔴 SELL"
                            target_val = s1_val
                            target_dist = ltp - s1_val
                            sl_val = round(ltp + (target_dist / 1.5), 2)

                within_cross = "🎯 YES" if (cross_val * 0.99) <= ltp <= (cross_val * 1.01) else "No"
                stock_data.update({
                    f"Action Signal ({tf_suffix})": signal,
                    f"Target ({tf_suffix})": target_val,
                    f"StopLoss ({tf_suffix})": sl_val,
                    f"RSI ({tf_suffix})": round(rsi, 2),
                    f"Last Cross Value ({tf_suffix})": cross_val,
                    f"Last Cross Type ({tf_suffix})": f"{cross_type} ({periods_ago} periods ago)",
                    f"Within 1% of Cross ({tf_suffix})": within_cross,
                    f"P / R1 / S1 ({tf_suffix})": f"{p_val} | {r1_val} | {s1_val}"
                })
            return stock_data
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, row) for _, row in meta_df.iterrows()]
        for future in as_completed(futures):
            res = future.result()
            if res: scan_results.append(res)
    return scan_results

# ─── DASHBOARD ─────────────────────────────────────────────────────────────────
def run_integrated_pipeline():
    meta_df = load_metadata()
    if meta_df is None or meta_df.empty: return

    kite = get_kite()
    token_lookup = get_instrument_lookup()
    india_vix = fetch_india_vix(kite)

    vix_color = "#00E5A0" if india_vix < 15.0 else "#F5A623"
    regime_label = "TRENDING (VIX < 15)" if india_vix < 15.0 else "PIVOT STRUCTURE (VIX ≥ 15)"

    # ── Sidebar ──
    st.sidebar.markdown("""
    <div style="padding:0.8rem 0 0.4rem; font-family:'Space Grotesk',sans-serif; font-size:0.7rem;
                letter-spacing:0.08em; text-transform:uppercase; color:#4A5A78;">
        Volatility Guard
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div style="
        background:#10141C; border:1px solid #1F2A3C; border-radius:8px;
        padding:0.9rem 1rem; margin-bottom:0.8rem;
    ">
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem;
                    color:#4A5A78; letter-spacing:0.06em; text-transform:uppercase;
                    margin-bottom:4px;">India VIX</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:1.5rem;
                    font-weight:500; color:{vix_color};">{india_vix}</div>
    </div>
    <div style="
        background:#10141C; border:1px solid #1F2A3C; border-radius:8px;
        padding:0.8rem 1rem; margin-bottom:0.8rem;
    ">
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem;
                    color:#4A5A78; letter-spacing:0.04em; text-transform:uppercase;
                    margin-bottom:4px;">Active Ruleset</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:0.82rem;
                    font-weight:600; color:#E8EDF5;">{regime_label}</div>
    </div>
    <div style="
        background:#0D2045; border:1px solid #3B82F6; border-radius:6px;
        padding:0.6rem 0.9rem; font-family:'Space Grotesk',sans-serif;
        font-size:0.75rem; color:#3B82F6;
    ">🔒 R:R Floor &nbsp;·&nbsp; <strong>1.5 : 1</strong></div>
    """, unsafe_allow_html=True)

    if "master_df" not in st.session_state: st.session_state.master_df = None
    if "last_run" not in st.session_state: st.session_state.last_run = None

    current_time = time.time()
    should_scan = st.session_state.master_df is None or (
        st.session_state.last_run and (current_time - st.session_state.last_run) >= 900
    )

    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("⟳  Re-Scan Nifty 100", use_container_width=True):
            should_scan = True
    with c_btn2:
        if st.session_state.last_run:
            ts = datetime.fromtimestamp(st.session_state.last_run).strftime('%H:%M:%S')
            st.markdown(f"""
            <div style="display:flex; align-items:center; height:100%; padding-top:6px;">
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                             color:#4A5A78;">Last sync &nbsp;</span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                             color:#8A9ABB;">{ts}</span>
            </div>
            """, unsafe_allow_html=True)

    if should_scan:
        with st.spinner("Syncing live data from Kite..."):
            results = execute_parallel_scan(meta_df, token_lookup, kite, india_vix)
            if results:
                st.session_state.master_df = pd.DataFrame(results)
                st.session_state.last_run = current_time
                st.rerun()

    if st.session_state.master_df is None: return
    master_df = st.session_state.master_df

    tab1, tab2 = st.tabs(["  📊  Technical Scanner  ", "  🏢  Valuation View  "])

    with tab1:
        active_tf = st.radio(
            "Timeframe",
            ["15 Minute", "1 Day"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown("""<div style="font-family:'Space Grotesk',sans-serif; font-size:0.7rem;
                    color:#4A5A78; letter-spacing:0.06em; text-transform:uppercase;
                    margin-bottom:0.6rem;">Timeframe Layer</div>""", unsafe_allow_html=True)

        suffix = " (15M)" if active_tf == "15 Minute" else " (1D)"
        near_cross_col = f"Within 1% of Cross{suffix}"
        near_cross_df = master_df[master_df[near_cross_col] == "🎯 YES"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Stocks Scanned", len(master_df))
        m2.metric(f"Near Crossover {suffix}", len(near_cross_df))
        action_col = f"Action Signal ({suffix.strip()})"
        active_signals = master_df[master_df[action_col].isin(["🟢 BUY", "🔴 SELL"])] if action_col in master_df.columns else pd.DataFrame()
        m3.metric("Active Signals", len(active_signals))

        st.divider()

        if active_tf == "15 Minute":
            tech_display_cols = [
                "Stock Name", "Action Signal (15M)", "LTP", "Target (15M)", "StopLoss (15M)",
                "Last Cross Value (15M)", "Last Cross Type (15M)", "Within 1% of Cross (15M)", "P / R1 / S1 (15M)"
            ]
        else:
            tech_display_cols = [
                "Stock Name", "Action Signal (1D)", "LTP", "Target (1D)", "StopLoss (1D)",
                "Last Cross Value (1D)", "Last Cross Type (1D)", "Within 1% of Cross (1D)", "P / R1 / S1 (1D)"
            ]

        st.markdown(f"""<div style="font-family:'Space Grotesk',sans-serif; font-size:0.7rem;
                    color:#4A5A78; letter-spacing:0.06em; text-transform:uppercase;
                    margin-bottom:0.5rem;">⚡ Active Signals · {active_tf}</div>""", unsafe_allow_html=True)

        signals_df = master_df[master_df[tech_display_cols[1]].isin(["🟢 BUY", "🔴 SELL"])]
        if not signals_df.empty:
            st.dataframe(signals_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info(f"No assets meet current signal criteria under the {regime_label} ruleset.")

        st.markdown(f"""<div style="font-family:'Space Grotesk',sans-serif; font-size:0.7rem;
                    color:#4A5A78; letter-spacing:0.06em; text-transform:uppercase;
                    margin: 1.2rem 0 0.5rem;">📋 Full Index Overview · {active_tf}</div>""", unsafe_allow_html=True)

        st.dataframe(
            master_df[tech_display_cols].sort_values(by=tech_display_cols[1], ascending=True),
            use_container_width=True, hide_index=True
        )

    with tab2:
        st.markdown("""<div style="font-family:'Space Grotesk',sans-serif; font-size:0.7rem;
                    color:#4A5A78; letter-spacing:0.06em; text-transform:uppercase;
                    margin-bottom:0.8rem;">Valuation & Ownership Filters</div>""", unsafe_allow_html=True)

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected_industry = st.selectbox("Sector", ["All Industries"] + sorted(list(master_df["Industry"].unique())))
        with f_col2:
            selected_tier = st.selectbox("Promoter Stake", ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"])

        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            master_df["Promoter Tier"] = master_df["Promoter Holding (%)"].apply(
                lambda x: "High (>50%)" if x >= 50.0 else ("Medium (30%-50%)" if x >= 30.0 else "Low/Institutional (<30%)")
            )
            bifurcated_df = bifurcated_df[master_df["Promoter Tier"] == selected_tier]

        display_cols = ["Stock Name", "Industry", "Promoter Holding (%)", "Stock PE", "Industry PE", "PB", "ROCE", "LTP"]
        if not bifurcated_df.empty:
            st.dataframe(
                bifurcated_df[display_cols].sort_values(by=["Industry", "Promoter Holding (%)"], ascending=[True, False]),
                use_container_width=True, hide_index=True
            )

if __name__ == "__main__":
    run_integrated_pipeline()
