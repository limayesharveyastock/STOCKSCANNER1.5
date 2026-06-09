import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide", page_title="NIFTY 500 Scanner", page_icon="📊")

# ─── GLOBAL THEME ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
    --bg-base:#0A0C10; --bg-surface:#10141C; --bg-card:#151A24; --bg-elevated:#1C2232;
    --border:#1F2A3C; --border-bright:#2E3D56;
    --text-primary:#E8EDF5; --text-secondary:#8A9ABB; --text-muted:#4A5A78;
    --green:#00E5A0; --green-dim:#003D2B; --red:#FF4D6A; --red-dim:#3D0012;
    --amber:#F5A623; --blue-accent:#3B82F6; --blue-dim:#0D2045;
    --font-ui:'Space Grotesk',sans-serif; --font-mono:'JetBrains Mono',monospace;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
    background-color:var(--bg-base)!important;color:var(--text-primary)!important;
    font-family:var(--font-ui)!important;}
[data-testid="stSidebar"]{background-color:var(--bg-surface)!important;border-right:1px solid var(--border)!important;}
[data-testid="stHeader"]{background-color:var(--bg-base)!important;}
h1{font-family:var(--font-ui)!important;font-weight:700!important;font-size:1.6rem!important;
   letter-spacing:-0.02em!important;color:var(--text-primary)!important;
   border-bottom:1px solid var(--border)!important;margin-bottom:1.2rem!important;}
h2,h3{font-family:var(--font-ui)!important;font-weight:600!important;color:var(--text-secondary)!important;
       font-size:0.85rem!important;letter-spacing:0.08em!important;text-transform:uppercase!important;}
[data-testid="metric-container"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;
    border-radius:8px!important;padding:1rem 1.2rem!important;}
[data-testid="metric-container"] label{font-family:var(--font-ui)!important;font-size:0.72rem!important;
    letter-spacing:0.06em!important;text-transform:uppercase!important;color:var(--text-muted)!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:var(--font-mono)!important;
    font-size:1.6rem!important;font-weight:500!important;color:var(--text-primary)!important;}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:8px!important;overflow:hidden!important;}
[data-testid="stDataFrame"] table{background:var(--bg-card)!important;font-family:var(--font-mono)!important;font-size:0.78rem!important;}
[data-testid="stDataFrame"] th{background:var(--bg-elevated)!important;color:var(--text-secondary)!important;
    font-family:var(--font-ui)!important;font-size:0.7rem!important;letter-spacing:0.05em!important;
    text-transform:uppercase!important;border-bottom:1px solid var(--border-bright)!important;padding:0.6rem 0.8rem!important;}
[data-testid="stDataFrame"] td{color:var(--text-primary)!important;border-bottom:1px solid var(--border)!important;padding:0.5rem 0.8rem!important;}
[data-testid="stDataFrame"] tr:hover td{background:var(--bg-elevated)!important;}
[data-testid="stButton"]>button{background:var(--bg-elevated)!important;color:var(--text-primary)!important;
    border:1px solid var(--border-bright)!important;border-radius:6px!important;
    font-family:var(--font-ui)!important;font-size:0.8rem!important;font-weight:600!important;
    letter-spacing:0.04em!important;transition:all 0.15s ease!important;}
[data-testid="stButton"]>button:hover{background:var(--blue-dim)!important;border-color:var(--blue-accent)!important;color:var(--blue-accent)!important;}
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:var(--bg-surface)!important;border-bottom:1px solid var(--border)!important;}
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;color:var(--text-muted)!important;
    font-family:var(--font-ui)!important;font-size:0.8rem!important;font-weight:600!important;
    letter-spacing:0.04em!important;padding:0.7rem 1.2rem!important;border-bottom:2px solid transparent!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--blue-accent)!important;border-bottom-color:var(--blue-accent)!important;}
[data-testid="stSelectbox"]>div>div{background:var(--bg-card)!important;border:1px solid var(--border)!important;
    border-radius:6px!important;color:var(--text-primary)!important;font-family:var(--font-ui)!important;font-size:0.82rem!important;}
[data-testid="stAlert"]{background:var(--blue-dim)!important;border:1px solid var(--blue-accent)!important;
    border-radius:6px!important;font-family:var(--font-ui)!important;font-size:0.82rem!important;}
hr{border-color:var(--border)!important;margin:1.2rem 0!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:var(--bg-base);}
::-webkit-scrollbar-thumb{background:var(--border-bright);border-radius:3px;}
</style>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:0.2rem 0 1.2rem;">
  <div style="background:linear-gradient(135deg,#1C2E4A,#0D2045);border:1px solid #3B82F6;
              border-radius:8px;padding:6px 10px;font-size:1.3rem;line-height:1;">📊</div>
  <div>
    <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.25rem;
                letter-spacing:-0.02em;color:#E8EDF5;line-height:1.2;">
      NIFTY 500 Stock Scanner & Signal Generator</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#4A5A78;
                letter-spacing:0.06em;text-transform:uppercase;">
      Intraday · Short Swing · Short/Med/Long Term · Live</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── KITE INIT ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_kite():
    kite = KiteConnect(api_key=st.secrets["api_key"], timeout=15)
    kite.set_access_token(st.secrets["access_token"])
    return kite

@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {i['tradingsymbol']: str(i['instrument_token']) for i in instruments}
    except Exception as e:
        st.error(f"Instrument lookup failed: {e}")
        return {}

@st.cache_data(ttl=86400)
def get_nfo_instruments():
    kite = get_kite()
    try:
        return kite.instruments("NFO")
    except Exception:
        return []

def fetch_india_vix(kite):
    try:
        return float(kite.ltp("NSE:INDIA VIX")["NSE:INDIA VIX"]["last_price"])
    except Exception:
        return 14.5

