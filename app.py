import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from kiteconnect import KiteConnect

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

# Dynamically fetch and map all active NSE instrument tokens to prevent truncation
@st.cache_data(ttl=86400) # Caches the instrument master map for 24 hours
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # Technical Indicators
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
    token_lookup = get_instrument_lookup()
    
    # Complete NIFTY 50 Ticker Stream
    nifty_50_symbols = [
        "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", 
        "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BHARTIARTL", 
        "BPCL", "BRITANNIA", "CIPLA", "COALINDIA", "DRREDDY", 
        "EICHERMOT", "ETERNAL", "GRASIM", "HCLTECH", "HDFCBANK", 
        "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", 
        "INDUSINDBK", "INFY", "ITC", "JSWSTEEL", "KOTAKBANK", 
        "LT", "LTIM", "M&M", "MARUTI", "MAXHEALTH", "NESTLEIND", 
        "NTPC", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", 
        "SBIN", "SUNPHARMA", "TATACONSUM", "TATAMOTORS", "TATASTEEL", 
        "TCS", "TECHM", "TITAN", "ULTRACEMCO", "WIPRO", "JIOFIN"
    ]
    
    scan_results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(nifty_50_symbols)
    
    for index, symbol in enumerate(nifty_50_symbols):
        status_text.text(f"Scanning {index + 1}/{total_stocks}: {symbol}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        # Resolve instrument token safely from master list
        token = token_lookup.get(symbol)
        if not token:
            continue # Skip if ticker symbol isn't matching the NSE master map
        
        try:
            hist = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            if not hist or len(hist) < 15:
                continue
                
            df = pd.DataFrame(hist)
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            # Condition Boundaries
            rsi_val = latest['RSI']
            if pd.isna(rsi_val):
                continue
                
            if rsi_val > 70:
                trend = "🟢 BULLISH"
            elif rsi_val < 30:
                trend = "🔴 BEARISH"
            else:
                trend = "⚪ NEUTRAL"
                
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            
            scan_results.append({
                "Stock Name": symbol,
                "LTP": round(latest['close'], 2),
                "VWMA 9": round(latest['VWMA_9'], 2),
                "VWMA 26": round(latest['VWMA_26'], 2),
                "RSI (14)": round(rsi_val, 2),
                "Supertrend": round(supertrend_val, 2),
                "Trend Status": trend
            })
            
            # Reduced sleep interval to prevent multi-minute execution lag across 50 tokens
            time.sleep(0.15)
            
        except Exception as e:
            time.sleep(0.15)
            continue

    progress_bar.empty()
    status_text.empty()
    
    if scan_results:
        results_df = pd.DataFrame(scan_results)
        
        bullish_df = results_df[results_df["Trend Status"] == "🟢 BULLISH"]
        bearish_df = results_df[results_df["Trend Status"] == "🔴 BEARISH"]
        neutral_df = results_df[results_df["Trend Status"] == "⚪ NEUTRAL"]
        
        # Summary Matrix
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Scanned", len(results_df))
        c2.metric("RSI > 70 (Bullish)", len(bullish_df))
        c3.metric("RSI < 30 (Bearish)", len(bearish_df))
        c4.metric("RSI 30-70 (Neutral)", len(neutral_df))
        
        st.divider()
        
        # Data View Segments
        st.subheader("🔥 Bullish Trend (RSI Above 70)")
        if not bullish_df.empty:
            st.dataframe(bullish_df.drop(columns=["Trend Status"]), use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently overbought.")
            
        st.divider()
        
        st.subheader("❄️ Bearish Trend (RSI Below 30)")
        if not bearish_df.empty:
            st.dataframe(bearish_df.drop(columns=["Trend Status"]), use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently oversold.")
            
        st.divider()
        
        st.subheader("⚖️ Neutral Market Trend (RSI 30-70)")
        if not neutral_df.empty:
            st.dataframe(neutral_df.drop(columns=["Trend Status"]), use_container_width=True, hide_index=True)
            
    else:
        st.warning("No data retrieved during scan.")
        
    st.write(f"Last data pull complete at: {datetime.now().strftime('%H:%M:%S')}")

run_nifty_50_scanner()
