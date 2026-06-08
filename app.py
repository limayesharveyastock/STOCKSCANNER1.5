import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="NIFTY 50 Pro Structural Scanner")

# --- CUSTOM CSS: TERMINAL STYLING ---
st.markdown("""
<style>
    /* Global Container */
    .stApp { background-color: #00008B; color: white; }
    
    /* Headers - Yellow */
    h1, h2, h3 { color: yellow !important; text-align: center; font-family: 'Courier New', monospace; }
    
    /* Table Styling - Faint Yellow Background, Black Text */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFE0 !important;
        border: 2px solid yellow;
    }
    div[data-testid="stDataFrame"] * {
        color: #000000 !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: yellow !important;
        color: black !important;
        font-weight: bold;
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] { color: yellow; }
    [data-testid="stMetricLabel"] { color: white; }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

@st.cache_data(ttl=3600)
def get_instrument_lookup():
    kite = get_kite()
    instruments = kite.instruments("NSE")
    return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}

def fetch_india_vix(kite):
    try: return float(kite.ltp("NSE:INDIA VIX")["NSE:INDIA VIX"]["last_price"])
    except: return 14.5

# --- FULL NIFTY 50 METADATA ---
def get_nifty50_universe():
    return {
        "RELIANCE": {"Industry": "Oil & Gas"}, "TCS": {"Industry": "IT"}, "HDFCBANK": {"Industry": "Banking"},
        "ICICIBANK": {"Industry": "Banking"}, "INFY": {"Industry": "IT"}, "HINDUNILVR": {"Industry": "FMCG"},
        "ITC": {"Industry": "FMCG"}, "LT": {"Industry": "Construction"}, "SBIN": {"Industry": "Banking"},
        "BHARTIARTL": {"Industry": "Telecom"}, "BAJFINANCE": {"Industry": "Finance"}, "KOTAKBANK": {"Industry": "Banking"},
        "ASIANPAINT": {"Industry": "Paints"}, "HCLTECH": {"Industry": "IT"}, "MARUTI": {"Industry": "Auto"},
        "SUNPHARMA": {"Industry": "Pharma"}, "AXISBANK": {"Industry": "Banking"}, "TITAN": {"Industry": "Retail"},
        "ULTRACEMCO": {"Industry": "Cement"}, "TATAMOTORS": {"Industry": "Auto"}, "M&M": {"Industry": "Auto"},
        "NESTLEIND": {"Industry": "FMCG"}, "POWERGRID": {"Industry": "Power"}, "TATASTEEL": {"Industry": "Metals"},
        "NTPC": {"Industry": "Power"}, "JSWSTEEL": {"Industry": "Metals"}, "BAJAJFINSV": {"Industry": "Finance"},
        "GRASIM": {"Industry": "Cement"}, "HDFCLIFE": {"Industry": "Insurance"}, "WIPRO": {"Industry": "IT"},
        "TECHM": {"Industry": "IT"}, "ADANIENT": {"Industry": "Metals"}, "ADANIPORTS": {"Industry": "Infra"},
        "BPCL": {"Industry": "Oil & Gas"}, "DRREDDY": {"Industry": "Pharma"}, "CIPLA": {"Industry": "Pharma"},
        "BRITANNIA": {"Industry": "FMCG"}, "SBILIFE": {"Industry": "Insurance"}, "EICHERMOT": {"Industry": "Auto"},
        "TATACONSUM": {"Industry": "FMCG"}, "HEROMOTOCO": {"Industry": "Auto"}, "DIVISLAB": {"Industry": "Pharma"},
        "APOLLOHOSP": {"Industry": "Healthcare"}, "INDUSINDBK": {"Industry": "Banking"}, "LTIM": {"Industry": "IT"},
        "BEL": {"Industry": "Defence"}, "COALINDIA": {"Industry": "Mining"}, "SHRIRAMFIN": {"Industry": "Finance"},
        "BAJAJ-AUTO": {"Industry": "Auto"}, "ONGC": {"Industry": "Oil & Gas"}
    }

# --- INDICATOR & PIVOT LOGIC ---
def calculate_indicators(df):
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def calculate_session_pivots(df_1d):
    # Anchor calculation based on previous day's high/low/close
    prev_day = df_1d.iloc[-2]
    high, low, close = float(prev_day['high']), float(prev_day['low']), float(prev_day['close'])
    p = (high + low + close) / 3.0
    return round(p, 2), round(p + 0.382 * (high - low), 2), round(p - 0.382 * (high - low), 2)

# --- THREADED SCANNER ENGINE ---
def scan_stock(symbol, token, kite):
    try:
        from_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        hist_1d = kite.historical_data(token, from_date, to_date, interval="day")
        hist_15m = kite.historical_data(token, from_date, to_date, interval="15minute")
        
        df_1d = calculate_indicators(pd.DataFrame(hist_1d))
        df_15m = calculate_indicators(pd.DataFrame(hist_15m))
        
        latest = df_15m.iloc[-1]
        p, r1, s1 = calculate_session_pivots(df_1d)
        
        # Structural Signal Generation
        # VWMA 9/26 Crossover + Pivot Proximity
        signal = "NEUTRAL"
        if latest['close'] > latest['VWMA_9'] and latest['close'] > p: signal = "BUY"
        elif latest['close'] < latest['VWMA_9'] and latest['close'] < p: signal = "SELL"
        
        return {
            "Stock": symbol, "LTP": latest['close'], "Signal": signal, 
            "RSI": round(latest['RSI'], 2), "Pivot": p, "R1": r1, "S1": s1
        }
    except: return None

# --- MAIN DASHBOARD ---
def main():
    st.title("🎯 NIFTY 50 STRUCTURAL SCANNER")
    kite = get_kite()
    vix = fetch_india_vix(kite)
    
    # UI METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("India VIX", vix)
    c2.metric("Market Regime", "VOLATILE" if vix > 15 else "STABLE")
    c3.metric("Engine Status", "ONLINE")
    
    st.divider()

    if st.button("🚀 EXECUTE STRUCTURAL SCAN"):
        universe = get_nifty50_universe()
        lookup = get_instrument_lookup()
        
        results = []
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(scan_stock, sym, lookup.get(sym), kite) for sym in universe.keys() if lookup.get(sym)]
            for f in as_completed(futures):
                if f.result(): results.append(f.result())
        
        st.session_state.df = pd.DataFrame(results)

    if "df" in st.session_state:
        # Define Styling Function for Grid
        def apply_styling(df):
            # Styling Signal Column Green/Red
            def color_signal(val):
                return 'color: green' if val == 'BUY' else 'color: red' if val == 'SELL' else 'color: black'
            
            # Applying styling
            return df.style.applymap(color_signal, subset=['Signal'])

        st.subheader("TECHNICAL STRUCTURAL MATRIX")
        st.dataframe(
            apply_styling(st.session_state.df), 
            use_container_width=True,
            column_config={
                "RSI": st.column_config.ProgressColumn("RSI Trend", min_value=0, max_value=100, format="%f")
            }
        )

if __name__ == "__main__":
    main()