# ─── NIFTY 500 UNIVERSE (representative sample — extend as needed) ─────────────
# Full Nifty 500 has 500 stocks; core set below covers Nifty 100 + key mid/smallcaps
NIFTY500_UNIVERSE = {
    # ── Nifty 50 ──
    "ADANIENT":    {"Industry":"Metals & Mining",         "Promoter":72.6,"PE":45.2,"Ind_PE":24.1,"PB":4.2, "ROCE":12.5},
    "ADANIPORTS":  {"Industry":"Infrastructure / Services","Promoter":65.3,"PE":33.1,"Ind_PE":28.5,"PB":3.9, "ROCE":14.8},
    "APOLLOHOSP":  {"Industry":"Healthcare",              "Promoter":29.3,"PE":78.4,"Ind_PE":38.2,"PB":9.1, "ROCE":16.2},
    "ASIANPAINT":  {"Industry":"Consumer Durables",       "Promoter":52.6,"PE":55.4,"Ind_PE":51.2,"PB":14.2,"ROCE":34.1},
    "AXISBANK":    {"Industry":"Financial Services",      "Promoter":0.0, "PE":14.1,"Ind_PE":15.2,"PB":2.1, "ROCE":11.2},
    "BAJAJ-AUTO":  {"Industry":"Automobile",              "Promoter":55.0,"PE":31.2,"Ind_PE":26.4,"PB":8.4, "ROCE":30.5},
    "BAJFINANCE":  {"Industry":"Financial Services",      "Promoter":54.7,"PE":28.3,"Ind_PE":22.1,"PB":5.8, "ROCE":17.4},
    "BAJAJFINSV":  {"Industry":"Financial Services",      "Promoter":60.7,"PE":33.4,"Ind_PE":22.1,"PB":4.1, "ROCE":14.9},
    "BEL":         {"Industry":"Capital Goods",           "Promoter":51.1,"PE":42.6,"Ind_PE":35.4,"PB":7.8, "ROCE":26.3},
    "BHARTIARTL":  {"Industry":"Telecommunication",       "Promoter":53.1,"PE":52.1,"Ind_PE":41.3,"PB":8.9, "ROCE":18.2},
    "BPCL":        {"Industry":"Oil & Gas",               "Promoter":53.0,"PE":11.4,"Ind_PE":12.8,"PB":1.7, "ROCE":22.1},
    "BRITANNIA":   {"Industry":"FMCG",                   "Promoter":50.5,"PE":54.3,"Ind_PE":44.2,"PB":28.1,"ROCE":48.6},
    "CIPLA":       {"Industry":"Healthcare",              "Promoter":33.4,"PE":29.6,"Ind_PE":31.4,"PB":4.3, "ROCE":21.3},
    "COALINDIA":   {"Industry":"Oil & Gas",               "Promoter":63.1,"PE":9.2, "Ind_PE":12.8,"PB":3.4, "ROCE":54.2},
    "DRREDDY":     {"Industry":"Healthcare",              "Promoter":26.7,"PE":18.9,"Ind_PE":31.4,"PB":3.1, "ROCE":24.5},
    "EICHERMOT":   {"Industry":"Automobile",              "Promoter":49.2,"PE":29.1,"Ind_PE":26.4,"PB":7.2, "ROCE":27.8},
    "GRASIM":      {"Industry":"Construction Materials",  "Promoter":42.7,"PE":44.1,"Ind_PE":32.1,"PB":1.9, "ROCE":9.4},
    "HCLTECH":     {"Industry":"Information Technology",  "Promoter":60.8,"PE":25.4,"Ind_PE":28.2,"PB":6.1, "ROCE":28.9},
    "HDFCBANK":    {"Industry":"Financial Services",      "Promoter":0.0, "PE":18.2,"Ind_PE":15.2,"PB":2.6, "ROCE":12.1},
    "HDFCLIFE":    {"Industry":"Financial Services",      "Promoter":50.4,"PE":61.2,"Ind_PE":55.4,"PB":4.8, "ROCE":14.2},
    "HINDALCO":    {"Industry":"Metals & Mining",         "Promoter":34.6,"PE":16.3,"Ind_PE":18.4,"PB":1.8, "ROCE":13.1},
    "HINDUNILVR":  {"Industry":"FMCG",                   "Promoter":61.9,"PE":56.2,"Ind_PE":44.2,"PB":11.4,"ROCE":39.5},
    "ICICIBANK":   {"Industry":"Financial Services",      "Promoter":0.0, "PE":17.4,"Ind_PE":15.2,"PB":3.1, "ROCE":13.4},
    "INDUSINDBK":  {"Industry":"Financial Services",      "Promoter":16.5,"PE":13.2,"Ind_PE":15.2,"PB":1.8, "ROCE":11.7},
    "INFY":        {"Industry":"Information Technology",  "Promoter":14.8,"PE":24.1,"Ind_PE":28.2,"PB":7.4, "ROCE":37.2},
    "INDIGO":      {"Industry":"Infrastructure / Services","Promoter":57.3,"PE":21.4,"Ind_PE":25.1,"PB":5.2, "ROCE":22.4},
    "ITC":         {"Industry":"FMCG",                   "Promoter":0.0, "PE":26.4,"Ind_PE":44.2,"PB":7.9, "ROCE":38.7},
    "JSWSTEEL":    {"Industry":"Metals & Mining",         "Promoter":44.8,"PE":27.2,"Ind_PE":18.4,"PB":3.2, "ROCE":14.1},
    "JIOFIN":      {"Industry":"Financial Services",      "Promoter":47.1,"PE":120.5,"Ind_PE":22.1,"PB":2.1,"ROCE":6.2},
    "KOTAKBANK":   {"Industry":"Financial Services",      "Promoter":25.9,"PE":19.1,"Ind_PE":15.2,"PB":2.9, "ROCE":12.8},
    "LT":          {"Industry":"Construction",            "Promoter":0.0, "PE":36.4,"Ind_PE":31.2,"PB":4.8, "ROCE":15.1},
    "M&M":         {"Industry":"Automobile",              "Promoter":19.3,"PE":28.4,"Ind_PE":26.4,"PB":4.9, "ROCE":19.2},
    "MARUTI":      {"Industry":"Automobile",              "Promoter":58.2,"PE":27.5,"Ind_PE":26.4,"PB":5.1, "ROCE":21.4},
    "MAXHEALTH":   {"Industry":"Healthcare",              "Promoter":23.1,"PE":68.2,"Ind_PE":38.2,"PB":8.4, "ROCE":15.5},
    "NESTLEIND":   {"Industry":"FMCG",                   "Promoter":62.8,"PE":74.2,"Ind_PE":44.2,"PB":21.4,"ROCE":58.1},
    "NTPC":        {"Industry":"Power",                   "Promoter":51.1,"PE":17.5,"Ind_PE":19.4,"PB":2.4, "ROCE":11.9},
    "ONGC":        {"Industry":"Oil & Gas",               "Promoter":58.9,"PE":8.1, "Ind_PE":12.8,"PB":1.1, "ROCE":14.5},
    "POWERGRID":   {"Industry":"Power",                   "Promoter":51.3,"PE":16.2,"Ind_PE":19.4,"PB":2.9, "ROCE":12.4},
    "RELIANCE":    {"Industry":"Oil & Gas",               "Promoter":50.3,"PE":26.1,"Ind_PE":12.8,"PB":2.4, "ROCE":10.2},
    "SBILIFE":     {"Industry":"Financial Services",      "Promoter":55.4,"PE":78.1,"Ind_PE":55.4,"PB":9.5, "ROCE":13.1},
    "SBIN":        {"Industry":"Financial Services",      "Promoter":57.5,"PE":10.4,"Ind_PE":15.2,"PB":1.6, "ROCE":11.8},
    "SHRIRAMFIN":  {"Industry":"Financial Services",      "Promoter":25.4,"PE":14.8,"Ind_PE":22.1,"PB":2.2, "ROCE":15.4},
    "SUNPHARMA":   {"Industry":"Healthcare",              "Promoter":54.5,"PE":36.2,"Ind_PE":31.4,"PB":4.9, "ROCE":17.2},
    "TATACONSUM":  {"Industry":"FMCG",                   "Promoter":34.4,"PE":64.1,"Ind_PE":44.2,"PB":4.1, "ROCE":9.8},
    "TATAMOTORS":  {"Industry":"Automobile",              "Promoter":46.4,"PE":11.5,"Ind_PE":26.4,"PB":3.2, "ROCE":20.1},
    "TATASTEEL":   {"Industry":"Metals & Mining",         "Promoter":33.2,"PE":38.4,"Ind_PE":18.4,"PB":1.7, "ROCE":10.5},
    "TCS":         {"Industry":"Information Technology",  "Promoter":72.4,"PE":29.5,"Ind_PE":28.2,"PB":12.8,"ROCE":51.4},
    "TECHM":       {"Industry":"Information Technology",  "Promoter":35.1,"PE":48.2,"Ind_PE":28.2,"PB":3.8, "ROCE":15.9},
    "TITAN":       {"Industry":"Consumer Durables",       "Promoter":52.9,"PE":82.1,"Ind_PE":51.2,"PB":19.4,"ROCE":25.1},
    "TRENT":       {"Industry":"Retail",                  "Promoter":37.0,"PE":145.2,"Ind_PE":68.4,"PB":28.4,"ROCE":24.3},
    "ULTRACEMCO":  {"Industry":"Construction Materials",  "Promoter":60.0,"PE":41.2,"Ind_PE":32.1,"PB":4.7, "ROCE":13.8},
    "UPL":         {"Industry":"Chemicals",               "Promoter":32.4,"PE":22.1,"Ind_PE":19.5,"PB":1.5, "ROCE":11.1},
    "WIPRO":       {"Industry":"Information Technology",  "Promoter":72.9,"PE":23.4,"Ind_PE":28.2,"PB":3.4, "ROCE":21.2},
    # ── Nifty 100 additions ──
    "ABB":         {"Industry":"Capital Goods",           "Promoter":75.0,"PE":62.4,"Ind_PE":35.4,"PB":14.2,"ROCE":28.6},
    "ADANIGREEN":  {"Industry":"Power",                   "Promoter":56.3,"PE":185.2,"Ind_PE":19.4,"PB":22.1,"ROCE":8.4},
    "ADANIPOWER":  {"Industry":"Power",                   "Promoter":74.2,"PE":14.6,"Ind_PE":19.4,"PB":4.8, "ROCE":22.1},
    "AMBUJACEM":   {"Industry":"Construction Materials",  "Promoter":63.2,"PE":38.1,"Ind_PE":32.1,"PB":3.4, "ROCE":10.2},
    "ATGL":        {"Industry":"Oil & Gas",               "Promoter":74.8,"PE":68.4,"Ind_PE":12.8,"PB":8.9, "ROCE":18.4},
    "AUROPHARMA":  {"Industry":"Healthcare",              "Promoter":51.8,"PE":22.4,"Ind_PE":31.4,"PB":3.2, "ROCE":19.5},
    "BAJAJHLDNG":  {"Industry":"Financial Services",      "Promoter":57.2,"PE":18.4,"Ind_PE":22.1,"PB":2.8, "ROCE":14.1},
    "BANKBARODA":  {"Industry":"Financial Services",      "Promoter":63.9,"PE":6.8, "Ind_PE":15.2,"PB":1.1, "ROCE":9.8},
    "BERGEPAINT":  {"Industry":"Consumer Durables",       "Promoter":74.9,"PE":52.1,"Ind_PE":51.2,"PB":12.4,"ROCE":28.9},
    "BOSCHLTD":    {"Industry":"Automobile",              "Promoter":70.5,"PE":38.2,"Ind_PE":26.4,"PB":6.8, "ROCE":22.4},
    "CANBK":       {"Industry":"Financial Services",      "Promoter":62.9,"PE":7.2, "Ind_PE":15.2,"PB":1.0, "ROCE":9.1},
    "CHOLAFIN":    {"Industry":"Financial Services",      "Promoter":51.4,"PE":28.6,"Ind_PE":22.1,"PB":4.8, "ROCE":16.2},
    "COLPAL":      {"Industry":"FMCG",                   "Promoter":51.0,"PE":48.6,"Ind_PE":44.2,"PB":18.4,"ROCE":52.1},
    "CUMMINSIND":  {"Industry":"Capital Goods",           "Promoter":51.0,"PE":44.2,"Ind_PE":35.4,"PB":9.8, "ROCE":30.1},
    "DABUR":       {"Industry":"FMCG",                   "Promoter":67.9,"PE":46.2,"Ind_PE":44.2,"PB":9.6, "ROCE":24.8},
    "DLF":         {"Industry":"Real Estate",             "Promoter":74.9,"PE":52.4,"Ind_PE":38.6,"PB":4.2, "ROCE":9.8},
    "FEDERALBNK":  {"Industry":"Financial Services",      "Promoter":0.0, "PE":10.4,"Ind_PE":15.2,"PB":1.4, "ROCE":11.2},
    "GAIL":        {"Industry":"Oil & Gas",               "Promoter":51.9,"PE":12.4,"Ind_PE":12.8,"PB":1.6, "ROCE":14.8},
    "GODREJCP":    {"Industry":"FMCG",                   "Promoter":63.2,"PE":42.6,"Ind_PE":44.2,"PB":8.4, "ROCE":21.4},
    "GODREJPROP":  {"Industry":"Real Estate",             "Promoter":58.5,"PE":68.4,"Ind_PE":38.6,"PB":5.8, "ROCE":8.6},
    "HAL":         {"Industry":"Capital Goods",           "Promoter":71.6,"PE":38.4,"Ind_PE":35.4,"PB":9.2, "ROCE":28.4},
    "HAVELLS":     {"Industry":"Capital Goods",           "Promoter":59.6,"PE":64.2,"Ind_PE":35.4,"PB":12.8,"ROCE":24.6},
    "HEROMOTOCO":  {"Industry":"Automobile",              "Promoter":34.6,"PE":20.4,"Ind_PE":26.4,"PB":5.2, "ROCE":32.8},
    "ICICIPRU":    {"Industry":"Financial Services",      "Promoter":74.0,"PE":72.4,"Ind_PE":55.4,"PB":8.2, "ROCE":12.4},
    "IDFCFIRSTB":  {"Industry":"Financial Services",      "Promoter":36.6,"PE":22.4,"Ind_PE":15.2,"PB":1.6, "ROCE":9.8},
    "IGL":         {"Industry":"Oil & Gas",               "Promoter":45.0,"PE":22.8,"Ind_PE":12.8,"PB":4.2, "ROCE":21.4},
    "IOC":         {"Industry":"Oil & Gas",               "Promoter":51.5,"PE":6.8, "Ind_PE":12.8,"PB":1.0, "ROCE":18.2},
    "IRCTC":       {"Industry":"Infrastructure / Services","Promoter":67.4,"PE":48.6,"Ind_PE":25.1,"PB":14.8,"ROCE":38.4},
    "IRFC":        {"Industry":"Financial Services",      "Promoter":86.4,"PE":28.4,"Ind_PE":22.1,"PB":4.2, "ROCE":6.8},
    "LTIM":        {"Industry":"Information Technology",  "Promoter":74.3,"PE":34.6,"Ind_PE":28.2,"PB":8.4, "ROCE":32.4},
    "LTTS":        {"Industry":"Information Technology",  "Promoter":74.2,"PE":32.8,"Ind_PE":28.2,"PB":6.8, "ROCE":28.6},
    "LUPIN":       {"Industry":"Healthcare",              "Promoter":47.0,"PE":28.4,"Ind_PE":31.4,"PB":4.6, "ROCE":18.4},
    "MARICO":      {"Industry":"FMCG",                   "Promoter":59.4,"PE":44.8,"Ind_PE":44.2,"PB":14.6,"ROCE":42.8},
    "MCDOWELL-N":  {"Industry":"FMCG",                   "Promoter":56.0,"PE":62.4,"Ind_PE":44.2,"PB":8.4, "ROCE":22.6},
    "MOTHERSON":   {"Industry":"Automobile",              "Promoter":58.3,"PE":38.6,"Ind_PE":26.4,"PB":4.8, "ROCE":14.2},
    "MPHASIS":     {"Industry":"Information Technology",  "Promoter":55.6,"PE":28.4,"Ind_PE":28.2,"PB":5.8, "ROCE":24.6},
    "MRF":         {"Industry":"Automobile",              "Promoter":27.8,"PE":24.6,"Ind_PE":26.4,"PB":3.4, "ROCE":16.8},
    "MUTHOOTFIN":  {"Industry":"Financial Services",      "Promoter":73.4,"PE":18.4,"Ind_PE":22.1,"PB":3.6, "ROCE":18.2},
    "NMDC":        {"Industry":"Metals & Mining",         "Promoter":60.8,"PE":9.4, "Ind_PE":18.4,"PB":2.2, "ROCE":28.4},
    "NYKAA":       {"Industry":"Retail",                  "Promoter":52.6,"PE":148.6,"Ind_PE":68.4,"PB":18.4,"ROCE":8.6},
    "OBEROIRLTY":  {"Industry":"Real Estate",             "Promoter":67.7,"PE":28.6,"Ind_PE":38.6,"PB":4.8, "ROCE":18.4},
    "OFSS":        {"Industry":"Information Technology",  "Promoter":72.8,"PE":32.4,"Ind_PE":28.2,"PB":8.6, "ROCE":38.4},
    "PAGEIND":     {"Industry":"Consumer Durables",       "Promoter":59.0,"PE":64.8,"Ind_PE":51.2,"PB":28.4,"ROCE":58.6},
    "PAYTM":       {"Industry":"Financial Services",      "Promoter":19.4,"PE":0.0, "Ind_PE":22.1,"PB":2.8, "ROCE":-4.2},
    "PERSISTENT":  {"Industry":"Information Technology",  "Promoter":31.1,"PE":58.4,"Ind_PE":28.2,"PB":12.4,"ROCE":28.6},
    "PETRONET":    {"Industry":"Oil & Gas",               "Promoter":50.0,"PE":12.8,"Ind_PE":12.8,"PB":2.8, "ROCE":24.6},
    "PFC":         {"Industry":"Financial Services",      "Promoter":55.9,"PE":8.6, "Ind_PE":22.1,"PB":1.6, "ROCE":8.2},
    "PIDILITIND":  {"Industry":"Chemicals",               "Promoter":70.7,"PE":72.4,"Ind_PE":19.5,"PB":18.4,"ROCE":32.4},
    "PIIND":       {"Industry":"Chemicals",               "Promoter":52.0,"PE":28.6,"Ind_PE":19.5,"PB":4.8, "ROCE":18.6},
    "PNB":         {"Industry":"Financial Services",      "Promoter":73.2,"PE":8.4, "Ind_PE":15.2,"PB":0.9, "ROCE":8.6},
    "POLYCAB":     {"Industry":"Capital Goods",           "Promoter":67.7,"PE":42.6,"Ind_PE":35.4,"PB":8.4, "ROCE":24.8},
    "RECLTD":      {"Industry":"Financial Services",      "Promoter":52.6,"PE":9.2, "Ind_PE":22.1,"PB":1.8, "ROCE":8.6},
    "SIEMENS":     {"Industry":"Capital Goods",           "Promoter":75.0,"PE":72.8,"Ind_PE":35.4,"PB":14.8,"ROCE":22.4},
    "SRF":         {"Industry":"Chemicals",               "Promoter":50.6,"PE":38.4,"Ind_PE":19.5,"PB":5.8, "ROCE":14.8},
    "TORNTPHARM":  {"Industry":"Healthcare",              "Promoter":71.3,"PE":38.6,"Ind_PE":31.4,"PB":8.4, "ROCE":22.4},
    "TORNTPOWER":  {"Industry":"Power",                   "Promoter":72.8,"PE":28.4,"Ind_PE":19.4,"PB":4.8, "ROCE":14.6},
    "TVSMOTOR":    {"Industry":"Automobile",              "Promoter":57.4,"PE":42.8,"Ind_PE":26.4,"PB":12.4,"ROCE":26.8},
    "UNIONBANK":   {"Industry":"Financial Services",      "Promoter":74.8,"PE":6.8, "Ind_PE":15.2,"PB":0.9, "ROCE":8.8},
    "VEDL":        {"Industry":"Metals & Mining",         "Promoter":56.4,"PE":12.4,"Ind_PE":18.4,"PB":2.8, "ROCE":18.4},
    "VOLTAS":      {"Industry":"Capital Goods",           "Promoter":30.3,"PE":68.4,"Ind_PE":35.4,"PB":8.6, "ROCE":14.2},
    "ZOMATO":      {"Industry":"Infrastructure / Services","Promoter":0.0, "PE":248.6,"Ind_PE":25.1,"PB":8.4,"ROCE":4.2},
    "ZYDUSLIFE":   {"Industry":"Healthcare",              "Promoter":74.9,"PE":28.4,"Ind_PE":31.4,"PB":4.8, "ROCE":18.6},
    # ── Nifty Midcap / Nifty 500 additions ──
    "ABCAPITAL":   {"Industry":"Financial Services",      "Promoter":69.2,"PE":18.4,"Ind_PE":22.1,"PB":2.4, "ROCE":12.4},
    "ABFRL":       {"Industry":"Retail",                  "Promoter":52.8,"PE":0.0, "Ind_PE":68.4,"PB":8.2, "ROCE":6.4},
    "ALKEM":       {"Industry":"Healthcare",              "Promoter":57.6,"PE":28.4,"Ind_PE":31.4,"PB":4.8, "ROCE":22.4},
    "APLLTD":      {"Industry":"Healthcare",              "Promoter":66.4,"PE":18.6,"Ind_PE":31.4,"PB":4.2, "ROCE":24.8},
    "ASTRAL":      {"Industry":"Construction Materials",  "Promoter":54.6,"PE":68.4,"Ind_PE":32.1,"PB":14.8,"ROCE":22.6},
    "ATUL":        {"Industry":"Chemicals",               "Promoter":45.2,"PE":38.4,"Ind_PE":19.5,"PB":5.4, "ROCE":14.8},
    "AUBANK":      {"Industry":"Financial Services",      "Promoter":28.8,"PE":28.6,"Ind_PE":15.2,"PB":4.2, "ROCE":12.4},
    "BALKRISIND":  {"Industry":"Automobile",              "Promoter":58.3,"PE":28.4,"Ind_PE":26.4,"PB":5.8, "ROCE":18.4},
    "BANDHANBNK":  {"Industry":"Financial Services",      "Promoter":39.9,"PE":18.4,"Ind_PE":15.2,"PB":2.4, "ROCE":10.8},
    "BATAINDIA":   {"Industry":"Consumer Durables",       "Promoter":52.9,"PE":38.4,"Ind_PE":51.2,"PB":6.8, "ROCE":18.4},
    "BHARATFORG":  {"Industry":"Automobile",              "Promoter":45.3,"PE":32.4,"Ind_PE":26.4,"PB":6.4, "ROCE":14.8},
    "BHEL":        {"Industry":"Capital Goods",           "Promoter":63.2,"PE":0.0, "Ind_PE":35.4,"PB":3.2, "ROCE":4.8},
    "BIOCON":      {"Industry":"Healthcare",              "Promoter":60.9,"PE":48.6,"Ind_PE":31.4,"PB":3.4, "ROCE":8.4},
    "BSE":         {"Industry":"Financial Services",      "Promoter":0.0, "PE":38.4,"Ind_PE":22.1,"PB":8.4, "ROCE":22.4},
    "CAMS":        {"Industry":"Financial Services",      "Promoter":68.3,"PE":38.4,"Ind_PE":22.1,"PB":14.8,"ROCE":32.4},
    "CANFINHOME":  {"Industry":"Financial Services",      "Promoter":29.9,"PE":12.4,"Ind_PE":22.1,"PB":2.4, "ROCE":14.8},
    "CDSL":        {"Industry":"Financial Services",      "Promoter":0.0, "PE":48.6,"Ind_PE":22.1,"PB":18.4,"ROCE":38.4},
    "CENTURYTEX":  {"Industry":"Construction Materials",  "Promoter":44.6,"PE":18.4,"Ind_PE":32.1,"PB":1.8, "ROCE":12.4},
    "COFORGE":     {"Industry":"Information Technology",  "Promoter":28.0,"PE":42.4,"Ind_PE":28.2,"PB":8.4, "ROCE":24.6},
    "CONCOR":      {"Industry":"Infrastructure / Services","Promoter":54.8,"PE":28.4,"Ind_PE":25.1,"PB":4.8, "ROCE":18.4},
    "CROMPTON":    {"Industry":"Capital Goods",           "Promoter":0.0, "PE":38.4,"Ind_PE":35.4,"PB":8.4, "ROCE":18.4},
    "DALBHARAT":   {"Industry":"Construction Materials",  "Promoter":75.0,"PE":22.4,"Ind_PE":32.1,"PB":3.8, "ROCE":14.8},
    "DEEPAKNTR":   {"Industry":"Chemicals",               "Promoter":45.1,"PE":22.4,"Ind_PE":19.5,"PB":4.8, "ROCE":14.8},
    "DIXON":       {"Industry":"Capital Goods",           "Promoter":34.0,"PE":88.4,"Ind_PE":35.4,"PB":18.4,"ROCE":28.4},
    "ESCORTS":     {"Industry":"Automobile",              "Promoter":44.8,"PE":22.4,"Ind_PE":26.4,"PB":3.8, "ROCE":14.8},
    "EXIDEIND":    {"Industry":"Automobile",              "Promoter":45.8,"PE":28.4,"Ind_PE":26.4,"PB":2.8, "ROCE":12.4},
    "GLENMARK":    {"Industry":"Healthcare",              "Promoter":46.7,"PE":18.4,"Ind_PE":31.4,"PB":2.8, "ROCE":12.4},
    "GMRINFRA":    {"Industry":"Infrastructure / Services","Promoter":59.3,"PE":0.0, "Ind_PE":25.1,"PB":4.8, "ROCE":4.2},
    "GNFC":        {"Industry":"Chemicals",               "Promoter":46.6,"PE":8.4, "Ind_PE":19.5,"PB":1.4, "ROCE":18.4},
    "GRANULES":    {"Industry":"Healthcare",              "Promoter":42.5,"PE":18.4,"Ind_PE":31.4,"PB":3.4, "ROCE":18.4},
    "GSPL":        {"Industry":"Oil & Gas",               "Promoter":37.6,"PE":12.4,"Ind_PE":12.8,"PB":2.4, "ROCE":18.4},
    "HAPPSTMNDS":  {"Industry":"Information Technology",  "Promoter":53.4,"PE":28.4,"Ind_PE":28.2,"PB":5.8, "ROCE":22.4},
    "HFCL":        {"Industry":"Telecommunication",       "Promoter":40.0,"PE":18.4,"Ind_PE":41.3,"PB":2.8, "ROCE":12.4},
    "HUDCO":       {"Industry":"Financial Services",      "Promoter":81.8,"PE":14.8,"Ind_PE":22.1,"PB":2.4, "ROCE":8.4},
    "IBREALEST":   {"Industry":"Real Estate",             "Promoter":42.7,"PE":0.0, "Ind_PE":38.6,"PB":3.4, "ROCE":4.8},
    "IDFC":        {"Industry":"Financial Services",      "Promoter":0.0, "PE":14.8,"Ind_PE":22.1,"PB":1.4, "ROCE":8.4},
    "INDHOTEL":    {"Industry":"Consumer Durables",       "Promoter":38.1,"PE":48.4,"Ind_PE":51.2,"PB":8.4, "ROCE":14.8},
    "INDIAMART":   {"Industry":"Information Technology",  "Promoter":48.8,"PE":38.4,"Ind_PE":28.2,"PB":8.4, "ROCE":22.4},
    "INDUSTOWER":  {"Industry":"Telecommunication",       "Promoter":69.0,"PE":12.4,"Ind_PE":41.3,"PB":2.8, "ROCE":14.8},
    "INTELLECT":   {"Industry":"Information Technology",  "Promoter":39.6,"PE":28.4,"Ind_PE":28.2,"PB":4.8, "ROCE":14.8},
    "IPCALAB":     {"Industry":"Healthcare",              "Promoter":26.6,"PE":28.4,"Ind_PE":31.4,"PB":4.8, "ROCE":18.4},
    "JKCEMENT":    {"Industry":"Construction Materials",  "Promoter":67.5,"PE":22.4,"Ind_PE":32.1,"PB":3.8, "ROCE":14.8},
    "JUBLFOOD":    {"Industry":"FMCG",                   "Promoter":41.9,"PE":68.4,"Ind_PE":44.2,"PB":18.4,"ROCE":22.4},
    "KALYANKJIL":  {"Industry":"Consumer Durables",       "Promoter":60.6,"PE":38.4,"Ind_PE":51.2,"PB":8.4, "ROCE":18.4},
    "KANSAINER":   {"Industry":"Consumer Durables",       "Promoter":74.9,"PE":38.4,"Ind_PE":51.2,"PB":8.4, "ROCE":24.8},
    "KEI":         {"Industry":"Capital Goods",           "Promoter":28.0,"PE":38.4,"Ind_PE":35.4,"PB":8.4, "ROCE":24.8},
    "KMARTIND":    {"Industry":"Retail",                  "Promoter":0.0, "PE":0.0, "Ind_PE":68.4,"PB":0.0, "ROCE":0.0},
    "KPITTECH":    {"Industry":"Information Technology",  "Promoter":39.0,"PE":48.4,"Ind_PE":28.2,"PB":12.4,"ROCE":24.8},
    "LAURUSLABS":  {"Industry":"Healthcare",              "Promoter":27.6,"PE":28.4,"Ind_PE":31.4,"PB":4.8, "ROCE":14.8},
    "LICHSGFIN":   {"Industry":"Financial Services",      "Promoter":40.3,"PE":8.4, "Ind_PE":22.1,"PB":1.4, "ROCE":12.4},
    "LICI":        {"Industry":"Financial Services",      "Promoter":96.5,"PE":14.8,"Ind_PE":55.4,"PB":4.8, "ROCE":12.4},
    "LINDEINDIA":  {"Industry":"Chemicals",               "Promoter":75.0,"PE":38.4,"Ind_PE":19.5,"PB":8.4, "ROCE":18.4},
    "MANAPPURAM":  {"Industry":"Financial Services",      "Promoter":35.1,"PE":8.4, "Ind_PE":22.1,"PB":1.8, "ROCE":18.4},
    "MCX":         {"Industry":"Financial Services",      "Promoter":0.0, "PE":38.4,"Ind_PE":22.1,"PB":8.4, "ROCE":22.4},
    "METROPOLIS":  {"Industry":"Healthcare",              "Promoter":50.0,"PE":48.4,"Ind_PE":31.4,"PB":8.4, "ROCE":22.4},
    "MINDTREE":    {"Industry":"Information Technology",  "Promoter":74.3,"PE":28.4,"Ind_PE":28.2,"PB":5.8, "ROCE":24.8},
    "NATCOPHARM":  {"Industry":"Healthcare",              "Promoter":52.1,"PE":18.4,"Ind_PE":31.4,"PB":3.4, "ROCE":18.4},
    "NAVINFLUOR":  {"Industry":"Chemicals",               "Promoter":56.0,"PE":28.4,"Ind_PE":19.5,"PB":5.4, "ROCE":18.4},
    "NIACL":       {"Industry":"Financial Services",      "Promoter":85.4,"PE":14.8,"Ind_PE":55.4,"PB":1.4, "ROCE":8.4},
    "NLCINDIA":    {"Industry":"Power",                   "Promoter":72.2,"PE":12.4,"Ind_PE":19.4,"PB":1.8, "ROCE":12.4},
    "NUVOCO":      {"Industry":"Construction Materials",  "Promoter":57.3,"PE":0.0, "Ind_PE":32.1,"PB":1.8, "ROCE":6.4},
    "OIL":         {"Industry":"Oil & Gas",               "Promoter":56.7,"PE":8.4, "Ind_PE":12.8,"PB":0.8, "ROCE":12.4},
    "OLECTRA":     {"Industry":"Automobile",              "Promoter":55.0,"PE":48.4,"Ind_PE":26.4,"PB":8.4, "ROCE":12.4},
    "PHOENIXLTD":  {"Industry":"Real Estate",             "Promoter":50.1,"PE":38.4,"Ind_PE":38.6,"PB":4.8, "ROCE":12.4},
    "POLYMED":     {"Industry":"Healthcare",              "Promoter":59.4,"PE":38.4,"Ind_PE":31.4,"PB":8.4, "ROCE":22.4},
    "PRAJIND":     {"Industry":"Capital Goods",           "Promoter":34.2,"PE":28.4,"Ind_PE":35.4,"PB":4.8, "ROCE":22.4},
    "PRESTIGE":    {"Industry":"Real Estate",             "Promoter":68.1,"PE":28.4,"Ind_PE":38.6,"PB":4.2, "ROCE":12.4},
    "PRINCEPIPES": {"Industry":"Construction Materials",  "Promoter":70.2,"PE":28.4,"Ind_PE":32.1,"PB":3.8, "ROCE":14.8},
    "PVRINOX":     {"Industry":"Consumer Durables",       "Promoter":15.7,"PE":0.0, "Ind_PE":51.2,"PB":3.4, "ROCE":4.8},
    "RAJESHEXPO":  {"Industry":"Consumer Durables",       "Promoter":68.4,"PE":18.4,"Ind_PE":51.2,"PB":2.8, "ROCE":18.4},
    "RAMCOCEM":    {"Industry":"Construction Materials",  "Promoter":42.5,"PE":28.4,"Ind_PE":32.1,"PB":3.4, "ROCE":12.4},
    "RITES":       {"Industry":"Infrastructure / Services","Promoter":72.2,"PE":22.4,"Ind_PE":25.1,"PB":4.8, "ROCE":24.8},
    "ROUTE":       {"Industry":"Telecommunication",       "Promoter":60.8,"PE":38.4,"Ind_PE":41.3,"PB":8.4, "ROCE":18.4},
    "SAIL":        {"Industry":"Metals & Mining",         "Promoter":65.0,"PE":14.8,"Ind_PE":18.4,"PB":0.8, "ROCE":8.4},
    "SCHAEFFLER":  {"Industry":"Automobile",              "Promoter":74.9,"PE":38.4,"Ind_PE":26.4,"PB":6.8, "ROCE":24.8},
    "SHYAMMETL":   {"Industry":"Metals & Mining",         "Promoter":75.0,"PE":12.4,"Ind_PE":18.4,"PB":2.4, "ROCE":18.4},
    "SOLARINDS":   {"Industry":"Capital Goods",           "Promoter":73.3,"PE":68.4,"Ind_PE":35.4,"PB":14.8,"ROCE":28.4},
    "SONACOMS":    {"Industry":"Automobile",              "Promoter":36.5,"PE":38.4,"Ind_PE":26.4,"PB":8.4, "ROCE":22.4},
    "STAR":        {"Industry":"Consumer Durables",       "Promoter":62.9,"PE":0.0, "Ind_PE":51.2,"PB":4.8, "ROCE":4.8},
    "STARHEALTH":  {"Industry":"Financial Services",      "Promoter":60.9,"PE":38.4,"Ind_PE":55.4,"PB":4.8, "ROCE":8.4},
    "SUNDARMFIN":  {"Industry":"Financial Services",      "Promoter":36.2,"PE":22.4,"Ind_PE":22.1,"PB":4.8, "ROCE":18.4},
    "SUNDRMFAST":  {"Industry":"Automobile",              "Promoter":50.5,"PE":28.4,"Ind_PE":26.4,"PB":6.8, "ROCE":22.4},
    "SUNTV":       {"Industry":"Consumer Durables",       "Promoter":75.0,"PE":18.4,"Ind_PE":51.2,"PB":4.8, "ROCE":28.4},
    "SUPREMEIND":  {"Industry":"Construction Materials",  "Promoter":47.8,"PE":38.4,"Ind_PE":32.1,"PB":8.4, "ROCE":18.4},
    "SYNGENE":     {"Industry":"Healthcare",              "Promoter":54.7,"PE":48.4,"Ind_PE":31.4,"PB":8.4, "ROCE":18.4},
    "TANLA":       {"Industry":"Information Technology",  "Promoter":44.8,"PE":18.4,"Ind_PE":28.2,"PB":4.8, "ROCE":28.4},
    "TASTYBITE":   {"Industry":"FMCG",                   "Promoter":72.9,"PE":38.4,"Ind_PE":44.2,"PB":8.4, "ROCE":22.4},
    "TATACHEM":    {"Industry":"Chemicals",               "Promoter":37.0,"PE":22.4,"Ind_PE":19.5,"PB":1.8, "ROCE":8.4},
    "TATACOMM":    {"Industry":"Telecommunication",       "Promoter":58.9,"PE":28.4,"Ind_PE":41.3,"PB":8.4, "ROCE":14.8},
    "TATAELXSI":   {"Industry":"Information Technology",  "Promoter":44.6,"PE":38.4,"Ind_PE":28.2,"PB":12.4,"ROCE":38.4},
    "TATAINVEST":  {"Industry":"Financial Services",      "Promoter":67.6,"PE":12.4,"Ind_PE":22.1,"PB":0.8, "ROCE":8.4},
    "TATAPOWER":   {"Industry":"Power",                   "Promoter":46.9,"PE":28.4,"Ind_PE":19.4,"PB":4.8, "ROCE":8.4},
    "TEAMLEASE":   {"Industry":"Infrastructure / Services","Promoter":43.4,"PE":38.4,"Ind_PE":25.1,"PB":8.4, "ROCE":14.8},
    "THERMAX":     {"Industry":"Capital Goods",           "Promoter":62.0,"PE":48.4,"Ind_PE":35.4,"PB":8.4, "ROCE":18.4},
    "TIINDIA":     {"Industry":"Automobile",              "Promoter":74.9,"PE":38.4,"Ind_PE":26.4,"PB":8.4, "ROCE":22.4},
    "TRIDENT":     {"Industry":"Construction Materials",  "Promoter":73.0,"PE":18.4,"Ind_PE":32.1,"PB":2.8, "ROCE":14.8},
    "TRITURBINE":  {"Industry":"Capital Goods",           "Promoter":58.0,"PE":28.4,"Ind_PE":35.4,"PB":6.8, "ROCE":18.4},
    "VGUARD":      {"Industry":"Capital Goods",           "Promoter":59.0,"PE":38.4,"Ind_PE":35.4,"PB":8.4, "ROCE":18.4},
    "VIJAYABANK":  {"Industry":"Financial Services",      "Promoter":0.0, "PE":8.4, "Ind_PE":15.2,"PB":0.8, "ROCE":8.4},
    "VBL":         {"Industry":"FMCG",                   "Promoter":62.9,"PE":48.4,"Ind_PE":44.2,"PB":8.4, "ROCE":18.4},
    "WHIRLPOOL":   {"Industry":"Consumer Durables",       "Promoter":75.0,"PE":48.4,"Ind_PE":51.2,"PB":4.8, "ROCE":8.4},
    "YESBANK":     {"Industry":"Financial Services",      "Promoter":0.0, "PE":18.4,"Ind_PE":15.2,"PB":0.8, "ROCE":4.8},
    "ZEEL":        {"Industry":"Consumer Durables",       "Promoter":4.0, "PE":18.4,"Ind_PE":51.2,"PB":1.8, "ROCE":8.4},
}

