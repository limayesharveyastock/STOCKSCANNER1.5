import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide", page_title="NIFTY 100 Scanner", page_icon="📊")

# ─── THEME ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg-base:#0A0C10;--bg-surface:#10141C;--bg-card:#151A24;--bg-elevated:#1C2232;
  --border:#1F2A3C;--border-bright:#2E3D56;
  --text-primary:#E8EDF5;--text-secondary:#8A9ABB;--text-muted:#4A5A78;
  --green:#00E5A0;--red:#FF4D6A;--amber:#F5A623;--blue:#3B82F6;--blue-dim:#0D2045;
  --font-ui:'Space Grotesk',sans-serif;--font-mono:'JetBrains Mono',monospace;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
  background-color:var(--bg-base)!important;color:var(--text-primary)!important;
  font-family:var(--font-ui)!important;}
[data-testid="stSidebar"]{background-color:var(--bg-surface)!important;border-right:1px solid var(--border)!important;}
[data-testid="stHeader"]{background-color:var(--bg-base)!important;}
[data-testid="metric-container"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;
  border-radius:8px!important;padding:1rem 1.2rem!important;}
[data-testid="metric-container"] label{font-size:0.72rem!important;letter-spacing:0.06em!important;
  text-transform:uppercase!important;color:var(--text-muted)!important;font-family:var(--font-ui)!important;}
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
[data-testid="stButton"]>button:hover{background:var(--blue-dim)!important;border-color:var(--blue)!important;color:var(--blue)!important;}
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:var(--bg-surface)!important;border-bottom:1px solid var(--border)!important;}
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;color:var(--text-muted)!important;
  font-family:var(--font-ui)!important;font-size:0.8rem!important;font-weight:600!important;
  letter-spacing:0.04em!important;padding:0.7rem 1.2rem!important;border-bottom:2px solid transparent!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--blue)!important;border-bottom-color:var(--blue)!important;}
[data-testid="stSelectbox"]>div>div{background:var(--bg-card)!important;border:1px solid var(--border)!important;
  border-radius:6px!important;color:var(--text-primary)!important;font-family:var(--font-ui)!important;font-size:0.82rem!important;}
[data-testid="stAlert"]{background:var(--blue-dim)!important;border:1px solid var(--blue)!important;
  border-radius:6px!important;font-family:var(--font-ui)!important;font-size:0.82rem!important;}
