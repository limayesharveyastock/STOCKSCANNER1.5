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
        "JIOFIN": "615553",
        "TATA CONSUMER": "878593"
    }
    
    scan_results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(nifty_50_stocks)
    
    for index, (name, token) in enumerate(nifty_50_stocks.items()):
        status_text.text(f"Scanning {index + 1}/{total_stocks}: {name}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        try:
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
            
            # Trend Logic: Conditioned strictly on your new RSI boundaries
            rsi_val = latest['RSI']
            if rsi_val > 70:
                trend = "🟢 BULLISH"
            elif rsi_val < 30:
                trend = "🔴 BEARISH"
            else:
                trend = "⚪ NEUTRAL"
                
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            
            scan_results.append({
                "Stock Name": name,
                "LTP": round(latest['close'], 2),
                "VWMA 9": round(latest['VWMA_9'], 2),
                "VWMA 26": round(latest['VWMA_26'], 2),
                "RSI (14)": round(rsi_val, 2),
                "Supertrend": round(supertrend_val, 2),
                "Trend Status": trend
            })
            
            time.sleep(0.35)
            
        except Exception as e:
            time.sleep(0.35)
            continue

    progress_bar.empty()
    status_text.empty()
    
    if scan_results:
        results_df = pd.DataFrame(scan_results)
        
        # Segment data based on Trend Status
        bullish_df = results_df[results_df["Trend Status"] == "🟢 BULLISH"]
        bearish_df = results_df[results_df["Trend Status"] == "🔴 BEARISH"]
        neutral_df = results_df[results_df["Trend Status"] == "⚪ NEUTRAL"]
        
        # Dashboard Overview Summary Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Scanned", len(results_df))
        c2.metric("RSI > 70 (Bullish)", len(bullish_df))
        c3.metric("RSI < 30 (Bearish)", len(bearish_df))
        c4.metric("RSI 30-70 (Neutral)", len(neutral_df))
        
        st.divider()
        
        # Section 1: Bullish Momentum
        st.subheader("🔥 Bullish Trend (RSI Above 70)")
        if not bullish_df.empty:
            st.dataframe(
                bullish_df.drop(columns=["Trend Status"]), 
                use_container_width=True, 
                hide_index=True,
                column_config={"LTP": st.column_config.NumberColumn("Price (₹)", format="%.2f")}
            )
        else:
            st.info("No stocks currently showing overbought/bullish RSI conditions.")
            
        st.divider()
        
        # Section 2: Bearish Momentum
        st.subheader("❄️ Bearish Trend (RSI Below 30)")
        if not bearish_df.empty:
            st.dataframe(
                bearish_df.drop(columns=["Trend Status"]), 
                use_container_width=True, 
                hide_index=True,
                column_config={"LTP": st.column_config.NumberColumn("Price (₹)", format="%.2f")}
            )
        else:
            st.info("No stocks currently showing oversold/bearish RSI conditions.")
            
        st.divider()
        
        # Section 3: Consolidation / Neutral Zone
        st.subheader("⚖️ Neutral Market Trend (RSI Between 30 and 70)")
        if not neutral_df.empty:
            st.dataframe(
                neutral_df.drop(columns=["Trend Status"]), 
                use_container_width=True, 
                hide_index=True,
                column_config={"LTP": st.column_config.NumberColumn("Price (₹)", format="%.2f")}
            )
        else:
            st.info("No stocks found within standard range.")
            
    else:
        st.warning("No data retrieved during scan.")
        
    st.write(f"Last data pull complete at: {datetime.now().strftime('%H:%M:%S')}")

run_nifty_50_scanner()