# F&O eligible stocks (subset — Kite will return empty opts for non-F&O names)
FNO_UNIVERSE = {
    "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL","BPCL","BRITANNIA","CIPLA",
    "COALINDIA","DRREDDY","EICHERMOT","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE",
    "HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY","INDIGO","ITC",
    "JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NESTLEIND","NTPC","ONGC",
    "POWERGRID","RELIANCE","SBILIFE","SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM",
    "TATAMOTORS","TATASTEEL","TCS","TECHM","TITAN","TRENT","ULTRACEMCO","WIPRO",
    "ABB","AMBUJACEM","AUROPHARMA","BANKBARODA","BOSCHLTD","CANBK","CHOLAFIN",
    "COLPAL","CUMMINSIND","DABUR","DLF","FEDERALBNK","GAIL","GODREJCP",
    "GODREJPROP","HAL","HAVELLS","HEROMOTOCO","IDFCFIRSTB","IGL","IOC","IRCTC",
    "LTIM","LUPIN","MARICO","MOTHERSON","MPHASIS","MRF","MUTHOOTFIN","NMDC",
    "OFSS","PAGEIND","PERSISTENT","PETRONET","PFC","PIDILITIND","PIIND","PNB",
    "POLYCAB","RECLTD","SIEMENS","SRF","TORNTPHARM","TORNTPOWER","TVSMOTOR",
    "UNIONBANK","VEDL","VOLTAS","ZYDUSLIFE","JIOFIN","MAXHEALTH","BERGEPAINT",
    "BAJAJHLDNG","ATGL","ZOMATO","NYKAA","IRFC","ICICIPRU","LICI","BANDHANBNK",
    "AUBANK","BALKRISIND","BHARATFORG","BIOCON","BSE","COFORGE","CONCOR",
    "DEEPAKNTR","DIXON","ESCORTS","EXIDEIND","GLENMARK","GRANULES","HAPPSTMNDS",
    "INDHOTEL","INDUSTOWER","IPCALAB","JUBLFOOD","KPITTECH","LAURUSLABS",
    "LICHSGFIN","MANAPPURAM","MCX","METROPOLIS","NATCOPHARM","OBEROIRLTY",
    "PHOENIXLTD","PRESTIGE","PVRINOX","SAIL","SOLARINDS","SONACOMS","STARHEALTH",
    "SUNDARMFIN","SYNGENE","TATACHEM","TATACOMM","TATAELXSI","TATAPOWER",
    "THERMAX","TRIDENT","VBL","YESBANK","IDFC",
}

