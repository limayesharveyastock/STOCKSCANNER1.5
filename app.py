import streamlit as st
import pandas as pd
import pandas_ta as ta
from kiteconnect import KiteConnect
from datetime import datetime, timedelta

st.title("Technical Indicator Scanner")

# Initialize Kite connection
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
    
    df['EMA_20'] = ta.ema(df['close'], length=20)
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="60s")
def display_indicators():
    kite = get_kite()
    
    # Store stock name and token together
    stocks = {"RELIANCE": "738561"} 
    
    for name, token in stocks.items():
        st.subheader(f"📊 Stock: {name}") # This shows the Stock Name
        
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
            
            # Display Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Price", f"₹{latest['close']:.2f}")
            col2.metric("EMA (20)", f"{latest['EMA_20']:.2f}")
            col3.metric("RSI (14)", f"{latest['RSI']:.2f}")
            
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            st.write(f"**Supertrend Value:** {supertrend_val:.2f}")
            st.divider() # Line separator for each stock
            
        except Exception as e:
            st.error(f"Error fetching {name}: {e}")
            
    st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

display_indicators()
