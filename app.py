import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

# --- [Keep your existing Initialization, get_kite, get_instrument_lookup, and load_metadata] ---

def calculate_indicators(df):
    """Lean Indicator Set: VWMA 9/26 and RSI."""
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def get_crossover_details(df):
    """Calculates the last VWMA 9/26 crossover details."""
    df = df.copy()
    df['diff'] = df['VWMA_9'] - df['VWMA_26']
    df['sign'] = (df['diff'] > 0).astype(int)
    crosses = df[df['sign'] != df['sign'].shift(1)].iloc[1:]
    
    if not crosses.empty:
        last = crosses.iloc[-1]
        bars_ago = len(df) - crosses.index.get_loc(last.name) - 1
        signal = "🔥 BULLISH" if last['VWMA_9'] > last['VWMA_26'] else "❄️ BEARISH"
        return round(last['close'], 2), signal, bars_ago
    return 0.0, "No Cross", 0

def worker(row, kite, token_lookup):
    symbol = str(row['Ticker']).strip()
    token = token_lookup.get(symbol)
    if not token: return None
    
    try:
        # Tactical (15m) & Structural (1D) Historical Data
        hist_15 = kite.historical_data(token, from_date=(datetime.now()-timedelta(days=10)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="15minute")
        hist_1d = kite.historical_data(token, from_date=(datetime.now()-timedelta(days=200)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="day")
        
        df_15 = calculate_indicators(pd.DataFrame(hist_15))
        df_1d = calculate_indicators(pd.DataFrame(hist_1d))
        
        px_15, sig_15, age_15 = get_crossover_details(df_15)
        px_1d, sig_1d, age_1d = get_crossover_details(df_1d)
        
        return {
            **row.to_dict(), # Keeps all structural ratios: PE, PB, ROCE, Industry, Promoter%
            "LTP": round(df_15.iloc[-1]['close'], 2),
            "15M Cross": f"{sig_15} @ {px_15} ({age_15} bars ago)",
            "1D Cross": f"{sig_1d} @ {px_1d} ({age_1d} days ago)",
            "RSI (15M)": round(df_15.iloc[-1]['RSI'], 2)
        }
    except: return None

# --- [Ensure you pass these columns to your st.dataframe in the Tab view] ---
# cols = ["Stock Name", "Industry", "LTP", "15M Cross", "1D Cross", "RSI (15M)", "Stock_PE", "PB", "ROCE"]