# ─── INDICATORS ───────────────────────────────────────────────────────────────
def calculate_indicators(df, mode="intraday"):
    """
    mode='intraday'  → VWMA 9, 26  + RSI-14 + Smoothed RSI-14 + Vol MA 20
    mode='longterm'  → VWMA 50, 100 + RSI-14 + Smoothed RSI-14 + Vol MA 50
    """
    for col in ['close','high','low','volume']:
        df[col] = pd.to_numeric(df[col])

    if mode == "intraday":
        df['VWMA_A'] = ta.vwma(df['close'], df['volume'], length=9)
        df['VWMA_B'] = ta.vwma(df['close'], df['volume'], length=26)
        df['VOL_MA'] = df['volume'].rolling(20).mean()
    else:
        df['VWMA_A'] = ta.vwma(df['close'], df['volume'], length=50)
        df['VWMA_B'] = ta.vwma(df['close'], df['volume'], length=100)
        df['VOL_MA'] = df['volume'].rolling(50).mean()

    df['RSI']          = ta.rsi(df['close'], length=14)
    df['RSI_SMOOTH']   = df['RSI'].ewm(span=14, adjust=False).mean()   # Smoothed RSI
    return df

def get_fibonacci_pivots(df, mode="intraday"):
    """
    Intraday  → use previous daily candle (last full row in daily df), 20 pivots back
    Long Term → use previous monthly candle, 50 pivots back
    Returns P, R1, R2, S1, S2
    """
    if len(df) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    prev = df.iloc[-2]
    H, L, C = float(prev['high']), float(prev['low']), float(prev['close'])
    P  = (H + L + C) / 3.0
    R1 = P + 0.382 * (H - L)
    R2 = P + 0.618 * (H - L)
    S1 = P - 0.382 * (H - L)
    S2 = P - 0.618 * (H - L)
    return round(P,2), round(R1,2), round(R2,2), round(S1,2), round(S2,2)

