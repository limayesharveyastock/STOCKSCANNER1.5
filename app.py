import streamlit as st
import pandas as pd
import pandas_ta as ta
from kiteconnect import KiteConnect
from datetime import datetime, timedelta

st.title("Technical Indicator Scanner")

@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    
    # EMA 9 and 26
    df['EMA_9'] = ta.ema(df['close'], length=9)
    df['EMA_26'] = ta.ema(df['close'], length=26)
    
    # RSI 14
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Supertrend
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="60s")
def display_indicators():
    kite = get_kite()
    stocks = {"RELIANCE": "738561"} 
    
    for name, token in stocks.items():
        st.subheader(f"📊 Stock: {name}")
        
        try:
            hist = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            df = pd.DataFrame(hist)
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            # Logic for Trend
            trend = "🟢 BULLISH" if latest['EMA_9'] > latest['EMA_26'] else "🔴 BEARISH"
            
            # Display Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Price", f"₹{latest['close']:.2f}")
            col2.metric("EMA 9/26", f"{latest['EMA_9']:.0f}/{latest['EMA_26']:.0f}")
            col3.metric("RSI", f"{latest['RSI']:.2f}")
            col4.metric("Trend", trend)
            
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            st.write(f"**Supertrend Value:** {supertrend_val:.2f}")
            st.divider()
            
        except Exception as e:
            st.error(f"Error fetching {name}: {e}")
            
    st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

display_indicators()
