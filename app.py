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

# --- CORE FUNCTIONS ---
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

def calculate_indicators(df):
    df['close'], df['high'], df['low'], df['volume'] = pd.to_numeric(df['close']), pd.to_numeric(df['high']), pd.to_numeric(df['low']), pd.to_numeric(df['volume'])
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    return pd.concat([df, st_data], axis=1)

def get_crossover_signal(df):
    """Detects 9 crossing 26 on the latest bar."""
    if len(df) < 2: return "No Cross"
    curr, prev = df.iloc[-1], df.iloc[-2]
    
    if prev['VWMA_9'] <= prev['VWMA_26'] and curr['VWMA_9'] > curr['VWMA_26']:
        return "🔥 9 CROSSES 26 FROM BELOW"
    elif prev['VWMA_9'] >= prev['VWMA_26'] and curr['VWMA_9'] < curr['VWMA_26']:
        return "❄️ 9 CROSSES 26 FROM ABOVE"
    return "No Cross"

# --- SCANNER LOGIC ---
def execute_parallel_scan(meta_df, token_lookup, kite):
    results = []
    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token: return None
        
        try:
            # 15M Data
            hist_15m = kite.historical_data(token, from_date=(datetime.now()-timedelta(days=10)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="15minute")
            df = calculate_indicators(pd.DataFrame(hist_15m))
            last = df.iloc[-1]
            
            # Logic: Price relative to Cross (Keep your original logic structure)
            cross_signal = get_crossover_signal(df)
            
            return {
                "Stock Name": symbol,
                "LTP": round(last['close'], 2),
                "VWMA Cross Indicator (15M)": cross_signal,
                "Trend Status (15M)": "🟢 BULLISH" if (last['RSI'] > 60) else ("🔴 BEARISH" if last['RSI'] < 40 else "⚪ NEUTRAL"),
                "RSI (15M)": round(last['RSI'], 2),
                "VWMA 9": round(last['VWMA_9'], 2),
                "VWMA 26": round(last['VWMA_26'], 2)
            }
        except: return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, row) for _, row in meta_df.iterrows()]
        for f in as_completed(futures):
            if f.result(): results.append(f.result())
    return results

# --- UI ---
if __name__ == "__main__":
    meta_df = pd.DataFrame([{"Ticker": "RELIANCE"}, {"Ticker": "TCS"}, {"Ticker": "INFY"}]) # Add your full list here
    kite = get_kite()
    tokens = get_instrument_lookup()
    
    if st.button("🔄 Scan Nifty 50"):
        data = execute_parallel_scan(meta_df, tokens, kite)
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