def get_crossover_details(df):
    """Detects last VWMA_A / VWMA_B crossover, returns (cross_price, type, bars_ago)."""
    if len(df) < 2: return 0.0, "No Cross", 0
    df = df.copy().dropna(subset=['VWMA_A','VWMA_B']).reset_index(drop=True)
    df['sign'] = (df['VWMA_A'] > df['VWMA_B']).astype(int)
    crosses = df[df['sign'] != df['sign'].shift(1)].iloc[1:]
    if not crosses.empty:
        last = crosses.iloc[-1]
        bars_ago = len(df) - 1 - crosses.index[-1]
        ctype = "🔥 Bullish" if last['VWMA_A'] > last['VWMA_B'] else "❄️ Bearish"
        return round(float(last['VWMA_A']), 2), ctype, int(bars_ago)
    return 0.0, "No Cross", 0


def get_crossover_signal(df):
    if len(df) < 3 or 'VWMA_9' not in df.columns:
        return "No Cross"
    latest, prev = df.iloc[-1], df.iloc[-2]
    if prev['VWMA_9'] <= prev['VWMA_26'] and latest['VWMA_9'] > latest['VWMA_26']:
        return "🔥 9 crosses 26 from below"
    elif prev['VWMA_9'] >= prev['VWMA_26'] and latest['VWMA_9'] < latest['VWMA_26']:
        return "❄️ 9 crosses 26 from above"
    return "No Cross"

