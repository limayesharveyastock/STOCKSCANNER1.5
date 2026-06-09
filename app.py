import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- Styling ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #E0E0E0; }
    h1, h2, h3, [data-testid="stHeader"] { color: #FFD700 !important; text-align: center; font-family: 'Courier New', monospace; font-weight: bold; }
    div[data-testid="stDataFrame"] { background-color: #1E1E1E !important; border: 1px solid #444444; border-radius: 4px; padding: 5px; }
    div[data-testid="stDataFrame"] * { color: #FFFFFF !important; }
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #B0B0B0 !important; font-size: 13px !important; }
    .stButton>button { background-color: #222222 !important; color: #FFD700 !important; border: 1px solid #FFD700 !important; font-weight: bold !important; font-family: 'Courier New', monospace !important; border-radius: 4px !important; }
    .stButton>button:hover { background-color: #333333 !important; color: #FFFFFF !important; border: 1px solid #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 NIFTY 50 Blue-Chip Multi-Timeframe Structural Scanner")

# --- KiteConnect initialization (patched) ---
@st.cache_resource
def get_kite(api_key: str, access_token: str):
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

def init_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = get_kite(api_key, access_token)
    try:
        kite.profile()  # verify token
    except Exception as e:
        st.error(f"❌ Invalid/expired token: {e}")
        return None
    return kite

# --- Explicit Nifty 50 stock list ---
NIFTY50_STOCKS = [
    "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL",
    "BHARTIARTL","BPCL","BRITANNIA","CIPLA","COALINDIA","DRREDDY","EICHERMOT","GRASIM","HCLTECH","HDFCBANK",
    "HDFCLIFE","HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY","INDIGO","ITC","JSWSTEEL","JIOFIN",
    "KOTAKBANK","LT","M&M","MARUTI","MAXHEALTH","NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE",
    "SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM","TATAMOTORS","TATASTEEL","TCS","TECHM","TITAN","TRENT",
    "ULTRACEMCO","UPL","WIPRO"
]

# --- Indicator calculations ---
def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_20'] = ta.sma(df['volume'], length=20)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

# --- Buy/Sell crossover logic ---
def get_crossover_signal(df):
    if len(df) < 3: return "No Cross"
    latest, prev, prev_2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    if prev['VWMA_9'] <= prev['VWMA_26'] and latest['VWMA_9'] > latest['VWMA_26']:
        return "🔥 BUY SIGNAL (9 crosses 26 up)"
    elif prev['VWMA_9'] >= prev['VWMA_26'] and latest['VWMA_9'] < latest['VWMA_26']:
        return "❄️ SELL SIGNAL (9 crosses 26 down)"
    if prev_2['VWMA_9'] <= prev_2['VWMA_26'] and prev['VWMA_9'] > prev['VWMA_26']:
        return "🔥 BUY (1 bar ago)"
    elif prev_2['VWMA_9'] >= prev_2['VWMA_26'] and prev['VWMA_9'] < prev['VWMA_26']:
        return "❄️ SELL (1 bar ago)"
    return "No Cross"

# --- Trend evaluation ---
def evaluate_trend(latest, last_cross_price, tf="15M"):
    curr_price = float(latest['close'])
    vol_ma = float(latest['VOL_MA_50']) if tf == "1D" else float(latest['VOL_MA_20'])
    curr_vol = float(latest['volume'])
    rsi = float(latest['RSI'])
    if curr_vol > vol_ma and rsi > 60 and curr_price > last_cross_price:
        return "🟢 BULLISH"
    elif curr_vol > vol_ma and rsi < 40 and curr_price < last_cross_price:
        return "🔴 BEARISH"
    else:
        return "⚪ NEUTRAL"

# --- Chart plotting helper ---
def plot_stock_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candles"
    )])
    # VWMA overlays
    fig.add_trace(go.Scatter(x=df.index, y=df['VWMA_9'], line=dict(color='yellow', width=1), name="VWMA 9"))
    fig.add_trace(go.Scatter(x=df.index, y=df['VWMA_26'], line=dict(color='orange', width=1), name="VWMA 26"))
    fig.add_trace(go.Scatter(x=df.index, y=df['VWMA_50'], line=dict(color='cyan', width=1), name="VWMA 50"))
    fig.add_trace(go.Scatter(x=df.index, y=df['VWMA_100'], line=dict(color='magenta', width=1), name="VWMA 100"))
    # Mark crossover signals
    cross_signal = get_crossover_signal(df)
    if "BUY" in cross_signal:
        fig.add_trace(go.Scatter(x=[df.index[-1]], y=[df['close'].iloc[-1]],
            mode="markers+text", text="BUY", textposition="top center",
            marker=dict(color="green", size=12, symbol="triangle-up"), name="Buy Signal"))
    elif "SELL" in cross_signal:
        fig.add_trace(go.Scatter(x=[df.index[-1]], y=[df['close'].iloc[-1]],
            mode="markers+text", text="SELL", textposition="bottom center",
            marker=dict(color="red", size=12, symbol="triangle-down"), name="Sell Signal"))
    # RSI subplot
    fig.update_layout(
        title=f"{symbol} Chart with VWMA & Signals",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        yaxis=dict(domain=[0.3, 1]),
        yaxis2=dict(domain=[0
