import streamlit as st
import pandas as pd
import pandas_ta as ta
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import time

st.set_page_config(layout="wide")
st.title("🚀 NIFTY 200 Authorized Technical Scanner")

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
    
    # Technical Indicators
    df['EMA_9'] = ta.ema(df['close'], length=9)
    df['EMA_26'] = ta.ema(df['close'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Supertrend
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="300s") # Refreshes every 5 minutes for index-wide scanning
def run_nifty_200_scanner():
    kite = get_kite()
    
    # Dictionary format: {"TRADING_SYMBOL": "INSTRUMENT_TOKEN"}
    # Replace/expand this dictionary with your target NIFTY 200 tokens
    nifty_200_stocks = {
        "RELIANCE": "738561",
        "TCS": "2953217",
        "INFY": "408065",
        "HDFCBANK": "341249",
        "ICICIBANK": "1270529",
        "SBIN": "779521",
        "BHARTIARTL": "2714625",
        "LTIM": "4632577",
        "ITC": "424961",
        "AXISBANK": "1510401"
        # Add the remaining tokens here
    }
    
    scan_results = []
    
    # UI Elements for tracking progress safely
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(nifty_200_stocks)
    
    for index, (name, token) in enumerate(nifty_200_stocks.items()):
        status_text.text(f"Scanning {index + 1}/{total_stocks}: {name}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        try:
            # Fetch historical data via official channel
            hist = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            if not hist:
                continue
                
            df = pd.DataFrame(hist)
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            # Trend and Signal Logic
            trend = "🟢 BULLISH" if latest['EMA_9'] > latest['EMA_26'] else "🔴 BEARISH"
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            
            # Append rows to our master list
            scan_results.append({
                "Stock Name": name,
                "LTP": round(latest['close'], 2),
                "EMA 9": round(latest['EMA_9'], 2),
                "EMA 26": round(latest['EMA_26'], 2),
                "RSI (14)": round(latest['RSI'], 2),
                "Supertrend": round(supertrend_val, 2),
                "Trend Status": trend
            })
            
            # CRITICAL PAUSE: Enforces 3 requests/sec to strictly respect authorized limits
            time.sleep(0.35)
            
        except Exception as e:
            # Soft logging to prevent one bad token from stopping the whole scan
            print(f"Skipping {name} due to error: {e}")
            time.sleep(0.35)
            continue

    # Clear progress metrics once done
    progress_bar.empty()
    status_text.empty()
    
    # Convert results into a structured dataframe
    if scan_results:
        results_df = pd.DataFrame(scan_results)
        
        # Display summary highlights
        bullish_count = len(results_df[results_df["Trend Status"] == "🟢 BULLISH"])
        bearish_count = len(results_df[results_df["Trend Status"] == "🔴 BEARISH"])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Scanned", len(results_df))
        c2.metric("Bullish Setups", bullish_count)
        c3.metric("Bearish Setups", bearish_count)
        
        # Render the master spreadsheet dashboard
        st.dataframe(
            results_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "RSI (14)": st.column_config.NumberColumn("RSI (14)", format="%.2f"),
                "LTP": st.column_config.NumberColumn("Price (₹)", format="%.2f")
            }
        )
    else:
        st.warning("No data retrieved during scan.")
        
    st.write(f"Last data pull complete at: {datetime.now().strftime('%H:%M:%S')}")

run_nifty_200_scanner()