def trading_signal_logic(latest, india_vix):
    signals = []
    price = latest['close']

    if india_vix < 15 and 'VWMA_9' in latest and 'VWMA_26' in latest:  # Trending Market
        if price > 1.01 * latest['VWMA_9'] and latest['VWMA_9'] > latest['VWMA_26']:
            target = round(price * 1.015, 2)
            stoploss = round(price - (target - price)/1.5, 2)
            signals.append({"Signal":"BUY","Target":target,"Stoploss":stoploss})
        elif price < 0.99 * latest['VWMA_9'] and latest['VWMA_9'] < latest['VWMA_26']:
            target = round(price * 0.985, 2)
            stoploss = round(price + (price - target)/1.5, 2)
            signals.append({"Signal":"SELL","Target":target,"Stoploss":stoploss})

    elif 'P' in latest and 'R1' in latest and 'S1' in latest:  # Sideways/Volatile Market
        pivot, r1, s1 = latest['P'], latest['R1'], latest['S1']
        midpoint = pivot + (r1 - pivot) * 0.5
        if price < midpoint:
            signals.append({"Signal":"BUY","Target":round(r1,2),"Stoploss":round(s1,2)})
        elif price > midpoint:
            signals.append({"Signal":"SELL","Target":round(s1,2),"Stoploss":round(r1,2)})

    return signals
# ─── OPTION CHAIN ─────────────────────────────────────────────────────────────
def fetch_option_chain(kite, symbol, ltp, nfo_instruments):
    if symbol not in FNO_UNIVERSE:
        return "NA", "NA"
    try:
        opts = [i for i in nfo_instruments
                if i['name'] == symbol and i['instrument_type'] in ('CE','PE')]
        if not opts: return "NA", "NA"

        expiries     = sorted(set(i['expiry'] for i in opts))
        nearest_exp  = expiries[0]
        opts         = [i for i in opts if i['expiry'] == nearest_exp]

        strikes      = sorted(set(i['strike'] for i in opts))
        atm_idx      = min(range(len(strikes)), key=lambda i: abs(strikes[i] - ltp))
        nearby       = strikes[max(0, atm_idx-4): atm_idx+5]

        ce_toks = {str(i['instrument_token']): i['strike']
                   for i in opts if i['instrument_type']=='CE' and i['strike'] in nearby}
        pe_toks = {str(i['instrument_token']): i['strike']
                   for i in opts if i['instrument_type']=='PE' and i['strike'] in nearby}
        if not ce_toks or not pe_toks: return "NA", "NA"

        quotes = kite.quote([f"NFO:{t}" for t in list(ce_toks)+list(pe_toks)])

        def best(toks):
            bs, boi, blp = None, -1, 0.0
            for tok, strike in toks.items():
                q  = quotes.get(f"NFO:{tok}", {})
                oi = q.get("oi", 0) or 0
                lp = q.get("last_price", 0.0) or 0.0
                if oi > boi:
                    boi, bs, blp = oi, strike, lp
            return bs, boi, blp

        cs, coi, clp = best(ce_toks)
        ps, poi, plp = best(pe_toks)
        exp_str = nearest_exp.strftime("%d%b%y").upper() if hasattr(nearest_exp,'strftime') else str(nearest_exp)
        ce_str  = f"{int(cs)} CE ₹{clp:.2f} | OI {int(coi):,} ({exp_str})" if cs else "NA"
        pe_str  = f"{int(ps)} PE ₹{plp:.2f} | OI {int(poi):,} ({exp_str})" if ps else "NA"
        return ce_str, pe_str
    except Exception:
        return "NA", "NA"

# ─── SIGNAL ENGINE ────────────────────────────────────────────────────────────
def compute_signal(ltp, va, vb, rsi, rsi_smooth, vol, vol_ma,
                   cross_val, cross_type,
                   P, R1, R2, S1, S2, india_vix, mode):
    """
    Unified signal logic from notes:
    BUY  → Price ≥ 1% above VWMA crossover level  AND  RSI > 60
           Volume(0) > Volume MA
    SELL → Price ≤ 1% below VWMA crossover level  AND  RSI < 40
           Volume(0) > Volume MA
    NEUTRAL → any condition fails

    Target / SL (same for intraday & long-term as per instruction):
      - Normal:   Target = Pivot R1, SL = Pivot S1 (1.5:1 R:R enforced)
      - If price > 50% above/below between P↔R1 or P↔S1 → suppress signal
      - If price already past R1/S1 → use next level (R2/S2)
    """
    signal    = "⚪ NEUTRAL"
    target    = 0.0
    sl        = 0.0
    skip_note = ""

    vol_ok = vol > vol_ma if (vol_ma and vol_ma > 0) else True

    # Cross proximity: price ≥ 1% above crossover for BUY, ≤ 1% below for SELL
    if cross_val > 0:
        above_cross = ltp >= cross_val * 1.01    # price ≥ 1% above cross level
        below_cross = ltp <= cross_val * 0.99    # price ≤ 1% below cross level
    else:
        above_cross = va > vb   # fallback: use live VWMA order
        below_cross = va < vb

    buy_cond  = above_cross and rsi > 60  and vol_ok
    sell_cond = below_cross and rsi < 40  and vol_ok

    if not (buy_cond or sell_cond):
        return signal, target, sl, skip_note

    # ── Determine Target & SL from Fibonacci Pivots ──
    if buy_cond:
        raw_target = R1
        raw_sl     = S1
        mid_p_r1   = (P + R1) / 2.0
        # Suppress if price is more than 50% of the way between P and R1
        if ltp > mid_p_r1:
            return "⚪ NEUTRAL", 0.0, 0.0, "Price >50% into P→R1 zone"
        # If price already above R1, use R2
        if ltp >= R1:
            raw_target = R2
        target_dist = raw_target - ltp
        if target_dist <= 0:
            return "⚪ NEUTRAL", 0.0, 0.0, "No room to target"
        sl = round(ltp - (target_dist / 1.5), 2)
        # Ensure SL doesn't cross S1 (hard floor)
        sl = max(sl, round(S1, 2))
        signal = "🟢 BUY"
        target = round(raw_target, 2)

    elif sell_cond:
        raw_target = S1
        raw_sl     = R1
        mid_p_s1   = (P + S1) / 2.0
        # Suppress if price is more than 50% of the way between P and S1
        if ltp < mid_p_s1:
            return "⚪ NEUTRAL", 0.0, 0.0, "Price >50% into P→S1 zone"
        # If price already below S1, use S2
        if ltp <= S1:
            raw_target = S2
        target_dist = ltp - raw_target
        if target_dist <= 0:
            return "⚪ NEUTRAL", 0.0, 0.0, "No room to target"
        sl = round(ltp + (target_dist / 1.5), 2)
        sl = min(sl, round(R1, 2))
        signal = "🔴 SELL"
        target = round(raw_target, 2)

    return signal, target, sl, skip_note

# ─── PARALLEL SCAN ────────────────────────────────────────────────────────────
def execute_scan(meta_df, token_lookup, kite, india_vix, scanner_mode):
    """
    scanner_mode: 'intraday' | 'swing' | 'longterm'
    intraday & swing  → 15min + 1D frames, VWMA 9/26
    longterm          → 1D + Monthly frames, VWMA 50/100
    """
    nfo_instr = get_nfo_instruments()
    results   = []

    is_lt = scanner_mode == "longterm"

    def worker(row):
        symbol = str(row['Ticker']).strip()
        token  = token_lookup.get(symbol)
        if not token: return None
        try:
            now = datetime.now()
            # Fetch history
            hist_day = kite.historical_data(
                token,
                from_date=(now - timedelta(days=400)).strftime('%Y-%m-%d'),
                to_date=now.strftime('%Y-%m-%d'),
                interval="day"
            )
            if not hist_day: return None except Exception as e:
    return None
result = {
    "Stock Name": symbol,
    "Close": round(latest_15m['close'],2),
    "VWMA Cross (15M)": get_crossover_signal(df_15m),
    "Signals (15M)": signals,
    # keep all your existing fields intact...
}
india_vix = fetch_india_vix(kite)
signals = trading_signal_logic(latest_15m, india_vix)