hr{border-color:var(--border)!important;margin:1.2rem 0!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:var(--bg-base);}
::-webkit-scrollbar-thumb{background:var(--border-bright);border-radius:3px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:0.2rem 0 1.2rem;">
  <div style="background:linear-gradient(135deg,#1C2E4A,#0D2045);border:1px solid #3B82F6;
              border-radius:8px;padding:6px 10px;font-size:1.3rem;line-height:1;">📊</div>
  <div>
    <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.25rem;
                letter-spacing:-0.02em;color:#E8EDF5;line-height:1.2;">
      NIFTY 100 Stock Scanner & Signal Generator</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#4A5A78;
                letter-spacing:0.06em;text-transform:uppercase;">
      Intraday · Med-Long Term Trades · Live</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── KITE ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_kite():
    kite = KiteConnect(api_key=st.secrets["api_key"], timeout=15)
    kite.set_access_token(st.secrets["access_token"])
    return kite

@st.cache_data(ttl=86400)
def get_instrument_lookup():
    try:
        instruments = get_kite().instruments("NSE")
        return {i['tradingsymbol']: str(i['instrument_token']) for i in instruments}
    except Exception as e:
        st.error(f"Instrument lookup failed: {e}")
        return {}

def fetch_india_vix(kite):
    try:
        return float(kite.ltp("NSE:INDIA VIX")["NSE:INDIA VIX"]["last_price"])
    except Exception:
        return 14.5

# ─── NIFTY 100 UNIVERSE ───────────────────────────────────────────────────────
# Key: {Industry, Promoter, PE, Ind_PE, PB, ROCE, NPM, OpProfGrowth3Y, SalesGrowth3Y, ROE3Y, ROCE3Y, CFO3Y}
NIFTY100 = {
    "ADANIENT":   {"Industry":"Metals & Mining",          "Promoter":72.6,"PE":45.2,"Ind_PE":24.1,"PB":4.2, "ROCE":12.5,"NPM":8.2, "OpGr3Y":18.4,"SalesGr3Y":22.1,"ROE3Y":14.2,"ROCE3Y":11.8,"CFO3Y":4200},
    "ADANIPORTS":  {"Industry":"Infrastructure / Services","Promoter":65.3,"PE":33.1,"Ind_PE":28.5,"PB":3.9, "ROCE":14.8,"NPM":24.1,"OpGr3Y":21.2,"SalesGr3Y":18.4,"ROE3Y":16.8,"ROCE3Y":14.2,"CFO3Y":6800},
    "APOLLOHOSP":  {"Industry":"Healthcare",              "Promoter":29.3,"PE":78.4,"Ind_PE":38.2,"PB":9.1, "ROCE":16.2,"NPM":6.4, "OpGr3Y":22.8,"SalesGr3Y":18.2,"ROE3Y":18.4,"ROCE3Y":15.8,"CFO3Y":2100},
    "ASIANPAINT":  {"Industry":"Consumer Durables",       "Promoter":52.6,"PE":55.4,"Ind_PE":51.2,"PB":14.2,"ROCE":34.1,"NPM":12.8,"OpGr3Y":14.2,"SalesGr3Y":12.4,"ROE3Y":28.4,"ROCE3Y":32.8,"CFO3Y":3800},
    "AXISBANK":    {"Industry":"Financial Services",      "Promoter":0.0, "PE":14.1,"Ind_PE":15.2,"PB":2.1, "ROCE":11.2,"NPM":18.4,"OpGr3Y":24.6,"SalesGr3Y":18.8,"ROE3Y":12.4,"ROCE3Y":10.8,"CFO3Y":9200},
    "BAJAJ-AUTO":  {"Industry":"Automobile",              "Promoter":55.0,"PE":31.2,"Ind_PE":26.4,"PB":8.4, "ROCE":30.5,"NPM":16.2,"OpGr3Y":12.4,"SalesGr3Y":14.8,"ROE3Y":22.4,"ROCE3Y":28.6,"CFO3Y":3400},
    "BAJFINANCE":  {"Industry":"Financial Services",      "Promoter":54.7,"PE":28.3,"Ind_PE":22.1,"PB":5.8, "ROCE":17.4,"NPM":22.8,"OpGr3Y":28.4,"SalesGr3Y":24.6,"ROE3Y":18.4,"ROCE3Y":16.8,"CFO3Y":8400},
    "BAJAJFINSV":  {"Industry":"Financial Services",      "Promoter":60.7,"PE":33.4,"Ind_PE":22.1,"PB":4.1, "ROCE":14.9,"NPM":16.4,"OpGr3Y":18.2,"SalesGr3Y":16.4,"ROE3Y":14.8,"ROCE3Y":13.6,"CFO3Y":5200},
    "BEL":         {"Industry":"Capital Goods",           "Promoter":51.1,"PE":42.6,"Ind_PE":35.4,"PB":7.8, "ROCE":26.3,"NPM":14.2,"OpGr3Y":22.4,"SalesGr3Y":18.6,"ROE3Y":24.2,"ROCE3Y":24.8,"CFO3Y":2800},
    "BHARTIARTL":  {"Industry":"Telecommunication",       "Promoter":53.1,"PE":52.1,"Ind_PE":41.3,"PB":8.9, "ROCE":18.2,"NPM":8.4, "OpGr3Y":18.6,"SalesGr3Y":14.2,"ROE3Y":12.4,"ROCE3Y":16.8,"CFO3Y":28000},
    "BPCL":        {"Industry":"Oil & Gas",               "Promoter":53.0,"PE":11.4,"Ind_PE":12.8,"PB":1.7, "ROCE":22.1,"NPM":3.2, "OpGr3Y":8.4, "SalesGr3Y":12.4,"ROE3Y":22.4,"ROCE3Y":20.8,"CFO3Y":9800},
    "BRITANNIA":   {"Industry":"FMCG",                   "Promoter":50.5,"PE":54.3,"Ind_PE":44.2,"PB":28.1,"ROCE":48.6,"NPM":12.4,"OpGr3Y":16.2,"SalesGr3Y":12.8,"ROE3Y":42.4,"ROCE3Y":46.2,"CFO3Y":2200},
    "CIPLA":       {"Industry":"Healthcare",              "Promoter":33.4,"PE":29.6,"Ind_PE":31.4,"PB":4.3, "ROCE":21.3,"NPM":12.8,"OpGr3Y":14.4,"SalesGr3Y":12.2,"ROE3Y":16.4,"ROCE3Y":19.8,"CFO3Y":3200},
    "COALINDIA":   {"Industry":"Oil & Gas",               "Promoter":63.1,"PE":9.2, "Ind_PE":12.8,"PB":3.4, "ROCE":54.2,"NPM":18.4,"OpGr3Y":14.8,"SalesGr3Y":12.4,"ROE3Y":48.4,"ROCE3Y":52.6,"CFO3Y":18000},
    "DRREDDY":     {"Industry":"Healthcare",              "Promoter":26.7,"PE":18.9,"Ind_PE":31.4,"PB":3.1, "ROCE":24.5,"NPM":16.4,"OpGr3Y":18.2,"SalesGr3Y":12.8,"ROE3Y":20.4,"ROCE3Y":22.8,"CFO3Y":4800},
    "EICHERMOT":   {"Industry":"Automobile",              "Promoter":49.2,"PE":29.1,"Ind_PE":26.4,"PB":7.2, "ROCE":27.8,"NPM":18.4,"OpGr3Y":14.2,"SalesGr3Y":16.4,"ROE3Y":24.4,"ROCE3Y":26.2,"CFO3Y":3600},
    "GRASIM":      {"Industry":"Construction Materials",  "Promoter":42.7,"PE":44.1,"Ind_PE":32.1,"PB":1.9, "ROCE":9.4, "NPM":6.4, "OpGr3Y":12.4,"SalesGr3Y":14.8,"ROE3Y":8.4, "ROCE3Y":8.8, "CFO3Y":5400},
    "HCLTECH":     {"Industry":"Information Technology",  "Promoter":60.8,"PE":25.4,"Ind_PE":28.2,"PB":6.1, "ROCE":28.9,"NPM":14.4,"OpGr3Y":12.8,"SalesGr3Y":14.2,"ROE3Y":24.4,"ROCE3Y":27.2,"CFO3Y":14000},
    "HDFCBANK":    {"Industry":"Financial Services",      "Promoter":0.0, "PE":18.2,"Ind_PE":15.2,"PB":2.6, "ROCE":12.1,"NPM":22.4,"OpGr3Y":18.4,"SalesGr3Y":16.8,"ROE3Y":14.4,"ROCE3Y":11.8,"CFO3Y":42000},
    "HDFCLIFE":    {"Industry":"Financial Services",      "Promoter":50.4,"PE":61.2,"Ind_PE":55.4,"PB":4.8, "ROCE":14.2,"NPM":8.4, "OpGr3Y":16.4,"SalesGr3Y":14.2,"ROE3Y":12.4,"ROCE3Y":13.8,"CFO3Y":6200},
    "HINDALCO":    {"Industry":"Metals & Mining",         "Promoter":34.6,"PE":16.3,"Ind_PE":18.4,"PB":1.8, "ROCE":13.1,"NPM":6.4, "OpGr3Y":14.2,"SalesGr3Y":18.4,"ROE3Y":12.4,"ROCE3Y":12.8,"CFO3Y":8400},
    "HINDUNILVR":  {"Industry":"FMCG",                   "Promoter":61.9,"PE":56.2,"Ind_PE":44.2,"PB":11.4,"ROCE":39.5,"NPM":16.4,"OpGr3Y":12.4,"SalesGr3Y":8.4, "ROE3Y":34.4,"ROCE3Y":38.2,"CFO3Y":8800},
    "ICICIBANK":   {"Industry":"Financial Services",      "Promoter":0.0, "PE":17.4,"Ind_PE":15.2,"PB":3.1, "ROCE":13.4,"NPM":24.4,"OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":14.4,"ROCE3Y":12.8,"CFO3Y":38000},
    "INDUSINDBK":  {"Industry":"Financial Services",      "Promoter":16.5,"PE":13.2,"Ind_PE":15.2,"PB":1.8, "ROCE":11.7,"NPM":16.4,"OpGr3Y":12.4,"SalesGr3Y":14.8,"ROE3Y":12.4,"ROCE3Y":11.2,"CFO3Y":7800},
    "INFY":        {"Industry":"Information Technology",  "Promoter":14.8,"PE":24.1,"Ind_PE":28.2,"PB":7.4, "ROCE":37.2,"NPM":17.4,"OpGr3Y":14.2,"SalesGr3Y":16.8,"ROE3Y":32.4,"ROCE3Y":36.4,"CFO3Y":18000},
    "INDIGO":      {"Industry":"Infrastructure / Services","Promoter":57.3,"PE":21.4,"Ind_PE":25.1,"PB":5.2, "ROCE":22.4,"NPM":8.4, "OpGr3Y":18.4,"SalesGr3Y":22.4,"ROE3Y":18.4,"ROCE3Y":20.8,"CFO3Y":9800},
    "ITC":         {"Industry":"FMCG",                   "Promoter":0.0, "PE":26.4,"Ind_PE":44.2,"PB":7.9, "ROCE":38.7,"NPM":28.4,"OpGr3Y":14.4,"SalesGr3Y":12.2,"ROE3Y":28.4,"ROCE3Y":36.8,"CFO3Y":14000},
    "JSWSTEEL":    {"Industry":"Metals & Mining",         "Promoter":44.8,"PE":27.2,"Ind_PE":18.4,"PB":3.2, "ROCE":14.1,"NPM":6.4, "OpGr3Y":12.4,"SalesGr3Y":14.8,"ROE3Y":14.4,"ROCE3Y":13.2,"CFO3Y":12000},
    "JIOFIN":      {"Industry":"Financial Services",      "Promoter":47.1,"PE":120.5,"Ind_PE":22.1,"PB":2.1,"ROCE":6.2, "NPM":42.4,"OpGr3Y":0.0, "SalesGr3Y":0.0, "ROE3Y":4.4, "ROCE3Y":5.8, "CFO3Y":1200},
    "KOTAKBANK":   {"Industry":"Financial Services",      "Promoter":25.9,"PE":19.1,"Ind_PE":15.2,"PB":2.9, "ROCE":12.8,"NPM":22.4,"OpGr3Y":18.4,"SalesGr3Y":16.4,"ROE3Y":14.4,"ROCE3Y":12.4,"CFO3Y":14000},
    "LT":          {"Industry":"Construction",            "Promoter":0.0, "PE":36.4,"Ind_PE":31.2,"PB":4.8, "ROCE":15.1,"NPM":8.4, "OpGr3Y":16.4,"SalesGr3Y":14.8,"ROE3Y":14.4,"ROCE3Y":14.8,"CFO3Y":7800},
    "M&M":         {"Industry":"Automobile",              "Promoter":19.3,"PE":28.4,"Ind_PE":26.4,"PB":4.9, "ROCE":19.2,"NPM":8.4, "OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":18.4,"ROCE3Y":18.8,"CFO3Y":6200},
    "MARUTI":      {"Industry":"Automobile",              "Promoter":58.2,"PE":27.5,"Ind_PE":26.4,"PB":5.1, "ROCE":21.4,"NPM":7.4, "OpGr3Y":18.4,"SalesGr3Y":14.8,"ROE3Y":16.4,"ROCE3Y":20.2,"CFO3Y":8400},
    "MAXHEALTH":   {"Industry":"Healthcare",              "Promoter":23.1,"PE":68.2,"Ind_PE":38.2,"PB":8.4, "ROCE":15.5,"NPM":7.4, "OpGr3Y":24.4,"SalesGr3Y":18.4,"ROE3Y":14.4,"ROCE3Y":14.8,"CFO3Y":1400},
    "NESTLEIND":   {"Industry":"FMCG",                   "Promoter":62.8,"PE":74.2,"Ind_PE":44.2,"PB":21.4,"ROCE":58.1,"NPM":14.4,"OpGr3Y":14.2,"SalesGr3Y":12.4,"ROE3Y":52.4,"ROCE3Y":56.4,"CFO3Y":3200},
    "NTPC":        {"Industry":"Power",                   "Promoter":51.1,"PE":17.5,"Ind_PE":19.4,"PB":2.4, "ROCE":11.9,"NPM":12.4,"OpGr3Y":12.4,"SalesGr3Y":8.4, "ROE3Y":12.4,"ROCE3Y":11.4,"CFO3Y":18000},
    "ONGC":        {"Industry":"Oil & Gas",               "Promoter":58.9,"PE":8.1, "Ind_PE":12.8,"PB":1.1, "ROCE":14.5,"NPM":8.4, "OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":12.4,"ROCE3Y":13.8,"CFO3Y":28000},
    "POWERGRID":   {"Industry":"Power",                   "Promoter":51.3,"PE":16.2,"Ind_PE":19.4,"PB":2.9, "ROCE":12.4,"NPM":28.4,"OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":18.4,"ROCE3Y":11.8,"CFO3Y":12000},
    "RELIANCE":    {"Industry":"Oil & Gas",               "Promoter":50.3,"PE":26.1,"Ind_PE":12.8,"PB":2.4, "ROCE":10.2,"NPM":8.4, "OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":10.4,"ROCE3Y":9.8, "CFO3Y":62000},
    "SBILIFE":     {"Industry":"Financial Services",      "Promoter":55.4,"PE":78.1,"Ind_PE":55.4,"PB":9.5, "ROCE":13.1,"NPM":6.4, "OpGr3Y":18.4,"SalesGr3Y":16.4,"ROE3Y":14.4,"ROCE3Y":12.8,"CFO3Y":4200},
    "SBIN":        {"Industry":"Financial Services",      "Promoter":57.5,"PE":10.4,"Ind_PE":15.2,"PB":1.6, "ROCE":11.8,"NPM":14.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":14.4,"ROCE3Y":11.4,"CFO3Y":42000},
    "SHRIRAMFIN":  {"Industry":"Financial Services",      "Promoter":25.4,"PE":14.8,"Ind_PE":22.1,"PB":2.2, "ROCE":15.4,"NPM":18.4,"OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":16.4,"ROCE3Y":14.8,"CFO3Y":3800},
    "SUNPHARMA":   {"Industry":"Healthcare",              "Promoter":54.5,"PE":36.2,"Ind_PE":31.4,"PB":4.9, "ROCE":17.2,"NPM":14.4,"OpGr3Y":16.4,"SalesGr3Y":12.8,"ROE3Y":14.4,"ROCE3Y":16.4,"CFO3Y":6800},
    "TATACONSUM":  {"Industry":"FMCG",                   "Promoter":34.4,"PE":64.1,"Ind_PE":44.2,"PB":4.1, "ROCE":9.8, "NPM":6.4, "OpGr3Y":18.4,"SalesGr3Y":14.8,"ROE3Y":8.4, "ROCE3Y":9.2, "CFO3Y":1800},
    "TATAMOTORS":  {"Industry":"Automobile",              "Promoter":46.4,"PE":11.5,"Ind_PE":26.4,"PB":3.2, "ROCE":20.1,"NPM":6.4, "OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":18.4,"ROCE3Y":19.4,"CFO3Y":18000},
    "TATASTEEL":   {"Industry":"Metals & Mining",         "Promoter":33.2,"PE":38.4,"Ind_PE":18.4,"PB":1.7, "ROCE":10.5,"NPM":4.4, "OpGr3Y":8.4, "SalesGr3Y":12.4,"ROE3Y":8.4, "ROCE3Y":9.8, "CFO3Y":14000},
    "TCS":         {"Industry":"Information Technology",  "Promoter":72.4,"PE":29.5,"Ind_PE":28.2,"PB":12.8,"ROCE":51.4,"NPM":18.4,"OpGr3Y":12.4,"SalesGr3Y":14.2,"ROE3Y":44.4,"ROCE3Y":49.8,"CFO3Y":42000},
    "TECHM":       {"Industry":"Information Technology",  "Promoter":35.1,"PE":48.2,"Ind_PE":28.2,"PB":3.8, "ROCE":15.9,"NPM":6.4, "OpGr3Y":4.4, "SalesGr3Y":8.4, "ROE3Y":12.4,"ROCE3Y":14.8,"CFO3Y":4800},
    "TITAN":       {"Industry":"Consumer Durables",       "Promoter":52.9,"PE":82.1,"Ind_PE":51.2,"PB":19.4,"ROCE":25.1,"NPM":6.4, "OpGr3Y":22.4,"SalesGr3Y":24.4,"ROE3Y":28.4,"ROCE3Y":24.2,"CFO3Y":3400},
    "TRENT":       {"Industry":"Retail",                  "Promoter":37.0,"PE":145.2,"Ind_PE":68.4,"PB":28.4,"ROCE":24.3,"NPM":8.4, "OpGr3Y":48.4,"SalesGr3Y":42.4,"ROE3Y":22.4,"ROCE3Y":22.8,"CFO3Y":1800},
    "ULTRACEMCO":  {"Industry":"Construction Materials",  "Promoter":60.0,"PE":41.2,"Ind_PE":32.1,"PB":4.7, "ROCE":13.8,"NPM":8.4, "OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":12.4,"ROCE3Y":12.8,"CFO3Y":6800},
    "UPL":         {"Industry":"Chemicals",               "Promoter":32.4,"PE":22.1,"Ind_PE":19.5,"PB":1.5, "ROCE":11.1,"NPM":4.4, "OpGr3Y":-4.4,"SalesGr3Y":2.4, "ROE3Y":6.4, "ROCE3Y":10.2,"CFO3Y":2800},
    "WIPRO":       {"Industry":"Information Technology",  "Promoter":72.9,"PE":23.4,"Ind_PE":28.2,"PB":3.4, "ROCE":21.2,"NPM":12.4,"OpGr3Y":6.4, "SalesGr3Y":8.4, "ROE3Y":14.4,"ROCE3Y":19.8,"CFO3Y":12000},
    # ── Nifty 100 additions ──
    "ABB":         {"Industry":"Capital Goods",           "Promoter":75.0,"PE":62.4,"Ind_PE":35.4,"PB":14.2,"ROCE":28.6,"NPM":8.4, "OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":24.4,"ROCE3Y":26.8,"CFO3Y":1200},
    "ADANIGREEN":  {"Industry":"Power",                   "Promoter":56.3,"PE":185.2,"Ind_PE":19.4,"PB":22.1,"ROCE":8.4, "NPM":14.4,"OpGr3Y":42.4,"SalesGr3Y":38.4,"ROE3Y":6.4, "ROCE3Y":7.8, "CFO3Y":4800},
    "ADANIPOWER":  {"Industry":"Power",                   "Promoter":74.2,"PE":14.6,"Ind_PE":19.4,"PB":4.8, "ROCE":22.1,"NPM":28.4,"OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":38.4,"ROCE3Y":20.4,"CFO3Y":6800},
    "AMBUJACEM":   {"Industry":"Construction Materials",  "Promoter":63.2,"PE":38.1,"Ind_PE":32.1,"PB":3.4, "ROCE":10.2,"NPM":8.4, "OpGr3Y":12.4,"SalesGr3Y":14.4,"ROE3Y":8.4, "ROCE3Y":9.8, "CFO3Y":3200},
    "ATGL":        {"Industry":"Oil & Gas",               "Promoter":74.8,"PE":68.4,"Ind_PE":12.8,"PB":8.9, "ROCE":18.4,"NPM":18.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":16.4,"ROCE3Y":17.8,"CFO3Y":1400},
    "AUROPHARMA":  {"Industry":"Healthcare",              "Promoter":51.8,"PE":22.4,"Ind_PE":31.4,"PB":3.2, "ROCE":19.5,"NPM":12.4,"OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":16.4,"ROCE3Y":18.8,"CFO3Y":2800},
    "BAJAJHLDNG":  {"Industry":"Financial Services",      "Promoter":57.2,"PE":18.4,"Ind_PE":22.1,"PB":2.8, "ROCE":14.1,"NPM":82.4,"OpGr3Y":8.4, "SalesGr3Y":4.4, "ROE3Y":12.4,"ROCE3Y":13.2,"CFO3Y":1800},
    "BANKBARODA":  {"Industry":"Financial Services",      "Promoter":63.9,"PE":6.8, "Ind_PE":15.2,"PB":1.1, "ROCE":9.8, "NPM":12.4,"OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":8.4, "ROCE3Y":9.2, "CFO3Y":12000},
    "BERGEPAINT":  {"Industry":"Consumer Durables",       "Promoter":74.9,"PE":52.1,"Ind_PE":51.2,"PB":12.4,"ROCE":28.9,"NPM":10.4,"OpGr3Y":12.4,"SalesGr3Y":10.4,"ROE3Y":24.4,"ROCE3Y":27.2,"CFO3Y":1400},
    "BOSCHLTD":    {"Industry":"Automobile",              "Promoter":70.5,"PE":38.2,"Ind_PE":26.4,"PB":6.8, "ROCE":22.4,"NPM":8.4, "OpGr3Y":16.4,"SalesGr3Y":14.4,"ROE3Y":16.4,"ROCE3Y":20.8,"CFO3Y":1800},
    "CANBK":       {"Industry":"Financial Services",      "Promoter":62.9,"PE":7.2, "Ind_PE":15.2,"PB":1.0, "ROCE":9.1, "NPM":10.4,"OpGr3Y":32.4,"SalesGr3Y":24.4,"ROE3Y":8.4, "ROCE3Y":8.6, "CFO3Y":8800},
    "CHOLAFIN":    {"Industry":"Financial Services",      "Promoter":51.4,"PE":28.6,"Ind_PE":22.1,"PB":4.8, "ROCE":16.2,"NPM":18.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":16.4,"ROCE3Y":15.8,"CFO3Y":4200},
    "COLPAL":      {"Industry":"FMCG",                   "Promoter":51.0,"PE":48.6,"Ind_PE":44.2,"PB":18.4,"ROCE":52.1,"NPM":14.4,"OpGr3Y":12.4,"SalesGr3Y":8.4, "ROE3Y":46.4,"ROCE3Y":50.4,"CFO3Y":2200},
    "CUMMINSIND":  {"Industry":"Capital Goods",           "Promoter":51.0,"PE":44.2,"Ind_PE":35.4,"PB":9.8, "ROCE":30.1,"NPM":12.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":26.4,"ROCE3Y":28.8,"CFO3Y":1200},
    "DABUR":       {"Industry":"FMCG",                   "Promoter":67.9,"PE":46.2,"Ind_PE":44.2,"PB":9.6, "ROCE":24.8,"NPM":14.4,"OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":20.4,"ROCE3Y":23.2,"CFO3Y":1800},
    "DLF":         {"Industry":"Real Estate",             "Promoter":74.9,"PE":52.4,"Ind_PE":38.6,"PB":4.2, "ROCE":9.8, "NPM":22.4,"OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":8.4, "ROCE3Y":9.2, "CFO3Y":3800},
    "FEDERALBNK":  {"Industry":"Financial Services",      "Promoter":0.0, "PE":10.4,"Ind_PE":15.2,"PB":1.4, "ROCE":11.2,"NPM":16.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":12.4,"ROCE3Y":10.8,"CFO3Y":3800},
    "GAIL":        {"Industry":"Oil & Gas",               "Promoter":51.9,"PE":12.4,"Ind_PE":12.8,"PB":1.6, "ROCE":14.8,"NPM":6.4, "OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":12.4,"ROCE3Y":13.8,"CFO3Y":6800},
    "GODREJCP":    {"Industry":"FMCG",                   "Promoter":63.2,"PE":42.6,"Ind_PE":44.2,"PB":8.4, "ROCE":21.4,"NPM":12.4,"OpGr3Y":12.4,"SalesGr3Y":10.4,"ROE3Y":18.4,"ROCE3Y":20.2,"CFO3Y":2200},
    "GODREJPROP":  {"Industry":"Real Estate",             "Promoter":58.5,"PE":68.4,"Ind_PE":38.6,"PB":5.8, "ROCE":8.6, "NPM":18.4,"OpGr3Y":42.4,"SalesGr3Y":38.4,"ROE3Y":8.4, "ROCE3Y":8.2, "CFO3Y":1800},
    "HAL":         {"Industry":"Capital Goods",           "Promoter":71.6,"PE":38.4,"Ind_PE":35.4,"PB":9.2, "ROCE":28.4,"NPM":14.4,"OpGr3Y":22.4,"SalesGr3Y":16.4,"ROE3Y":24.4,"ROCE3Y":27.2,"CFO3Y":4800},
    "HAVELLS":     {"Industry":"Capital Goods",           "Promoter":59.6,"PE":64.2,"Ind_PE":35.4,"PB":12.8,"ROCE":24.6,"NPM":7.4, "OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":18.4,"ROCE3Y":22.8,"CFO3Y":1400},
    "HEROMOTOCO":  {"Industry":"Automobile",              "Promoter":34.6,"PE":20.4,"Ind_PE":26.4,"PB":5.2, "ROCE":32.8,"NPM":8.4, "OpGr3Y":12.4,"SalesGr3Y":8.4, "ROE3Y":28.4,"ROCE3Y":31.4,"CFO3Y":4800},
    "ICICIPRU":    {"Industry":"Financial Services",      "Promoter":74.0,"PE":72.4,"Ind_PE":55.4,"PB":8.2, "ROCE":12.4,"NPM":8.4, "OpGr3Y":16.4,"SalesGr3Y":14.4,"ROE3Y":10.4,"ROCE3Y":11.8,"CFO3Y":3200},
    "IDFCFIRSTB":  {"Industry":"Financial Services",      "Promoter":36.6,"PE":22.4,"Ind_PE":15.2,"PB":1.6, "ROCE":9.8, "NPM":8.4, "OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":6.4, "ROCE3Y":9.2, "CFO3Y":3400},
    "IGL":         {"Industry":"Oil & Gas",               "Promoter":45.0,"PE":22.8,"Ind_PE":12.8,"PB":4.2, "ROCE":21.4,"NPM":12.4,"OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":18.4,"ROCE3Y":20.2,"CFO3Y":1600},
    "IOC":         {"Industry":"Oil & Gas",               "Promoter":51.5,"PE":6.8, "Ind_PE":12.8,"PB":1.0, "ROCE":18.2,"NPM":2.4, "OpGr3Y":4.4, "SalesGr3Y":8.4, "ROE3Y":14.4,"ROCE3Y":17.4,"CFO3Y":18000},
    "IRCTC":       {"Industry":"Infrastructure / Services","Promoter":67.4,"PE":48.6,"Ind_PE":25.1,"PB":14.8,"ROCE":38.4,"NPM":24.4,"OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":34.4,"ROCE3Y":36.8,"CFO3Y":2400},
    "IRFC":        {"Industry":"Financial Services",      "Promoter":86.4,"PE":28.4,"Ind_PE":22.1,"PB":4.2, "ROCE":6.8, "NPM":24.4,"OpGr3Y":12.4,"SalesGr3Y":8.4, "ROE3Y":12.4,"ROCE3Y":6.4, "CFO3Y":4200},
    "LTIM":        {"Industry":"Information Technology",  "Promoter":74.3,"PE":34.6,"Ind_PE":28.2,"PB":8.4, "ROCE":32.4,"NPM":14.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":28.4,"ROCE3Y":30.8,"CFO3Y":4800},
    "LTTS":        {"Industry":"Information Technology",  "Promoter":74.2,"PE":32.8,"Ind_PE":28.2,"PB":6.8, "ROCE":28.6,"NPM":12.4,"OpGr3Y":18.4,"SalesGr3Y":14.4,"ROE3Y":24.4,"ROCE3Y":27.2,"CFO3Y":2400},
    "LUPIN":       {"Industry":"Healthcare",              "Promoter":47.0,"PE":28.4,"Ind_PE":31.4,"PB":4.6, "ROCE":18.4,"NPM":10.4,"OpGr3Y":14.4,"SalesGr3Y":10.4,"ROE3Y":14.4,"ROCE3Y":17.2,"CFO3Y":2800},
    "MARICO":      {"Industry":"FMCG",                   "Promoter":59.4,"PE":44.8,"Ind_PE":44.2,"PB":14.6,"ROCE":42.8,"NPM":14.4,"OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":36.4,"ROCE3Y":40.4,"CFO3Y":1600},
    "MCDOWELL-N":  {"Industry":"FMCG",                   "Promoter":56.0,"PE":62.4,"Ind_PE":44.2,"PB":8.4, "ROCE":22.6,"NPM":8.4, "OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":18.4,"ROCE3Y":21.4,"CFO3Y":2200},
    "MOTHERSON":   {"Industry":"Automobile",              "Promoter":58.3,"PE":38.6,"Ind_PE":26.4,"PB":4.8, "ROCE":14.2,"NPM":2.4, "OpGr3Y":18.4,"SalesGr3Y":22.4,"ROE3Y":12.4,"ROCE3Y":13.4,"CFO3Y":4800},
    "MPHASIS":     {"Industry":"Information Technology",  "Promoter":55.6,"PE":28.4,"Ind_PE":28.2,"PB":5.8, "ROCE":24.6,"NPM":12.4,"OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":20.4,"ROCE3Y":23.2,"CFO3Y":1800},
    "MRF":         {"Industry":"Automobile",              "Promoter":27.8,"PE":24.6,"Ind_PE":26.4,"PB":3.4, "ROCE":16.8,"NPM":8.4, "OpGr3Y":14.4,"SalesGr3Y":10.4,"ROE3Y":14.4,"ROCE3Y":15.8,"CFO3Y":2800},
    "MUTHOOTFIN":  {"Industry":"Financial Services",      "Promoter":73.4,"PE":18.4,"Ind_PE":22.1,"PB":3.6, "ROCE":18.2,"NPM":22.4,"OpGr3Y":14.4,"SalesGr3Y":12.4,"ROE3Y":18.4,"ROCE3Y":17.4,"CFO3Y":2200},
    "NMDC":        {"Industry":"Metals & Mining",         "Promoter":60.8,"PE":9.4, "Ind_PE":18.4,"PB":2.2, "ROCE":28.4,"NPM":28.4,"OpGr3Y":8.4, "SalesGr3Y":4.4, "ROE3Y":24.4,"ROCE3Y":26.8,"CFO3Y":6800},
    "NYKAA":       {"Industry":"Retail",                  "Promoter":52.6,"PE":148.6,"Ind_PE":68.4,"PB":18.4,"ROCE":8.6, "NPM":2.4, "OpGr3Y":28.4,"SalesGr3Y":24.4,"ROE3Y":4.4, "ROCE3Y":7.8, "CFO3Y":400},
    "OBEROIRLTY":  {"Industry":"Real Estate",             "Promoter":67.7,"PE":28.6,"Ind_PE":38.6,"PB":4.8, "ROCE":18.4,"NPM":28.4,"OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":16.4,"ROCE3Y":17.8,"CFO3Y":1400},
    "OFSS":        {"Industry":"Information Technology",  "Promoter":72.8,"PE":32.4,"Ind_PE":28.2,"PB":8.6, "ROCE":38.4,"NPM":24.4,"OpGr3Y":12.4,"SalesGr3Y":10.4,"ROE3Y":34.4,"ROCE3Y":36.8,"CFO3Y":6800},
    "PAGEIND":     {"Industry":"Consumer Durables",       "Promoter":59.0,"PE":64.8,"Ind_PE":51.2,"PB":28.4,"ROCE":58.6,"NPM":12.4,"OpGr3Y":12.4,"SalesGr3Y":10.4,"ROE3Y":54.4,"ROCE3Y":56.8,"CFO3Y":800},
    "PERSISTENT":  {"Industry":"Information Technology",  "Promoter":31.1,"PE":58.4,"Ind_PE":28.2,"PB":12.4,"ROCE":28.6,"NPM":12.4,"OpGr3Y":28.4,"SalesGr3Y":24.4,"ROE3Y":24.4,"ROCE3Y":27.2,"CFO3Y":2200},
    "PETRONET":    {"Industry":"Oil & Gas",               "Promoter":50.0,"PE":12.8,"Ind_PE":12.8,"PB":2.8, "ROCE":24.6,"NPM":8.4, "OpGr3Y":6.4, "SalesGr3Y":4.4, "ROE3Y":20.4,"ROCE3Y":23.2,"CFO3Y":3800},
    "PFC":         {"Industry":"Financial Services",      "Promoter":55.9,"PE":8.6, "Ind_PE":22.1,"PB":1.6, "ROCE":8.2, "NPM":22.4,"OpGr3Y":18.4,"SalesGr3Y":14.4,"ROE3Y":14.4,"ROCE3Y":7.8, "CFO3Y":8800},
    "PIDILITIND":  {"Industry":"Chemicals",               "Promoter":70.7,"PE":72.4,"Ind_PE":19.5,"PB":18.4,"ROCE":32.4,"NPM":14.4,"OpGr3Y":14.4,"SalesGr3Y":10.4,"ROE3Y":28.4,"ROCE3Y":30.8,"CFO3Y":2400},
    "PIIND":       {"Industry":"Chemicals",               "Promoter":52.0,"PE":28.6,"Ind_PE":19.5,"PB":4.8, "ROCE":18.6,"NPM":10.4,"OpGr3Y":12.4,"SalesGr3Y":10.4,"ROE3Y":16.4,"ROCE3Y":17.8,"CFO3Y":1200},
    "PNB":         {"Industry":"Financial Services",      "Promoter":73.2,"PE":8.4, "Ind_PE":15.2,"PB":0.9, "ROCE":8.6, "NPM":8.4, "OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":6.4, "ROCE3Y":7.8, "CFO3Y":8800},
    "POLYCAB":     {"Industry":"Capital Goods",           "Promoter":67.7,"PE":42.6,"Ind_PE":35.4,"PB":8.4, "ROCE":24.8,"NPM":8.4, "OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":20.4,"ROCE3Y":23.2,"CFO3Y":1800},
    "RECLTD":      {"Industry":"Financial Services",      "Promoter":52.6,"PE":9.2, "Ind_PE":22.1,"PB":1.8, "ROCE":8.6, "NPM":24.4,"OpGr3Y":22.4,"SalesGr3Y":16.4,"ROE3Y":16.4,"ROCE3Y":8.2, "CFO3Y":7800},
    "SIEMENS":     {"Industry":"Capital Goods",           "Promoter":75.0,"PE":72.8,"Ind_PE":35.4,"PB":14.8,"ROCE":22.4,"NPM":8.4, "OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":18.4,"ROCE3Y":20.8,"CFO3Y":2400},
    "SRF":         {"Industry":"Chemicals",               "Promoter":50.6,"PE":38.4,"Ind_PE":19.5,"PB":5.8, "ROCE":14.8,"NPM":10.4,"OpGr3Y":8.4, "SalesGr3Y":10.4,"ROE3Y":14.4,"ROCE3Y":13.8,"CFO3Y":1800},
    "TORNTPHARM":  {"Industry":"Healthcare",              "Promoter":71.3,"PE":38.6,"Ind_PE":31.4,"PB":8.4, "ROCE":22.4,"NPM":14.4,"OpGr3Y":16.4,"SalesGr3Y":12.4,"ROE3Y":18.4,"ROCE3Y":21.2,"CFO3Y":2800},
    "TORNTPOWER":  {"Industry":"Power",                   "Promoter":72.8,"PE":28.4,"Ind_PE":19.4,"PB":4.8, "ROCE":14.6,"NPM":12.4,"OpGr3Y":14.4,"SalesGr3Y":10.4,"ROE3Y":14.4,"ROCE3Y":13.8,"CFO3Y":3200},
    "TVSMOTOR":    {"Industry":"Automobile",              "Promoter":57.4,"PE":42.8,"Ind_PE":26.4,"PB":12.4,"ROCE":26.8,"NPM":6.4, "OpGr3Y":22.4,"SalesGr3Y":18.4,"ROE3Y":28.4,"ROCE3Y":25.4,"CFO3Y":2800},
    "UNIONBANK":   {"Industry":"Financial Services",      "Promoter":74.8,"PE":6.8, "Ind_PE":15.2,"PB":0.9, "ROCE":8.8, "NPM":8.4, "OpGr3Y":28.4,"SalesGr3Y":22.4,"ROE3Y":8.4, "ROCE3Y":8.2, "CFO3Y":8400},
    "VEDL":        {"Industry":"Metals & Mining",         "Promoter":56.4,"PE":12.4,"Ind_PE":18.4,"PB":2.8, "ROCE":18.4,"NPM":8.4, "OpGr3Y":8.4, "SalesGr3Y":6.4, "ROE3Y":18.4,"ROCE3Y":17.2,"CFO3Y":8800},
    "VOLTAS":      {"Industry":"Capital Goods",           "Promoter":30.3,"PE":68.4,"Ind_PE":35.4,"PB":8.6, "ROCE":14.2,"NPM":4.4, "OpGr3Y":12.4,"SalesGr3Y":14.4,"ROE3Y":10.4,"ROCE3Y":13.2,"CFO3Y":800},
    "ZOMATO":      {"Industry":"Infrastructure / Services","Promoter":0.0, "PE":248.6,"Ind_PE":25.1,"PB":8.4,"ROCE":4.2, "NPM":2.4, "OpGr3Y":0.0, "SalesGr3Y":58.4,"ROE3Y":2.4, "ROCE3Y":3.8, "CFO3Y":1200},
    "ZYDUSLIFE":   {"Industry":"Healthcare",              "Promoter":74.9,"PE":28.4,"Ind_PE":31.4,"PB":4.8, "ROCE":18.6,"NPM":14.4,"OpGr3Y":18.4,"SalesGr3Y":12.4,"ROE3Y":16.4,"ROCE3Y":17.8,"CFO3Y":3200},
}

# ─── INDICATORS ───────────────────────────────────────────────────────────────
def calculate_indicators(df, mode="intraday"):
    for col in ['close','high','low','volume','open']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['close','high','low','volume']).reset_index(drop=True)

    if mode == "intraday":
        df['VWMA_A'] = ta.vwma(df['close'], df['volume'], length=9)
        df['VWMA_B'] = ta.vwma(df['close'], df['volume'], length=26)
        df['VOL_MA'] = df['volume'].rolling(20).mean()
    else:
        df['VWMA_A'] = ta.vwma(df['close'], df['volume'], length=50)
        df['VWMA_B'] = ta.vwma(df['close'], df['volume'], length=100)
        df['VOL_MA'] = df['volume'].rolling(20).mean()

    df['RSI']        = ta.rsi(df['close'], length=14)
    df['RSI_SMOOTH'] = df['RSI'].ewm(span=14, adjust=False).mean()

    macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        df['MACD']        = macd_df.iloc[:, 0]
        df['MACD_SIGNAL'] = macd_df.iloc[:, 2]
        df['MACD_HIST']   = macd_df.iloc[:, 1]
    else:
        df['MACD'] = df['MACD_SIGNAL'] = df['MACD_HIST'] = float('nan')

    bb_df = ta.bbands(df['close'], length=20, std=2)
    if bb_df is not None and not bb_df.empty:
        bb_lower = bb_df.iloc[:, 0]
        bb_upper = bb_df.iloc[:, 2]
        denom = (bb_upper - bb_lower).replace(0, float('nan'))
        df['BB_PCT'] = (df['close'] - bb_lower) / denom
    else:
        df['BB_PCT'] = float('nan')

    adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
    if adx_df is not None and not adx_df.empty:
        df['ADX']    = adx_df.iloc[:, 0]
        df['DI_POS'] = adx_df.iloc[:, 1]
        df['DI_NEG'] = adx_df.iloc[:, 2]
    else:
        df['ADX'] = df['DI_POS'] = df['DI_NEG'] = float('nan')

    st_df = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3.0)
    if st_df is not None and not st_df.empty:
        dir_cols = [c for c in st_df.columns if 'SUPERTd' in c]
        val_cols = [c for c in st_df.columns if c.startswith('SUPERT_') and
                    'SUPERTd' not in c and 'SUPERTl' not in c and 'SUPERTs' not in c]
        df['ST_DIR'] = st_df[dir_cols[0]] if dir_cols else float('nan')
        df['ST_VAL'] = st_df[val_cols[0]] if val_cols else float('nan')
    else:
        df['ST_DIR'] = df['ST_VAL'] = float('nan')

    df['EMA_200'] = ta.ema(df['close'], length=200)
    return df


def get_fibonacci_pivots(df):
    """Previous candle Fibonacci pivot: P, R1, R2, S1, S2."""
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
    if len(df) < 2: return 0.0, "No Cross", 0
    d = df.copy().dropna(subset=['VWMA_A','VWMA_B']).reset_index(drop=True)
    if len(d) < 2: return 0.0, "No Cross", 0
    d['sign'] = (d['VWMA_A'] > d['VWMA_B']).astype(int)
    crosses = d[d['sign'] != d['sign'].shift(1)].iloc[1:]
    if not crosses.empty:
        last     = crosses.iloc[-1]
        bars_ago = len(d) - 1 - crosses.index[-1]
        ctype    = "🔥 Bullish" if last['VWMA_A'] > last['VWMA_B'] else "❄️ Bearish"
        return round(float(last['VWMA_A']), 2), ctype, int(bars_ago)
    return 0.0, "No Cross", 0


# ─── SIGNAL ENGINE ────────────────────────────────────────────────────────────
def compute_signal(ltp, va, vb, rsi, vol, vol_ma, cross_val, cross_type,
                   P, R1, R2, S1, S2):
    """
    INTRADAY (VWMA 9/26):
      BUY  → RSI > 60  AND price > VWMA cross level  AND Vol > Vol MA(20)
      SELL → RSI < 30  AND price < VWMA cross level  AND Vol > Vol MA(20)

    MED-LONG TERM (VWMA 50/100):
      BUY  → RSI > 60  AND price above VWMA cross    AND Vol(0) > Vol MA(20)
      SELL → RSI < 30  AND price below VWMA cross    AND Vol(0) > Vol MA(20)

    Target = Pivot R1 (or R2 if price already past R1)
    SL     = Pivot S1 (or R1 for sells), enforced 1.5:1 R:R
    Suppressed if price is >50% into P→R1 (buy) or P→S1 (sell) zone.
    """
    signal, target, sl = "⚪ NEUTRAL", 0.0, 0.0

    vol_ok = (vol > vol_ma) if (vol_ma and vol_ma > 0) else True

    # Use live VWMA levels as reference when no prior cross detected
    ref = cross_val if cross_val > 0 else ((va + vb) / 2.0)
    above_cross = ltp > ref
    below_cross = ltp < ref

    buy_cond  = rsi > 60 and above_cross and vol_ok
    sell_cond = rsi < 30 and below_cross and vol_ok

    if not (buy_cond or sell_cond):
        return signal, target, sl

    if buy_cond:
        mid_p_r1 = (P + R1) / 2.0
        if ltp > mid_p_r1:           # >50% into P→R1 zone, suppress
            return "⚪ NEUTRAL", 0.0, 0.0
        raw_tgt = R2 if ltp >= R1 else R1
        dist    = raw_tgt - ltp
        if dist <= 0: return "⚪ NEUTRAL", 0.0, 0.0
        signal = "🟢 BUY"
        target = round(raw_tgt, 2)
        sl     = round(max(ltp - dist / 1.5, S1), 2)

    elif sell_cond:
        mid_p_s1 = (P + S1) / 2.0
        if ltp < mid_p_s1:           # >50% into P→S1 zone, suppress
            return "⚪ NEUTRAL", 0.0, 0.0
        raw_tgt = S2 if ltp <= S1 else S1
        dist    = ltp - raw_tgt
        if dist <= 0: return "⚪ NEUTRAL", 0.0, 0.0
        signal = "🔴 SELL"
        target = round(raw_tgt, 2)
        sl     = round(min(ltp + dist / 1.5, R1), 2)

    return signal, target, sl


# ─── METADATA ─────────────────────────────────────────────────────────────────
import os

def load_metadata():
    csv_path = "stock_fundamentals.csv"
    
    # 1. Try to load live fundamentals from CSV
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Ensure the CSV has a 'Ticker' column
            if not df.empty and "Ticker" in df.columns:
                # Filter to only include stocks in your universe
                df = df[df["Ticker"].isin(NIFTY100_UNIVERSE.keys())]
                return df
        except Exception as e:
            st.error(f"⚠️ Error reading fundamentals CSV: {e}")

    # 2. Fallback to static dictionary if CSV is missing
    st.warning("⚠️ Live fundamentals CSV not found. Using static hardcoded fallback data.")
    fallback = [{
        "Ticker": t, "Industry": d["Industry"], "Promoter_Percent": d.get("Promoter", 0),
        "Stock_PE": d.get("PE", 0), "Industry_PE": d.get("Ind_PE", 0), "PB": d.get("PB", 0), "ROCE": d.get("ROCE", 0)
    } for t, d in NIFTY100_UNIVERSE.items()]
    return pd.DataFrame(fallback)


# ─── SCANNER ──────────────────────────────────────────────────────────────────
def execute_scan(meta_df, token_lookup, kite, mode):
    """
    mode='intraday'  → 15min + 1D, VWMA 9/26, daily Fib pivots
    mode='medlong'   → 1D + monthly, VWMA 50/100, monthly Fib pivots (50 bars)
    """
    results = []
    is_ml   = (mode == "medlong")

    def worker(row):
        symbol = str(row['Ticker']).strip()
        token  = token_lookup.get(symbol)
        if not token: return None
        try:
            now = datetime.now()
            # Fetch enough daily history for VWMA 100 + EMA 200 + indicators
            days_back = 900 if is_ml else 400
            hist_day  = kite.historical_data(
                token,
                from_date=(now - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                to_date=now.strftime('%Y-%m-%d'),
                interval="day"
            )
            if not hist_day or len(hist_day) < 10: return None

            df_day = calculate_indicators(
                pd.DataFrame(hist_day),
                mode="longterm" if is_ml else "intraday"
            )
            ltp_val = round(float(df_day.iloc[-1]['close']), 2)

            stock_data = {
                "Stock":       symbol,
                "Industry":    row.get("Industry", "—"),
                "LTP":         ltp_val,
            }

            # ── Build timeframe dict ──────────────────────────────
            if is_ml:
                # Resample daily → monthly (50 bars back)
                df_idx = df_day.copy()
                df_idx.index = pd.to_datetime([r['date'] for r in hist_day[:len(df_idx)]])
                monthly = df_idx[['open','high','low','close','volume']].resample('ME').agg(
                    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
                ).dropna().tail(60).reset_index()   # keep 60 months max
                if len(monthly) < 5: return None
                df_monthly = calculate_indicators(monthly.rename(columns={'index':'date'}),
                                                  mode="longterm")
                timeframes = [("1D", df_day, df_day), ("1M", df_monthly, df_monthly)]
            else:
                hist_15m = kite.historical_data(
                    token,
                    from_date=(now - timedelta(days=12)).strftime('%Y-%m-%d'),
                    to_date=now.strftime('%Y-%m-%d'),
                    interval="15minute"
                )
                if not hist_15m or len(hist_15m) < 10: return None
                df_15m = calculate_indicators(pd.DataFrame(hist_15m), mode="intraday")
                timeframes = [("15M", df_15m, df_day), ("1D", df_day, df_day)]

            for tf, df_tf, piv_src in timeframes:
                if len(df_tf) < 5: continue
                latest   = df_tf.iloc[-1]
                ltp      = round(float(latest['close']), 2)
                va       = float(latest['VWMA_A'])   if pd.notna(latest.get('VWMA_A')) else 0.0
                vb       = float(latest['VWMA_B'])   if pd.notna(latest.get('VWMA_B')) else 0.0
                rsi      = float(latest['RSI'])       if pd.notna(latest.get('RSI'))    else 50.0
                rsi_s    = float(latest['RSI_SMOOTH'])if pd.notna(latest.get('RSI_SMOOTH')) else 50.0
                vol      = float(latest['volume'])
                vol_ma   = float(latest['VOL_MA'])    if pd.notna(latest.get('VOL_MA'))  else 0.0
                macd     = float(latest['MACD'])      if pd.notna(latest.get('MACD'))    else 0.0
                macd_sig = float(latest['MACD_SIGNAL'])if pd.notna(latest.get('MACD_SIGNAL')) else 0.0
                bb_pct   = float(latest['BB_PCT'])    if pd.notna(latest.get('BB_PCT'))  else 0.5
                adx      = float(latest['ADX'])       if pd.notna(latest.get('ADX'))     else 0.0
                st_dir   = float(latest['ST_DIR'])    if pd.notna(latest.get('ST_DIR'))  else 0.0
                ema200   = float(latest['EMA_200'])   if pd.notna(latest.get('EMA_200')) else 0.0

                cross_val, cross_type, bars_ago = get_crossover_details(df_tf)
                P, R1, R2, S1, S2 = get_fibonacci_pivots(piv_src)

                sig, tgt, sl = compute_signal(
                    ltp, va, vb, rsi, vol, vol_ma,
                    cross_val, cross_type,
                    P, R1, R2, S1, S2
                )

                vA_lbl = "VWMA 50" if is_ml else "VWMA 9"
                vB_lbl = "VWMA 100" if is_ml else "VWMA 26"

                stock_data.update({
                    f"Signal ({tf})":          sig,
                    f"{vA_lbl} ({tf})":        round(va, 2),
                    f"{vB_lbl} ({tf})":        round(vb, 2),
                    f"RSI ({tf})":             round(rsi, 2),
                    f"RSI Smooth ({tf})":      round(rsi_s, 2),
                    f"MACD ({tf})":            round(macd, 2),
                    f"MACD Signal ({tf})":     round(macd_sig, 2),
                    f"BB% ({tf})":             round(bb_pct, 3),
                    f"ADX ({tf})":             round(adx, 2),
                    f"Supertrend ({tf})":      "🟢 Bull" if st_dir == 1 else ("🔴 Bear" if st_dir == -1 else "—"),
                    f"EMA 200 ({tf})":         round(ema200, 2),
                    f"Vol > Vol MA ({tf})":    "✅" if vol > vol_ma else "❌",
                    f"Target ({tf})":          tgt,
                    f"StopLoss ({tf})":        sl,
                    f"Cross ({tf})":           f"{cross_type} @ {cross_val} ({bars_ago} bars ago)",
                    f"Pivots ({tf})":          f"P:{P} R1:{R1} R2:{R2} S1:{S1} S2:{S2}",
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


# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def run():
    meta_df      = load_metadata()
    kite         = get_kite()
    token_lookup = get_instrument_lookup()
    india_vix    = fetch_india_vix(kite)

    vix_color    = "#00E5A0" if india_vix < 15.0 else "#F5A623"
    regime_label = "TRENDING (VIX < 15)" if india_vix < 15.0 else "VOLATILE (VIX ≥ 15)"

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style="padding:0.8rem 0 0.4rem;font-family:'Space Grotesk',sans-serif;
                font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;color:#4A5A78;">
        Market Regime</div>
    <div style="background:#10141C;border:1px solid #1F2A3C;border-radius:8px;
                padding:0.9rem 1rem;margin-bottom:0.8rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                  color:#4A5A78;text-transform:uppercase;margin-bottom:4px;">India VIX</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;
                  font-weight:500;color:{vix_color};">{india_vix}</div>
    </div>
    <div style="background:#10141C;border:1px solid #1F2A3C;border-radius:8px;
                padding:0.8rem 1rem;margin-bottom:0.8rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                  color:#4A5A78;text-transform:uppercase;margin-bottom:4px;">Regime</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.82rem;
                  font-weight:600;color:#E8EDF5;">{regime_label}</div>
    </div>
    <div style="background:#0D2045;border:1px solid #3B82F6;border-radius:6px;
                padding:0.6rem 0.9rem;font-family:'Space Grotesk',sans-serif;
                font-size:0.75rem;color:#3B82F6;margin-bottom:0.8rem;">
      🔒 R:R Floor · <strong>1.5 : 1</strong>
    </div>
    <div style="background:#10141C;border:1px solid #1F2A3C;border-radius:8px;padding:0.8rem 1rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#4A5A78;
                  text-transform:uppercase;margin-bottom:6px;">Signal Rules</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.76rem;color:#00E5A0;margin-bottom:2px;">🟢 BUY</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;color:#8A9ABB;margin-bottom:8px;">
        RSI &gt; 60 · Price above VWMA cross<br>Vol &gt; Vol MA(20)</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.76rem;color:#FF4D6A;margin-bottom:2px;">🔴 SELL</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;color:#8A9ABB;">
        RSI &lt; 30 · Price below VWMA cross<br>Vol &gt; Vol MA(20)</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_intra, tab_ml, tab_fund = st.tabs([
        "  ⚡  Intraday / Short Swing  ",
        "  📈  Med-Long Term Trades  ",
        "  🏢  Fundamentals  ",
    ])

    for tab, mode_key, label, is_ml_tab in [
        (tab_intra, "intraday", "Intraday · Short Swing", False),
        (tab_ml,    "medlong",  "Med-Long Term Trades",   True),
    ]:
        with tab:
            sk_df  = f"df_{mode_key}"
            sk_ts  = f"ts_{mode_key}"
            if sk_df not in st.session_state:  st.session_state[sk_df]  = None
            if sk_ts not in st.session_state:  st.session_state[sk_ts]  = None

            cur_t = time.time()
            stale = (st.session_state[sk_df] is None or
                     (st.session_state[sk_ts] and cur_t - st.session_state[sk_ts] >= 900))

            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button(f"⟳  Scan", key=f"btn_{mode_key}", use_container_width=True):
                    stale = True
            with c2:
                if st.session_state[sk_ts]:
                    ts = datetime.fromtimestamp(st.session_state[sk_ts]).strftime('%H:%M:%S')
                    st.markdown(
                        f'<div style="padding-top:6px;font-family:\'JetBrains Mono\',monospace;'
                        f'font-size:0.75rem;color:#4A5A78;">Last sync &nbsp;'
                        f'<span style="color:#8A9ABB;">{ts}</span></div>',
                        unsafe_allow_html=True)

            if stale:
                with st.spinner(f"Scanning {len(meta_df)} Nifty 100 stocks…"):
                    rows = execute_scan(meta_df, token_lookup, kite, mode_key)
                    if rows:
                        st.session_state[sk_df] = pd.DataFrame(rows)
                        st.session_state[sk_ts] = cur_t
                        st.rerun()

            df = st.session_state[sk_df]
            if df is None:
                st.info("Click Scan to load data.")
            else:
                tf1 = "1D" if is_ml_tab else "15M"
                tf2 = "1M" if is_ml_tab else "1D"
                vA  = "VWMA 50" if is_ml_tab else "VWMA 9"
                vB  = "VWMA 100" if is_ml_tab else "VWMA 26"

                active_tf = st.radio("Timeframe", [tf1, tf2], horizontal=True,
                                     key=f"tf_{mode_key}")
                sig_col   = f"Signal ({active_tf})"

                if sig_col in df.columns:
                    buys  = (df[sig_col] == "🟢 BUY").sum()
                    sells = (df[sig_col] == "🔴 SELL").sum()
                    m1,m2,m3,m4 = st.columns(4)
                    m1.metric("Stocks Scanned",  len(df))
                    m2.metric("🟢 BUY Signals",  int(buys))
                    m3.metric("🔴 SELL Signals", int(sells))
                    m4.metric("⚪ Neutral",       int(len(df)-buys-sells))
                st.divider()

                base_cols = [
                    "Stock", sig_col, "LTP",
                    f"{vA} ({active_tf})", f"{vB} ({active_tf})",
                    f"RSI ({active_tf})", f"RSI Smooth ({active_tf})",
                    f"MACD ({active_tf})", f"MACD Signal ({active_tf})",
                    f"BB% ({active_tf})", f"ADX ({active_tf})",
                    f"Supertrend ({active_tf})", f"EMA 200 ({active_tf})",
                    f"Vol > Vol MA ({active_tf})",
                    f"Target ({active_tf})", f"StopLoss ({active_tf})",
                    f"Cross ({active_tf})", f"Pivots ({active_tf})",
                ]
                disp_cols = [c for c in base_cols if c in df.columns]

                sig_df = df[df[sig_col].isin(["🟢 BUY","🔴 SELL"])] \
                         if sig_col in df.columns else pd.DataFrame()

                if not sig_df.empty:
                    st.markdown(
                        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:0.7rem;'
                        f'color:#4A5A78;letter-spacing:0.06em;text-transform:uppercase;'
                        f'margin-bottom:0.5rem;">⚡ Active Signals · {active_tf}</div>',
                        unsafe_allow_html=True)
                    st.dataframe(sig_df[disp_cols], use_container_width=True, hide_index=True)
                    st.divider()
                else:
                    st.info(f"No BUY/SELL signals on {active_tf} under current conditions.")

                st.markdown(
                    f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:0.7rem;'
                    f'color:#4A5A78;letter-spacing:0.06em;text-transform:uppercase;'
                    f'margin:0.8rem 0 0.4rem;">📋 Full Nifty 100 · {active_tf}</div>',
                    unsafe_allow_html=True)
                sort_c = sig_col if sig_col in df.columns else disp_cols[0]
                st.dataframe(df[disp_cols].sort_values(by=sort_c, ascending=True),
                             use_container_width=True, hide_index=True)

    # ── Fundamentals Tab ─────────────────────────────────────────────────────
    with tab_fund:
        st.markdown(
            '<div style="font-family:\'Space Grotesk\',sans-serif;font-size:0.7rem;'
            'color:#4A5A78;letter-spacing:0.06em;text-transform:uppercase;'
            'margin-bottom:0.8rem;">Valuation, Quality & Growth Filter</div>',
            unsafe_allow_html=True)

        # Build fundamentals from static universe (no scan needed)
        fund_df = load_metadata().rename(columns={
            "Ticker":"Stock","Promoter_Percent":"Promoter (%)","Stock_PE":"PE",
            "Industry_PE":"Industry PE","NPM":"Net Profit Margin (%) FY",
            "OpGr3Y":"Op Profit Growth 3Y Avg (%)","SalesGr3Y":"Sales Growth 3Y Avg (%)",
            "ROE3Y":"ROE 3Y Avg (%)","ROCE3Y":"ROCE 3Y Avg (%)",
            "CFO3Y":"Avg CFO 3Y (₹ Cr)",
        })

        f1, f2, f3 = st.columns(3)
        with f1:
            sectors  = ["All"] + sorted(fund_df["Industry"].dropna().unique().tolist())
            sel_sec  = st.selectbox("Sector", sectors)
        with f2:
            sel_tier = st.selectbox("Promoter Tier",
                                    ["All", "High (>50%)", "Medium (30-50%)", "Low (<30%)"])
        with f3:
            sel_roce = st.selectbox("ROCE 3Y Filter",
                                    ["All", ">20%", ">15%", ">10%"])

        fdf = fund_df.copy()
        if sel_sec != "All":
            fdf = fdf[fdf["Industry"] == sel_sec]
        if sel_tier != "All":
            def tier(x):
                x = float(x) if x else 0
                return "High (>50%)" if x >= 50 else ("Medium (30-50%)" if x >= 30 else "Low (<30%)")
            fdf = fdf[fdf["Promoter (%)"].apply(tier) == sel_tier]
        if sel_roce != "All":
            thres = {"All":0,">20%":20,">15%":15,">10%":10}[sel_roce]
            fdf = fdf[pd.to_numeric(fdf["ROCE 3Y Avg (%)"], errors='coerce') >= thres]

        fund_display = [
            "Stock","Industry","Promoter (%)","PE","Industry PE","PB","ROCE",
            "Net Profit Margin (%) FY",
            "Op Profit Growth 3Y Avg (%)",
            "Sales Growth 3Y Avg (%)",
            "ROE 3Y Avg (%)",
            "ROCE 3Y Avg (%)",
            "Avg CFO 3Y (₹ Cr)",
        ]
        fund_display = [c for c in fund_display if c in fdf.columns]
        if not fdf.empty:
            st.dataframe(
                fdf[fund_display].sort_values(["Industry","Promoter (%)"],
                                              ascending=[True, False]),
                use_container_width=True, hide_index=True)
        else:
            st.info("No stocks match the selected filters.")

if __name__ == "__main__":
    run()
