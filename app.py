import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="NIFTY 50 Professional Structural Scanner")

# --- CUSTOM CSS (The Terminal Look) ---
st.markdown("""
<style>
    /* Dark Blue Background */
    .stApp { background-color: #00008B; color: white; }
    
    /* Headers - Yellow */
    h1, h2, h3 { color: yellow !important; text-align: center; font-family: 'Courier New', monospace; }
    
    /* Faint Yellow Table Background with Black Text */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFE0 !important;
        border: 2px solid yellow;
    }
    div[data-testid="stDataFrame"] div[data-testid="stDataEditor"] {
        background-color: #FFFFE0 !important;
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
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except: return {}

# --- FULL NIFTY 50 METADATA ---
def get_nifty50_universe():
    return {
        "ADANIENT": {"Industry": "Metals", "PE": 45.2, "PB": 4.2, "ROCE": 12.5},
        "ADANIPORTS": {"Industry": "Infra", "PE": 33.1, "PB": 3.9, "ROCE": 14.8},
        "APOLLOHOSP": {"Industry": "Healthcare", "PE": 78.4, "PB": 9.1, "ROCE": 16.2},
        "ASIANPAINT": {"Industry": "Consumer", "PE": 55.4, "PB": 14.2, "ROCE": 34.1},
        "AXISBANK": {"Industry": "Finance", "PE": 14.1, "PB": 2.1, "ROCE": 11.2},
        "BAJAJ-AUTO": {"Industry": "Auto", "PE": 31.2, "PB": 8.4, "ROCE": 30.5},
        "BAJFINANCE": {"Industry": "Finance", "PE": 28.3, "PB": 5.8, "ROCE": 17.4},
        "BHARTIARTL": {"Industry": "Telecom", "PE": 52.1, "PB": 8.9, "ROCE": 18.2},
        "BPCL": {"Industry": "Oil & Gas", "PE": 11.4, "PB": 1.7, "ROCE": 22.1},
        "BRITANNIA": {"Industry": "FMCG", "PE": 54.3, "PB": 28.1, "ROCE": 48.6},
        "CIPLA": {"Industry": "Healthcare", "PE": 29.6, "PB": 4.3, "ROCE": 21.3},
        "COALINDIA": {"Industry": "Mining", "PE": 9.2, "PB": 3.4, "ROCE": 54.2},
        "DRREDDY": {"Industry": "Healthcare", "PE": 18.9, "PB": 3.1, "ROCE": 24.5},
        "HCLTECH": {"Industry": "IT", "PE": 25.4, "PB": 6.1, "ROCE": 28.9},
        "HDFCBANK": {"Industry": "Finance", "PE": 18.2, "PB": 2.6, "ROCE": 12.1},
        "HINDUNILVR": {"Industry": "FMCG", "PE": 56.2, "PB": 11.4, "ROCE": 39.5},
        "ICICIBANK": {"Industry": "Finance", "PE": 17.4, "PB": 3.1, "ROCE": 13.4},
        "INFY": {"Industry": "IT", "PE": 24.1, "PB": 7.4, "ROCE": 37.2},
        "ITC": {"Industry": "FMCG", "PE": 26.4, "PB": 7.9, "ROCE": 38.7},
        "JSWSTEEL": {"Industry": "Metals", "PE": 27.2, "PB": 3.2, "ROCE": 14.1},
        "KOTAKBANK": {"Industry": "Finance", "PE": 19.1, "PB": 2.9, "ROCE": 12.8},
        "LT": {"Industry": "Construction", "PE": 36.4, "PB": 4.8, "ROCE": 15.1},
        "M&M": {"Industry": "Auto", "PE": 28.4, "PB": 4.9, "ROCE": 19.2},
        "MARUTI": {"Industry": "Auto", "PE": 27.5, "PB": 5.1, "ROCE": 21.4},
        "NESTLEIND": {"Industry": "FMCG", "PE": 74.2, "PB": 21.4, "ROCE": 58.1},
        "NTPC": {"Industry": "Power", "PE": 17.5, "PB": 2.4, "ROCE": 11.9},
        "ONGC": {"Industry": "Oil & Gas", "PE": 8.1, "PB": 1.1, "ROCE": 14.5},
        "POWERGRID": {"Industry": "Power", "PE": 16.2, "PB": 2.9, "ROCE": 12.4},
        "RELIANCE": {"Industry": "Oil & Gas", "PE": 26.1, "PB": 2.4, "ROCE": 10.2},
        "SBIN": {"Industry": "Finance", "PE": 10.4, "PB": 1.6, "ROCE": 11.8},
        "SUNPHARMA": {"Industry": "Healthcare", "PE": 36.2, "PB": 4.9, "ROCE": 17.2},
        "TATAMOTORS": {"Industry": "Auto", "PE": 11.5, "PB": 3.2, "ROCE": 20.1},
        "TATASTEEL": {"Industry": "Metals", "PE": 38.4, "PB": 1.7, "ROCE": 10.5},
        "TCS": {"Industry": "IT", "PE": 29.5, "PB": 12.8, "ROCE": 51.4},
        "TITAN": {"Industry": "Retail", "PE": 82.1, "PB": 19.4, "ROCE": 25.1},
        "ULTRACEMCO": {"Industry": "Cement", "PE": 41.2, "PB": 4.7, "ROCE": 13.8},
        "WIPRO": {"Industry": "IT", "PE": 23.4, "PB": 3.4, "ROCE": 21.2}
    }

# --- INDICATOR & PIVOT LOGIC ---
def calculate_indicators(df):
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def calculate_session_pivots(df_1d):
    if len(df_1d) < 2: return 0, 0, 0
    prev_day = df_1d.iloc[-2]
    high, low, close = float(prev_day['high']), float(prev_day['low']), float(prev_day['close'])
    p = (high + low + close) / 3.0
    return round(p, 2), round(p + 0.382 * (high - low), 2), round(p - 0.382 * (high - low), 2)

# --- SCANNER ENGINE (REAL DATA) ---
def worker(symbol, metadata, token, kite):
    try:
        from_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        hist_1d = kite.historical_data(token, from_date, to_date, interval="day")
        hist_15m = kite.historical_data(token, from_date, to_date, interval="15minute")
        
        if not hist_1d or not hist_15m: return None
        
        df_1d = calculate_indicators(pd.DataFrame(hist_1d))
        df_15m = calculate_indicators(pd.DataFrame(hist_15m))
        
        latest = df_15m.iloc[-1]
        p, r1, s1 = calculate_session_pivots(df_1d)
        
        signal = "NEUTRAL"
        if latest['close'] > latest['VWMA_9'] and latest['close'] > p: signal = "BUY"
        elif latest['close'] < latest['VWMA_9'] and latest['close'] < p: signal = "SELL"
        
        return {
            "Stock": symbol, "Industry": metadata['Industry'], "PE": metadata['PE'],
            "PB": metadata['PB'], "ROCE": metadata['ROCE'],
            "LTP": round(latest['close'], 2), "Signal": signal, 
            "RSI": round(latest['RSI'], 2), "Pivot": p
        }
    except: return None

# --- APP DASHBOARD ---
def main():
    st.title("🎯 NIFTY 50 STRUCTURAL SCANNER")
    kite = get_kite()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Status", "Live API")
    col2.metric("Scan Universe", "Nifty 50")
    col3.metric("Engine", "Multi-Threaded")
    
    st.divider()

    if st.button("🚀 EXECUTE STRUCTURAL SCAN"):
        universe = get_nifty50_universe()
        lookup = get_instrument_lookup()
        
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, sym, meta, lookup.get(sym), kite) for sym, meta in universe.items() if lookup.get(sym)]
            for f in as_completed(futures):
                if f.result(): results.append(f.result())
        
        st.session_state.df = pd.DataFrame(results)

    if "df" in st.session_state:
        st.subheader("TECHNICAL STRUCTURAL MATRIX")
        
        # Color Formatting
        def color_signal(val):
            return 'color: green' if val == 'BUY' else 'color: red' if val == 'SELL' else 'color: black'
        
        styled_df = st.session_state.df.style.map(color_signal, subset=['Signal'])
        
        st.dataframe(
            styled_df, 
            use_container_width=True,
            column_config={
                "RSI": st.column_config.ProgressColumn("RSI", min_value=0, max_value=100, format="%f")
            }
        )

if __name__ == "__main__":
    main()
