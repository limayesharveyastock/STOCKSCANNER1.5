import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time

st.set_page_config(layout="wide")
st.title("🚀 NIFTY 50 Technical Scanner")

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
    df['volume'] = pd.to_numeric(df['volume'])
    
    # Technical Indicators (Retaining VWMA 9/26 for reference matrix)
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Supertrend
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="300s") # Refreshes every 5 minutes
def run_nifty_50_scanner():
    kite = get_kite()
    
    # NIFTY 50 Trading Symbols and Instrument Tokens
    nifty_50_stocks = {
        "RELIANCE": "738561",
        "TCS": "2953217",
        "INFY": "408065",
        "HDFCBANK": "341249",
        "ICICIBANK": "1270529",
        "SBIN": "779521",
        "BHARTIARTL": "2714625",
        "ITC": "424961",
        "LT": "2939649",
        "AXISBANK": "1510401",
        "KOTAKBANK": "492033",
        "HINDUNILVR": "340481",
        "BAJFINANCE": "81153",
        "MARUTI": "2800641",
        "M&M": "525825",
        "TATASTEEL": "895745",
        "HCLTECH": "1839361",
        "SUNPHARMA": "857857",
        "NTPC": "2977281",
        "POWERGRID": "3834113",
        "TITAN": "897537",
        "ULTRACEMCO": "2952193",
        "ASIANPAINT": "60417",
        "COALINDIA": "5215745",
        "INDUSINDBK": "1346049",
        "BAJAJFINSV": "4265217",
        "ADANIENT": "1118465",
        "ADANIPORTS": "3861249",
        "JIOFIN": "6
    
