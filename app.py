import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")
st.title("🎯 NIFTY 50 Blue-Chip Multi-Timeframe Structural Scanner")

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
        st.error(f"Error fetching instrument master: {e}")
        return {}

def load_metadata():
    # Baseline Nifty 50 Data
    nifty50_universe = {
        "ADANIENT": {"Industry": "Metals & Mining", "Promoter": 72.6, "PE": 45.2, "Ind_PE": 24.1, "PB": 4.2, "ROCE": 12.5},
        "AXISBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 14.1, "Ind_PE": 15.2, "PB": 2.1, "ROCE": 11.2},
        "BAJFINANCE": {"Industry": "Financial Services", "Promoter": 54.7, "PE": 28.3, "Ind_PE": 22.1, "PB": 5.8, "ROCE": 17.4},
        "BHARTIARTL": {"Industry": "Telecommunication", "Promoter": 53.1, "PE": 52.1, "Ind_PE": 41.3, "PB": 8.9, "ROCE": 18.2},
        "HDFCBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 18.2, "Ind_PE": 15.2, "PB": 2.6, "ROCE": 12.1},
        "ICICIBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 17.4, "Ind_PE": 15.2, "PB": 3.1, "ROCE": 13.4},
        "INFY": {"Industry": "Information Technology", "Promoter": 14.8, "PE": 24.1, "Ind_PE": 28.2, "PB": 7.4, "ROCE": 37.2},
        "ITC": {"Industry": "FMCG", "Promoter": 0.0, "PE": 26.4, "Ind_PE": 44.2, "PB": 7.9, "ROCE": 38.7},
        "KOTAKBANK": {"Industry": "Financial Services", "Promoter": 25.9, "PE": 19.1, "Ind_PE": 15.2, "PB": 2.9, "ROCE": 12.8},
        "LT": {"Industry": "Construction", "Promoter": 0.0, "PE": 36.4, "Ind_PE": 31.2, "PB": 4.8, "ROCE": 15.1},
        "M&M": {"Industry": "Automobile", "Promoter": 19.3, "PE": 28.4, "Ind_PE": 26.4, "PB": 4.9, "ROCE": 19.2},
        "RELIANCE": {"Industry": "Oil & Gas", "Promoter": 50.3, "PE": 26.1, "Ind_PE": 12.8, "PB": 2.4, "ROCE": 10.2},
        "SBIN": {"Industry": "Financial Services", "Promoter": 57.5, "PE": 10.4, "Ind_PE": 15.2, "PB": 1.6, "ROCE": 11.8},
        "TCS": {"Industry": "Information Technology", "Promoter": 72.4, "PE": 29.5, "Ind_PE": 28.2, "PB": 12.8, "ROCE": 51.4},
        "TITAN": {"Industry": "Consumer Durables", "Promoter": 52.9, "PE": 82.1, "Ind_PE": 51.2, "PB": 19.4, "ROCE": 25.1}
    }
    fallback = [{"Ticker": k, **v} for k, v in nifty50_universe.items()]
    return pd.DataFrame(fallback)

def calculate_indicators(df):
    df['close'], df['high'], df['low'], df['volume'] = pd.to_numeric(df['close']), pd.to_numeric(df['high']), pd.to_numeric(df['low']), pd.to_numeric(df['volume'])
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    return pd.concat([df, st_data], axis=1)

def get_crossover_signal(df):
    if len(df) < 3: return "No Cross"
    l, p, p2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    if p['VWMA_9'] <= p['VWMA_26'] and l['VWMA_9'] > l['VWMA_26']: return "🔥 9 CROSSES 26 FROM BELOW"
    if p['VWMA_9'] >= p['VWMA_26'] and l['VWMA_9'] < l['VWMA_26']: return "❄️ 9 CROSSES 26 FROM ABOVE"
    return "No Cross"

@st.cache_data(ttl=3600)
def get_daily_macro_data(_kite, token):
    try:
        hist = _kite.historical_data(token, from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="day")
        df = calculate_indicators(pd.DataFrame(hist))
        last_cross_price = float(df['close'].iloc[-1]) # Simplified for brevity
        return {
            "RSI_1D": float(df['RSI'].iloc[-1]),
            "VWMA_CROSS_SIGNAL_1D": get_crossover_signal(df),
            "VWMA_CROSS_PRICE_1D": last_cross_price,
            "TREND_STATUS_1D": "⚪ NEUTRAL" # Placeholder for complex logic
        }
    except: return None

def execute_parallel_scan(meta_df, token_lookup, kite):
    results = []
    def worker(row):
        symbol = row['Ticker']
        token = token_lookup.get(symbol)
        if not token: return None
        daily = get_daily_macro_data(kite, token)
        # 15M Logic
        df15 = calculate_indicators(pd.DataFrame(kite.historical_data(token, from_date=(datetime.now()-timedelta(days=5)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="15minute")))
        l15 = df15.iloc[-1]
        
        return {
            "Stock Name": symbol,
            "LTP": round(l15['close'], 2),
            "VWMA Cross Indicator (15M)": get_crossover_signal(df15),
            "VWMA Cross Price (15M)": round(l15['close'], 2),
            "Trend Status (15M)": "⚪ NEUTRAL",
            "RSI (15M)": round(l15['RSI'], 2),
            "VWMA 9 (15M)": round(l15['VWMA_9'], 2),
            "VWMA 26 (15M)": round(l15['VWMA_26'], 2),
            "VWMA Cross Indicator (1D)": daily["VWMA_CROSS_SIGNAL_1D"],
            "VWMA Cross Price (1D)": round(daily["VWMA_CROSS_PRICE_1D"], 2),
            "Trend Status (1D)": daily["TREND_STATUS_1D"],
            "RSI (1D)": round(daily["RSI_1D"], 2)
        }
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, row) for _, row in meta_df.iterrows()]
        for f in as_completed(futures):
            if f.result(): results.append(f.result())
    return results

# UI Execution
if __name__ == "__main__":
    meta_df = load_metadata()
    kite = get_kite()
    tokens = get_instrument_lookup()
    
    if st.button("Run Scan"):
        results = execute_parallel_scan(meta_df, tokens, kite)
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
