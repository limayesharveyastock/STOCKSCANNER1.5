import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

# --- HIGH-CONTRAST TERMINAL THEME ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #E0E0E0; }
    h1, h2, h3 { color: #FFD700 !important; text-align: center; font-family: 'Courier New', monospace; }
    div[data-testid="stDataFrame"] { background-color: #1E1E1E !important; border: 1px solid #444; }
    div[data-testid="stDataFrame"] * { color: #FFFFFF !important; }
    [data-testid="stMetricValue"] { color: #FFD700; }
    [data-testid="stMetricLabel"] { color: #E0E0E0; }
    .stButton>button { background-color: #333 !important; color: #FFD700 !important; border: 1px solid #FFD700; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide")
st.title("🎯 NIFTY 50 Blue-Chip Multi-Timeframe Structural Scanner")

# --- INITIALIZATION ---
@st.cache_resource
def get_kite():
    api_key = st.secrets.get("api_key")
    access_token = st.secrets.get("access_token")
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
        st.error(f"Error fetching instrument master: {e}")
        return {}

def fetch_india_vix(kite):
    try:
        vix_data = kite.ltp("NSE:INDIA VIX")
        return float(vix_data["NSE:INDIA VIX"]["last_price"])
    except:
        return 14.5

def load_metadata():
    nifty50_universe = {
        "ADANIENT": {"Industry": "Metals & Mining", "Promoter": 72.6, "PE": 45.2, "Ind_PE": 24.1, "PB": 4.2, "ROCE": 12.5},
        "ADANIPORTS": {"Industry": "Infrastructure", "Promoter": 65.3, "PE": 33.1, "Ind_PE": 28.5, "PB": 3.9, "ROCE": 14.8},
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
        "GRASIM": {"Industry": "Construction", "Promoter": 42.7, "PE": 44.1, "Ind_PE": 32.1, "PB": 1.9, "ROCE": 9.4},
        "HCLTECH": {"Industry": "IT", "Promoter": 60.8, "PE": 25.4, "Ind_PE": 28.2, "PB": 6.1, "ROCE": 28.9},
        "HDFCBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 18.2, "Ind_PE": 15.2, "PB": 2.6, "ROCE": 12.1},
        "HDFCLIFE": {"Industry": "Financial Services", "Promoter": 50.4, "PE": 61.2, "Ind_PE": 55.4, "PB": 4.8, "ROCE": 14.2},
        "HINDALCO": {"Industry": "Metals & Mining", "Promoter": 34.6, "PE": 16.3, "Ind_PE": 18.4, "PB": 1.8, "ROCE": 13.1},
        "HINDUNILVR": {"Industry": "FMCG", "Promoter": 61.9, "PE": 56.2, "Ind_PE": 44.2, "PB": 11.4, "ROCE": 39.5},
        "ICICIBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 17.4, "Ind_PE": 15.2, "PB": 3.1, "ROCE": 13.4},
        "INDUSINDBK": {"Industry": "Financial Services", "Promoter": 16.5, "PE": 13.2, "Ind_PE": 15.2, "PB": 1.8, "ROCE": 11.7},
        "INFY": {"Industry": "IT", "Promoter": 14.8, "PE": 24.1, "Ind_PE": 28.2, "PB": 7.4, "ROCE": 37.2},
        "INDIGO": {"Industry": "Infrastructure", "Promoter": 57.3, "PE": 21.4, "Ind_PE": 25.1, "PB": 5.2, "ROCE": 22.4},
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
        "TCS": {"Industry": "IT", "Promoter": 72.4, "PE": 29.5, "Ind_PE": 28.2, "PB": 12.8, "ROCE": 51.4},
        "TECHM": {"Industry": "IT", "Promoter": 35.1, "PE": 48.2, "Ind_PE": 28.2, "PB": 3.8, "ROCE": 15.9},
        "TITAN": {"Industry": "Consumer Durables", "Promoter": 52.9, "PE": 82.1, "Ind_PE": 51.2, "PB": 19.4, "ROCE": 25.1},
        "TRENT": {"Industry": "Retail", "Promoter": 37.0, "PE": 145.2, "Ind_PE": 68.4, "PB": 28.4, "ROCE": 24.3},
        "ULTRACEMCO": {"Industry": "Construction", "Promoter": 60.0, "PE": 41.2, "Ind_PE": 32.1, "PB": 4.7, "ROCE": 13.8},
        "UPL": {"Industry": "Chemicals", "Promoter": 32.4, "PE": 22.1, "Ind_PE": 19.5, "PB": 1.5, "ROCE": 11.1},
        "WIPRO": {"Industry": "IT", "Promoter": 72.9, "PE": 23.4, "Ind_PE": 28.2, "PB": 3.4, "ROCE": 21.2}
    }
    return pd.DataFrame([{"Ticker": t, **v} for t, v in nifty50_universe.items()])

# --- TECHNICAL ENGINE ---
def calculate_indicators(df):
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def calculate_session_pivots(df_1d):
    if len(df_1d) < 2: return 0.0, 0.0, 0.0
    p = (df_1d.iloc[-2]['high'] + df_1d.iloc[-2]['low'] + df_1d.iloc[-2]['close']) / 3.0
    return round(p, 2), round(p + 0.382 * (df_1d.iloc[-2]['high'] - df_1d.iloc[-2]['low']), 2), round(p - 0.382 * (df_1d.iloc[-2]['high'] - df_1d.iloc[-2]['low']), 2)

def get_last_crossover_details(df):
    if len(df) < 2: return 0.0, "No Cross", 0
    df = df.copy().dropna(subset=['VWMA_9', 'VWMA_26']).reset_index(drop=True)
    df['diff'] = df['VWMA_9'] - df['VWMA_26']
    df['sign'] = (df['diff'] > 0).astype(int)
    crosses = df[df['sign'] != df['sign'].shift(1)].iloc[1:]
    if not crosses.empty:
        last = crosses.iloc[-1]
        c_type = "🔥 Bullish" if last['VWMA_9'] > last['VWMA_26'] else "❄️ Bearish"
        return round(last['VWMA_9'], 2), c_type, len(df) - 1 - crosses.index[-1]
    return 0.0, "No Cross", 0

# --- PARALLEL SCANNER ---
def execute_parallel_scan(meta_df, kite, india_vix):
    scan_results = []
    token_lookup = {inst['tradingsymbol']: str(inst['instrument_token']) for inst in kite.instruments("NSE")}
    
    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token: return None
        try:
            hist_1d = calculate_indicators(pd.DataFrame(kite.historical_data(token, (datetime.now() - timedelta(200)).strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'), "day")))
            hist_15m = calculate_indicators(pd.DataFrame(kite.historical_data(token, (datetime.now() - timedelta(12)).strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'), "15minute")))
            
            p, r1, s1 = calculate_session_pivots(hist_1d)
            data = {"Stock Name": symbol, "Industry": row['Industry'], "LTP": round(float(hist_15m.iloc[-1]['close']), 2)}
            
            for tf, df in [("15M", hist_15m), ("1D", hist_1d)]:
                ltp, v9, v26 = float(df.iloc[-1]['close']), float(df.iloc[-1]['VWMA_9']), float(df.iloc[-1]['VWMA_26'])
                signal = "⚪ NEUTRAL"
                if india_vix < 15:
                    if ltp > v9 > v26: signal = "🟢 BUY"
                    elif ltp < v9 < v26: signal = "🔴 SELL"
                elif ("Bullish" in get_last_crossover_details(df)[1] and ltp <= (r1+p)/2): signal = "🟢 BUY"
                elif ("Bearish" in get_last_crossover_details(df)[1] and ltp >= (s1+p)/2): signal = "🔴 SELL"
                
                data[f"Action Signal ({tf})"] = signal
            return data
        except: return None
        
    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(worker, [row for _, row in meta_df.iterrows()]))
    return [r for r in results if r]

# --- MAIN DASHBOARD ---
def run_integrated_pipeline():
    meta_df = load_metadata(); kite = get_kite(); india_vix = fetch_india_vix(kite)
    
    if st.sidebar.button("🔄 Execute Structural Scan"):
        with st.spinner("Scanning..."):
            st.session_state.master_df = pd.DataFrame(execute_parallel_scan(meta_df, kite, india_vix))
            st.rerun()

    if "master_df" in st.session_state and st.session_state.master_df is not None:
        active_tf = st.radio("Timeframe:", ["15M", "1D"], horizontal=True)
        col_name = f"Action Signal ({active_tf})"
        
        if col_name in st.session_state.master_df.columns:
            st.dataframe(st.session_state.master_df[st.session_state.master_df[col_name].isin(["🟢 BUY", "🔴 SELL"])], use_container_width=True)
        else:
            st.error("Scan results incomplete. Please re-run.")

if __name__ == "__main__":
    run_integrated_pipeline()
