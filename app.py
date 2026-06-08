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

# Dynamically fetch and map all active NSE instrument tokens
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
    
    # Technical Indicators (Updated to 50 & 100 periods)
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_100'] = ta.sma(df['volume'], length=100) # Updated to 50-period Volume MA
    
    # Supertrend
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="900s") # Maintained 15-minute auto-refresh cycle
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
        
        token = token_lookup.get(symbol)
        if not token:
            continue
        
        try:
            hist = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            # Increased minimum length guard to 110 to accommodate the new 100-period calculation matrix
            if not hist or len(hist) < 110:
                continue
                
            df = pd.DataFrame(hist)
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            rsi_val = latest['RSI']
            curr_volume = latest['volume']
            vol_ma_val = latest['VOL_MA_100']
            
            if pd.isna(rsi_val) or pd.isna(vol_ma_val):
                continue
            
            # Trend Logic: Volume Spike confirmation with RSI Momentum thresholds
            if curr_volume > vol_ma_val and rsi_val > 60:
                trend = "🟢 BULLISH"
            elif curr_volume > vol_ma_val and rsi_val < 40:
                trend = "🔴 BEARISH"
            else:
                trend = "⚪ NEUTRAL"
                
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            
            scan_results.append({
                "Stock Name": symbol,
                "LTP": round(latest['close'], 2),
                "VWMA 50": round(latest['VWMA_50'], 2),
                "VWMA 100": round(latest['VWMA_100'], 2),
                "RSI (14)": round(rsi_val, 2),
                "Volume": int(curr_volume),
                "Vol MA (100)": round(vol_ma_val, 1),
                "Supertrend": round(supertrend_val, 2),
                "Trend Status": trend
            })
            
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
        
        # Summary Grid
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Scanned", len(results_df))
        c2.metric("Vol Spike + RSI > 60", len(bullish_df))
        c3.metric("Vol Spike + RSI < 40", len(bearish_df))
        c4.metric("Consolidating/No Vol", len(neutral_df))
        
        st.divider()
        
        # Data View Segments
        st.subheader("🔥 Volume Backed Bullish Breakouts (RSI > 60 & Volume > 100 MA)")
        if not bullish_df.empty:
            st.dataframe(bullish_df.drop(columns=["Trend Status"]), use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently matching volume surge and strong bullish momentum.")
            
        st.divider()
        
        st.subheader("❄️ Volume Backed Bearish Breakdowns (RSI < 40 & Volume > 100 MA)")
        if not bearish_df.empty:
            st.dataframe(bearish_df.drop(columns=["Trend Status"]), use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently matching volume surge and distribution momentum.")
            
        st.divider()
        
        st.subheader("⚖️ Neutral Zone (Normal Volume or RSI Between 40-60)")
        if not neutral_df.empty:
            st.dataframe(neutral_df.drop(columns=["Trend Status"]), use_container_width=True, hide_index=True)
            
    else:
        st.warning("No data retrieved during scan.")
        
    st.write(f"Last data pull complete at: {datetime.now().strftime('%H:%M:%S')}")

run_nifty_50_scanner()
                         