result = {
    "Stock Name": symbol,
    "Close": round(latest_1d['close'],2),
    "VWMA Cross (1d)": get_crossover_signal(df_1d),
    "Signals (1d)": signals,
    # keep all your existing fields intact...
}
            
            df_day = calculate_indicators(
                pd.DataFrame(hist_day),
                mode="longterm" if is_lt else "intraday"
            )

            ltp_val = round(float(df_day.iloc[-1]['close']), 2)
            ce_str, pe_str = fetch_option_chain(kite, symbol, ltp_val, nfo_instr)

            # Base stock record
            stock_data = {
                "Stock":                  symbol,
                "Industry":               row.get("Industry","—"),
                "Promoter (%)":           row.get("Promoter_Percent", 0.0),
                "Stock PE":               row.get("Stock_PE", 0.0),
                "Industry PE":            row.get("Industry_PE", 0.0),
                "PB":                     row.get("PB", 0.0),
                "ROCE":                   row.get("ROCE", 0.0),
                "LTP":                    ltp_val,
                "OI Call (ATM)":          ce_str,
                "OI Put (ATM)":           pe_str,
            }

            # ── Timeframe loop ──────────────────────────────────────
            if is_lt:
                # Long term: 1D and Monthly
                # Build monthly OHLCV by resampling daily data
                df_day_idx = df_day.copy()
                df_day_idx['date'] = pd.to_datetime([r['date'] for r in hist_day])
                df_day_idx = df_day_idx.set_index('date')

                monthly_ohlcv = df_day_idx[['open','high','low','close','volume']].resample('ME').agg({
                    'open':'first','high':'max','low':'min','close':'last','volume':'sum'
                }).dropna().reset_index()
                df_monthly = calculate_indicators(monthly_ohlcv, mode="longterm")

                timeframes = {"1D": df_day, "1M": df_monthly}
                piv_df     = df_monthly   # monthly pivots for long term
            else:
                # Intraday/Swing: 15min and 1D
                hist_15m = kite.historical_data(
                    token,
                    from_date=(now - timedelta(days=12)).strftime('%Y-%m-%d'),
                    to_date=now.strftime('%Y-%m-%d'),
                    interval="15minute"
                )
                if not hist_15m: return None
                df_15m = calculate_indicators(pd.DataFrame(hist_15m), mode="intraday")
                timeframes = {"15M": df_15m, "1D": df_day}
                piv_df     = df_day   # daily pivots for intraday

            P, R1, R2, S1, S2 = get_fibonacci_pivots(piv_df, mode="intraday" if not is_lt else "longterm")
            piv_str = f"P:{P} | R1:{R1} | R2:{R2} | S1:{S1} | S2:{S2}"

            for tf, df_tf in timeframes.items():
                if len(df_tf) < 5: continue
                latest = df_tf.iloc[-1]
                ltp    = round(float(latest['close']), 2)
                va     = float(latest.get('VWMA_A', 0))
                vb     = float(latest.get('VWMA_B', 0))
                rsi    = float(latest.get('RSI', 50))
                rsi_s  = float(latest.get('RSI_SMOOTH', 50))
                vol    = float(latest.get('volume', 0))
                vol_ma = float(latest.get('VOL_MA', 0))

                cross_val, cross_type, bars_ago = get_crossover_details(df_tf)

                sig, tgt, sl, note = compute_signal(
                    ltp, va, vb, rsi, rsi_s, vol, vol_ma,
                    cross_val, cross_type,
                    P, R1, R2, S1, S2,
                    india_vix, scanner_mode
                )

                vwma_label_a = "VWMA 50" if is_lt else "VWMA 9"
                vwma_label_b = "VWMA 100" if is_lt else "VWMA 26"

                stock_data.update({
                    f"Signal ({tf})":         sig,
                    f"{vwma_label_a} ({tf})": round(va, 2),
                    f"{vwma_label_b} ({tf})": round(vb, 2),
                    f"RSI ({tf})":            round(rsi, 2),
                    f"RSI Smooth ({tf})":     round(rsi_s, 2),
                    f"Vol > Vol MA ({tf})":   "✅" if vol > vol_ma else "❌",
                    f"Target ({tf})":         tgt,
                    f"StopLoss ({tf})":       sl,
                    f"Cross ({tf})":          f"{cross_type} @ {cross_val} ({bars_ago} bars ago)",
                    f"Pivots ({tf})":         piv_str,
                })

            return stock_data
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(worker, row) for _, row in meta_df.iterrows()]
        for f in as_completed(futs):
            r = f.result()
            if r: results.append(r)
    return results

# ─── METADATA LOADER ──────────────────────────────────────────────────────────
def load_metadata():
    fallback = [{
        "Ticker": t, "Industry": d["Industry"], "Promoter_Percent": d["Promoter"],
        "Stock_PE": d["PE"], "Industry_PE": d["Ind_PE"], "PB": d["PB"], "ROCE": d["ROCE"]
    } for t, d in NIFTY500_UNIVERSE.items()]
    return pd.DataFrame(fallback)

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def run():
    meta_df = load_metadata()
    kite    = get_kite()
    token_lookup = get_instrument_lookup()
    india_vix    = fetch_india_vix(kite)

    vix_color    = "#00E5A0" if india_vix < 15.0 else "#F5A623"
    regime_label = "TRENDING (VIX < 15)" if india_vix < 15.0 else "VOLATILE (VIX ≥ 15)"

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="padding:0.8rem 0 0.4rem;font-family:'Space Grotesk',sans-serif;
                font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;color:#4A5A78;">
        Market Regime</div>""", unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div style="background:#10141C;border:1px solid #1F2A3C;border-radius:8px;
                padding:0.9rem 1rem;margin-bottom:0.8rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#4A5A78;
                  text-transform:uppercase;margin-bottom:4px;">India VIX</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;
                  font-weight:500;color:{vix_color};">{india_vix}</div>
    </div>
    <div style="background:#10141C;border:1px solid #1F2A3C;border-radius:8px;
                padding:0.8rem 1rem;margin-bottom:0.8rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#4A5A78;
                  text-transform:uppercase;margin-bottom:4px;">Regime</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.82rem;
                  font-weight:600;color:#E8EDF5;">{regime_label}</div>
    </div>
    <div style="background:#0D2045;border:1px solid #3B82F6;border-radius:6px;
                padding:0.6rem 0.9rem;font-family:'Space Grotesk',sans-serif;
                font-size:0.75rem;color:#3B82F6;margin-bottom:0.8rem;">
      🔒 R:R Floor · <strong>1.5 : 1</strong>
    </div>
    <div style="background:#10141C;border:1px solid #1F2A3C;border-radius:8px;
                padding:0.8rem 1rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#4A5A78;
                  text-transform:uppercase;margin-bottom:6px;">Signal Rules</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.76rem;color:#00E5A0;
                  margin-bottom:2px;">🟢 BUY</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;color:#8A9ABB;
                  margin-bottom:8px;">Price ≥ 1% above VWMA cross<br>RSI &gt; 60 · Vol &gt; Vol MA</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.76rem;color:#FF4D6A;
                  margin-bottom:2px;">🔴 SELL</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;color:#8A9ABB;">
        Price ≤ 1% below VWMA cross<br>RSI &lt; 40 · Vol &gt; Vol MA</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Scanner Mode Tabs ─────────────────────────────────────────────────────
    tab_intra, tab_swing, tab_lt, tab_fund = st.tabs([
        "  ⚡  Intraday / Short Swing  ",
        "  📈  Short Swing Detail  ",
        "  🏦  Short / Med / Long Term  ",
        "  🏢  Fundamentals  "
    ])

    for tab, mode_key, label in [
        (tab_intra, "intraday", "Intraday · Short Swing"),
        (tab_swing, "intraday", "Short Swing Detail"),
        (tab_lt,    "longterm", "Short · Med · Long Term"),
    ]:
        with tab:
            sess_key_df   = f"df_{mode_key}"
            sess_key_time = f"ts_{mode_key}"

            if sess_key_df   not in st.session_state: st.session_state[sess_key_df]   = None
            if sess_key_time not in st.session_state: st.session_state[sess_key_time] = None

            current_t = time.time()
            stale = (
                st.session_state[sess_key_df] is None or
                (st.session_state[sess_key_time] and current_t - st.session_state[sess_key_time] >= 900)
            )

            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button(f"⟳  Scan ({label})", key=f"btn_{mode_key}_{label}", use_container_width=True):
                    stale = True
            with c2:
                if st.session_state[sess_key_time]:
                    ts = datetime.fromtimestamp(st.session_state[sess_key_time]).strftime('%H:%M:%S')
                    st.markdown(
                        f"""<div style="padding-top:6px;font-family:'JetBrains Mono',monospace;
                        font-size:0.75rem;color:#4A5A78;">Last sync &nbsp;
                        <span style="color:#8A9ABB;">{ts}</span></div>""",
                        unsafe_allow_html=True
                    )

            if stale:
                with st.spinner(f"Scanning {len(meta_df)} stocks ({label})..."):
                    rows = execute_scan(meta_df, token_lookup, kite, india_vix, mode_key)
                    if rows:
                        st.session_state[sess_key_df]   = pd.DataFrame(rows)
                        st.session_state[sess_key_time] = current_t
                        st.rerun()

            df = st.session_state[sess_key_df]

            if df is None:
                st.info("Click Scan to load data.")

            else:
                is_lt_tab = mode_key == "longterm"
                tf1 = "1D" if is_lt_tab else "15M"
                tf2 = "1M" if is_lt_tab else "1D"
                vA  = "VWMA 50" if is_lt_tab else "VWMA 9"
                vB  = "VWMA 100" if is_lt_tab else "VWMA 26"

                active_tf = st.radio("Timeframe View", [tf1, tf2], horizontal=True, key=f"tf_{mode_key}_{label}")
                sig_col   = f"Signal ({active_tf})"

                if sig_col in df.columns:
                    buys  = (df[sig_col] == "🟢 BUY").sum()
                    sells = (df[sig_col] == "🔴 SELL").sum()
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Stocks Scanned", len(df))
                    m2.metric("🟢 BUY Signals",  buys)
                    m3.metric("🔴 SELL Signals", sells)
                    m4.metric("⚪ Neutral",       len(df) - buys - sells)
                st.divider()

                base_cols = [
                    "Stock", sig_col, "LTP",
                    f"{vA} ({active_tf})", f"{vB} ({active_tf})",
                    f"RSI ({active_tf})", f"RSI Smooth ({active_tf})",
                    f"Vol > Vol MA ({active_tf})",
                    f"Target ({active_tf})", f"StopLoss ({active_tf})",
                    f"Cross ({active_tf})", f"Pivots ({active_tf})",
                    "OI Call (ATM)", "OI Put (ATM)"
                ]
                disp_cols = [c for c in base_cols if c in df.columns]

                sig_df = df[df[sig_col].isin(["🟢 BUY", "🔴 SELL"])] if sig_col in df.columns else pd.DataFrame()
                if not sig_df.empty:
                    st.markdown(
                        f"""<div style="font-family:'Space Grotesk',sans-serif;font-size:0.7rem;
                        color:#4A5A78;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.5rem;">
                        ⚡ Active Signals · {active_tf}</div>""",
                        unsafe_allow_html=True
                    )
                    st.dataframe(sig_df[disp_cols], use_container_width=True, hide_index=True)
                    st.divider()
                else:
                    st.info(f"No BUY/SELL signals on {active_tf} timeframe under current conditions.")

                st.markdown(
                    f"""<div style="font-family:'Space Grotesk',sans-serif;font-size:0.7rem;
                    color:#4A5A78;letter-spacing:0.06em;text-transform:uppercase;margin:0.8rem 0 0.4rem;">
                    📋 Full Universe · {active_tf}</div>""",
                    unsafe_allow_html=True
                )
                sort_col = sig_col if sig_col in df.columns else disp_cols[0]
                st.dataframe(
                    df[disp_cols].sort_values(by=sort_col, ascending=True),
                    use_container_width=True, hide_index=True
                )

    # ── Fundamentals Tab ─────────────────────────────────────────────────────
    with tab_fund:
        st.markdown("""<div style="font-family:'Space Grotesk',sans-serif;font-size:0.7rem;
            color:#4A5A78;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.8rem;">
            Valuation & Ownership Filter</div>""", unsafe_allow_html=True)

        # Try to use whichever scan has run — must use 'is not None' to avoid pandas ValueError
        _d1 = st.session_state.get("df_intraday")
        _d2 = st.session_state.get("df_longterm")
        base_df = _d1 if (_d1 is not None and not _d1.empty) else \
                  (_d2 if (_d2 is not None and not _d2.empty) else None)
        if base_df is None:
            st.info("Run any scanner tab first to populate fundamentals.")
        else:
            f1, f2 = st.columns(2)
            with f1:
                sectors = ["All"] + sorted(base_df["Industry"].dropna().unique().tolist())
                sel_sec = st.selectbox("Sector", sectors)
            with f2:
                tier_map = {"All":"All","High (>50%)":"High (>50%)","Medium (30-50%)":"Medium (30-50%)","Low (<30%)":"Low (<30%)"}
                sel_tier = st.selectbox("Promoter Tier", list(tier_map.keys()))

            fdf = base_df.copy()
            if sel_sec != "All":
                fdf = fdf[fdf["Industry"] == sel_sec]
            if sel_tier != "All":
                def tier(x):
                    x = float(x) if x else 0
                    return "High (>50%)" if x>=50 else ("Medium (30-50%)" if x>=30 else "Low (<30%)")
                fdf = fdf[fdf["Promoter (%)"].apply(tier) == sel_tier]

            fund_cols = ["Stock","Industry","Promoter (%)","Stock PE","Industry PE","PB","ROCE","LTP",
                         "OI Call (ATM)","OI Put (ATM)"]
            fund_cols = [c for c in fund_cols if c in fdf.columns]
            if not fdf.empty:
                st.dataframe(
                    fdf[fund_cols].sort_values(["Industry","Promoter (%)"], ascending=[True,False]),
                    use_container_width=True, hide_index=True
                )

if __name__ == "__main__":
    run()


# ─── KITE INIT ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_kite():
    kite = KiteConnect(api_key=st.secrets["api_key"], timeout=15)
    kite.set_access_token(st.secrets["access_token"])
    return kite

@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {i['tradingsymbol']: str(i['instrument_token']) for i in instruments}
    except Exception as e:
        st.error(f"Instrument lookup failed: {e}")
        return {}

def fetch_india_vix(kite):
    try:
        return float(kite.ltp("NSE:INDIA VIX")["NSE:INDIA VIX"]["last_price"])
    except Exception:
        return 14.5

# ─── INDICATOR CALCULATIONS ───────────────────────────────────────────────────
def calculate_indicators(df, indicator_choice="VWMA"):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])

    if indicator_choice == "VWMA":
        df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
        df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
        df['RSI'] = ta.rsi(df['close'], length=14)
        pivots = ta.pivots(df['high'], df['low'], df['close'], mode="fibonacci", lookback=20)
        df = pd.concat([df, pivots], axis=1)

    elif indicator_choice == "EMA":
        df['EMA_9'] = ta.ema(df['close'], length=9)
        df['EMA_26'] = ta.ema(df['close'], length=26)

    elif indicator_choice == "Supertrend":
        st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
        df = pd.concat([df, st_data], axis=1)

    elif indicator_choice == "Bollinger":
        bbands = ta.bbands(df['close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)

    return df

def get_crossover_signal(df):
    if len(df) < 3 or 'VWMA_9' not in df.columns:
        return "No Cross"
    latest, prev = df.iloc[-1], df.iloc[-2]
    if prev['VWMA_9'] <= prev['VWMA_26'] and latest['VWMA_9'] > latest['VWMA_26']:
        return "🔥 9 crosses 26 from below"
    elif prev['VWMA_9'] >= prev['VWMA_26'] and latest['VWMA_9'] < latest['VWMA_26']:
        return "❄️ 9 crosses 26 from above"
    return "No Cross"

# ─── TRADING SIGNAL LOGIC ─────────────────────────────────────────────────────
def trading_signal_logic(latest, india_vix):
    signals = []
    price = latest['close']

    if india_vix < 15 and 'VWMA_9' in latest and 'VWMA_26' in latest:  # Trending Market
        if price > 1.01 * latest['VWMA_9'] and latest['VWMA_9'] > latest['VWMA_26']:
            target = round(price * 1.015, 2)
            stoploss = round(price - (target - price)/1.5, 2)
            signals.append({"Signal":"BUY","Target":target,"Stoploss":stoploss})
        elif price < 0.99 * latest['VWMA_9'] and latest['VWMA_9'] < latest['VWMA_26']:
            target = round(price * 0.985, 2)
            stoploss = round(price + (price - target)/1.5, 2)
            signals.append({"Signal":"SELL","Target":target,"Stoploss":stoploss})

    elif 'P' in latest and 'R1' in latest and 'S1' in latest:  # Sideways/Volatile Market
        pivot, r1, s1 = latest['P'], latest['R1'], latest['S1']
        midpoint = pivot + (r1 - pivot) * 0.5
        if price < midpoint:
            signals.append({"Signal":"BUY","Target":round(r1,2),"Stoploss":round(s1,2)})
        elif price > midpoint:
            signals.append({"Signal":"SELL","Target":round(s1,2),"Stoploss":round(r1,2)})

    return signals

# ─── SCANNER PIPELINE ─────────────────────────────────────────────────────────
def run_scan(universe, token_lookup, kite, interval, indicator_choice):
    india_vix = fetch_india_vix(kite)
    results = []

    def worker(symbol):
        token = token_lookup.get(symbol)
        if not token:
            return None
        try:
            hist = kite.historical_data(
                token,
                from_date=(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'),
                interval=interval
            )
            if not hist or len(hist) < 30:
                return None

            df = pd.DataFrame(hist)
            df = calculate_indicators(df, indicator_choice)
            latest = df.iloc[-1]

            crossover = get_crossover_signal(df)
            signals = trading_signal_logic(latest, india_vix)

            return {
                "Stock": symbol,
                "Close": round(latest['close'],2),
                "VWMA Cross": crossover,
                "Signals": signals
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, sym) for sym in universe]
        for f in as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    return pd.DataFrame(results)

# ─── STREAMLIT UI ─────────────────────────────────────────────────────────────
st.title("📊 NIFTY 500 Multi-Timeframe Scanner")

kite = get_kite()
token_lookup = get_instrument_lookup()
universe = list(token_lookup.keys())[:50]  # demo subset

indicator_choice = st.selectbox("Choose Indicator Set", ["VWMA","EMA","Supertrend","Bollinger"])

tab1, tab2, tab3 = st.tabs(["📈 Short Term (15m)", "📉 Mid Term (1D)", "📊 Long Term (1W)"])

with tab1:
    if st.button("Run Short Term Scan"):
        df = run_scan(universe, token_lookup, kite, "15minute", indicator_choice)
        st.dataframe(df)

with tab2:
    if st.button("Run Mid Term Scan"):
        df = run_scan(universe, token_lookup, kite, "day", indicator_choice)
        st.dataframe(df)

with tab3:
    if st.button("Run Long Term Scan"):
        df = run_scan(universe, token_lookup, kite, "week", indicator_choice)
        st.dataframe(df)
indicator_choice = st.selectbox("Choose Indicator Set", ["VWMA","EMA","Supertrend","Bollinger"])

tab1, tab2, tab3 = st.tabs(["📈 Short Term (15m)", "📉 Mid Term (1D)", "📊 Long Term (1W)"])

with tab1:
    if st.button("Run Short Term Scan"):
        df = execute_parallel_scan(universe, token_lookup, kite, interval="15minute", indicator_choice=indicator_choice)
        st.dataframe(df)

with tab2:
    if st.button("Run Mid Term Scan"):
        df = execute_parallel_scan(universe, token_lookup, kite, interval="day", indicator_choice=indicator_choice)
        st.dataframe(df)

with tab3:
    if st.button("Run Long Term Scan"):
        df = execute_parallel_scan(universe, token_lookup, kite, interval="week", indicator_choice=indicator_choice)
        st.dataframe(df)
