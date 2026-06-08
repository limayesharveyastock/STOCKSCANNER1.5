import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")
st.title("🚀 NIFTY 50 Multi-Dimensional Scanner")

# Initialize Kite connection
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

# Dynamically fetch and map all active NSE instrument tokens
@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

# Expanded Metadata Matrix: Industry PE, PE, PB, ROCE, 52W Ranges, and 5Y Ranges
STOCK_METADATA = {
    "ADANIENT": {"Industry": "Conglomerate", "Promoter%": 72.6, "PE": 92.4, "Ind_PE": 61.2, "PB": 9.2, "ROCE": 9.8, "52W_H": 3450.0, "52W_L": 2150.0, "5Y_H": 4190.0, "5Y_L": 130.0},
    "ADANIPORTS": {"Industry": "Infrastructure", "Promoter%": 65.9, "PE": 35.1, "Ind_PE": 28.4, "PB": 4.8, "ROCE": 13.2, "52W_H": 1620.0, "52W_L": 990.0, "5Y_H": 1620.0, "5Y_L": 240.0},
    "APOLLOHOSP": {"Industry": "Healthcare", "Promoter%": 29.3, "PE": 88.7, "Ind_PE": 45.6, "PB": 9.4, "ROCE": 11.7, "52W_H": 7400.0, "52W_L": 5700.0, "5Y_H": 7400.0, "5Y_L": 1200.0},
    "ASIANPAINT": {"Industry": "Consumer Goods", "Promoter%": 52.6, "PE": 54.3, "Ind_PE": 51.1, "PB": 15.1, "ROCE": 29.4, "52W_H": 3400.0, "52W_L": 2680.0, "5Y_H": 3590.0, "5Y_L": 1400.0},
    "AXISBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 12.8, "Ind_PE": 15.2, "PB": 1.9, "ROCE": 10.2, "52W_H": 1340.0, "52W_L": 1020.0, "5Y_H": 1340.0, "5Y_L": 330.0},
    "BAJAJ-AUTO": {"Industry": "Automobile", "Promoter%": 55.1, "PE": 32.4, "Ind_PE": 26.8, "PB": 9.8, "ROCE": 31.6, "52W_H": 10700.0, "52W_L": 6200.0, "5Y_H": 10700.0, "5Y_L": 2000.0},
    "BAJFINANCE": {"Industry": "Banking & Finance", "Promoter%": 55.4, "PE": 28.9, "Ind_PE": 24.5, "PB": 4.4, "ROCE": 11.8, "52W_H": 7900.0, "52W_L": 6200.0, "5Y_H": 8190.0, "5Y_L": 1900.0},
    "BAJAJFINSV": {"Industry": "Banking & Finance", "Promoter%": 60.7, "PE": 31.2, "Ind_PE": 24.5, "PB": 3.9, "ROCE": 11.5, "52W_H": 1750.0, "52W_L": 1420.0, "5Y_H": 1930.0, "5Y_L": 460.0},
    "BEL": {"Industry": "Defense & Capital Goods", "Promoter%": 51.1, "PE": 48.5, "Ind_PE": 42.1, "PB": 11.2, "ROCE": 26.3, "52W_H": 340.0, "52W_L": 125.0, "5Y_H": 340.0, "5Y_L": 20.0},
    "BHARTIARTL": {"Industry": "Telecom", "Promoter%": 53.8, "PE": 61.2, "Ind_PE": 45.0, "PB": 6.4, "ROCE": 12.4, "52W_H": 1700.0, "52W_L": 980.0, "5Y_H": 1700.0, "5Y_L": 360.0},
    "BPCL": {"Industry": "Energy & Oil", "Promoter%": 53.0, "PE": 14.2, "Ind_PE": 12.1, "PB": 2.1, "ROCE": 17.1, "52W_H": 370.0, "52W_L": 200.0, "5Y_H": 370.0, "5Y_L": 150.0},
    "BRITANNIA": {"Industry": "FMCG", "Promoter%": 50.5, "PE": 52.1, "Ind_PE": 44.3, "PB": 28.4, "ROCE": 49.2, "52W_H": 6400.0, "52W_L": 4700.0, "5Y_H": 6400.0, "5Y_L": 2400.0},
    "CIPLA": {"Industry": "Pharmaceuticals", "Promoter%": 33.5, "PE": 24.6, "Ind_PE": 31.8, "PB": 3.8, "ROCE": 18.3, "52W_H": 1700.0, "52W_L": 1150.0, "5Y_H": 1700.0, "5Y_L": 400.0},
    "COALINDIA": {"Industry": "Energy & Oil", "Promoter%": 63.1, "PE": 9.8, "Ind_PE": 12.1, "PB": 3.4, "ROCE": 52.1, "52W_H": 540.0, "52W_L": 310.0, "5Y_H": 540.0, "5Y_L": 110.0},
    "DRREDDY": {"Industry": "Pharmaceuticals", "Promoter%": 26.7, "PE": 18.9, "Ind_PE": 31.8, "PB": 3.1, "ROCE": 20.4, "52W_H": 1400.0, "52W_L": 960.0, "5Y_H": 1400.0, "5Y_L": 450.0},
    "EICHERMOT": {"Industry": "Automobile", "Promoter%": 49.2, "PE": 29.7, "Ind_PE": 26.8, "PB": 7.2, "ROCE": 27.5, "52W_H": 5100.0, "52W_L": 3500.0, "5Y_H": 5100.0, "5Y_L": 1300.0},
    "GRASIM": {"Industry": "Materials & Cement", "Promoter%": 42.8, "PE": 42.1, "Ind_PE": 30.2, "PB": 2.2, "ROCE": 8.4, "52W_H": 2850.0, "52W_L": 2000.0, "5Y_H": 2850.0, "5Y_L": 450.0},
    "HCLTECH": {"Industry": "Information Technology", "Promoter%": 64.3, "PE": 26.4, "Ind_PE": 28.1, "PB": 6.1, "ROCE": 28.7, "52W_H": 1850.0, "52W_L": 1300.0, "5Y_H": 1850.0, "5Y_L": 410.0},
    "HDFCBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 18.2, "Ind_PE": 15.2, "PB": 2.6, "ROCE": 10.8, "52W_H": 1790.0, "52W_L": 1360.0, "5Y_H": 1790.0, "5Y_L": 750.0},
    "HDFCLIFE": {"Industry": "Banking & Finance", "Promoter%": 50.4, "PE": 78.4, "Ind_PE": 24.5, "PB": 7.8, "ROCE": 9.4, "52W_H": 740.0, "52W_L": 550.0, "5Y_H": 770.0, "5Y_L": 350.0},
    "HEROMOTOCO": {"Industry": "Automobile", "Promoter%": 34.8, "PE": 23.1, "Ind_PE": 26.8, "PB": 4.9, "ROCE": 25.1, "52W_H": 6100.0, "52W_L": 3900.0, "5Y_H": 6100.0, "5Y_L": 1600.0},
    "HINDALCO": {"Industry": "Metals & Mining", "Promoter%": 34.6, "PE": 15.4, "Ind_PE": 18.9, "PB": 1.7, "ROCE": 11.6, "52W_H": 710.0, "52W_L": 460.0, "5Y_H": 710.0, "5Y_L": 90.0},
    "HINDUNILVR": {"Industry": "FMCG", "Promoter%": 61.9, "PE": 58.2, "Ind_PE": 44.3, "PB": 11.4, "ROCE": 27.3, "52W_H": 2770.0, "52W_L": 2200.0, "5Y_H": 2950.0, "5Y_L": 1750.0},
    "ICICIBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 17.5, "Ind_PE": 15.2, "PB": 3.1, "ROCE": 11.3, "52W_H": 1360.0, "52W_L": 980.0, "5Y_H": 1360.0, "5Y_L": 280.0},
    "INDUSINDBK": {"Industry": "Banking & Finance", "Promoter%": 15.9, "PE": 13.1, "Ind_PE": 15.2, "PB": 1.8, "ROCE": 9.9, "52W_H": 1690.0, "52W_L": 1310.0, "5Y_H": 1690.0, "5Y_L": 300.0},
    "INFY": {"Industry": "Information Technology", "Promoter%": 14.8, "PE": 24.1, "Ind_PE": 28.1, "PB": 7.4, "ROCE": 37.2, "52W_H": 1950.0, "52W_L": 1380.0, "5Y_H": 1950.0, "5Y_L": 510.0},
    "ITC": {"Industry": "FMCG", "Promoter%": 0.0, "PE": 26.8, "Ind_PE": 44.3, "PB": 7.2, "ROCE": 39.1, "52W_H": 520.0, "52W_L": 399.0, "5Y_H": 520.0, "5Y_L": 140.0},
    "JSWSTEEL": {"Industry": "Metals & Mining", "Promoter%": 44.8, "PE": 28.2, "Ind_PE": 18.9, "PB": 2.8, "ROCE": 12.1, "52W_H": 1040.0, "52W_L": 760.0, "5Y_H": 1040.0, "5Y_L": 130.0},
    "KOTAKBANK": {"Industry": "Banking & Finance", "Promoter%": 25.9, "PE": 19.1, "Ind_PE": 15.2, "PB": 2.9, "ROCE": 11.1, "52W_H": 1910.0, "52W_L": 1550.0, "5Y_H": 2250.0, "5Y_L": 1000.0},
    "LT": {"Industry": "Defense & Capital Goods", "Promoter%": 0.0, "PE": 37.4, "Ind_PE": 42.1, "PB": 4.9, "ROCE": 14.8, "52W_H": 3900.0, "52W_L": 3100.0, "5Y_H": 3900.0, "5Y_L": 700.0},
    "LTIM": {"Industry": "Information Technology", "Promoter%": 68.6, "PE": 33.7, "Ind_PE": 28.1, "PB": 7.8, "ROCE": 28.4, "52W_H": 6400.0, "52W_L": 4600.0, "5Y_H": 7500.0, "5Y_L": 1100.0},
    "M&M": {"Industry": "Automobile", "Promoter%": 19.3, "PE": 30.2, "Ind_PE": 26.8, "PB": 5.1, "ROCE": 18.2, "52W_H": 3150.0, "52W_L": 1500.0, "5Y_H": 3150.0, "5Y_L": 270.0},
    "MARUTI": {"Industry": "Automobile", "Promoter%": 58.2, "PE": 27.4, "Ind_PE": 26.8, "PB": 4.6, "ROCE": 21.3, "52W_H": 13400.0, "52W_L": 9700.0, "5Y_H": 13400.0, "5Y_L": 4000.0},
    "MAXHEALTH": {"Industry": "Healthcare", "Promoter%": 23.8, "PE": 91.3, "Ind_PE": 45.6, "PB": 8.7, "ROCE": 13.1, "52W_H": 1050.0, "52W_L": 660.0, "5Y_H": 1050.0, "5Y_L": 100.0},
    "NESTLEIND": {"Industry": "FMCG", "Promoter%": 62.8, "PE": 76.4, "Ind_PE": 44.3, "PB": 24.1, "ROCE": 56.4, "52W_H": 2750.0, "52W_L": 2150.0, "5Y_H": 2750.0, "5Y_L": 1200.0},
    "NTPC": {"Industry": "Energy & Oil", "Promoter%": 51.1, "PE": 18.9, "Ind_PE": 12.1, "PB": 2.4, "ROCE": 11.8, "52W_H": 430.0, "52W_L": 290.0, "5Y_H": 430.0, "5Y_L": 70.0},
    "ONGC": {"Industry": "Energy & Oil", "Promoter%": 58.9, "PE": 8.4, "Ind_PE": 12.1, "PB": 1.1, "ROCE": 14.3, "52W_H": 340.0, "52W_L": 190.0, "5Y_H": 340.0, "5Y_L": 60.0},
    "POWERGRID": {"Industry": "Energy & Oil", "Promoter%": 51.3, "PE": 16.2, "Ind_PE": 12.1, "PB": 3.1, "ROCE": 12.9, "52W_H": 365.0, "52W_L": 240.0, "5Y_H": 365.0, "5Y_L": 80.0},
    "RELIANCE": {"Industry": "Energy & Oil", "Promoter%": 50.4, "PE": 26.5, "Ind_PE": 12.1, "PB": 2.3, "ROCE": 10.1, "52W_H": 3200.0, "52W_L": 2200.0, "5Y_H": 3200.0, "5Y_L": 850.0},
    "SBILIFE": {"Industry": "Banking & Finance", "Promoter%": 55.4, "PE": 82.1, "Ind_PE": 24.5, "PB": 11.1, "ROCE": 12.1, "52W_H": 1900.0, "52W_L": 1380.0, "5Y_H": 1900.0, "5Y_L": 650.0},
    "SBIN": {"Industry": "Banking & Finance", "Promoter%": 57.5, "PE": 10.4, "Ind_PE": 15.2, "PB": 1.6, "ROCE": 10.5, "52W_H": 915.0, "52W_L": 620.0, "5Y_H": 915.0, "5Y_L": 150.0},
    "SUNPHARMA": {"Industry": "Pharmaceuticals", "Promoter%": 54.5, "PE": 36.8, "Ind_PE": 31.8, "PB": 4.9, "ROCE": 16.4, "52W_H": 1900.0, "52W_L": 1250.0, "5Y_H": 1900.0, "5Y_L": 330.0},
    "TATACONSUM": {"Industry": "FMCG", "Promoter%": 33.6, "PE": 68.2, "Ind_PE": 44.3, "PB": 4.2, "ROCE": 9.1, "52W_H": 1250.0, "52W_L": 900.0, "5Y_H": 1250.0, "5Y_L": 280.0},
    "TATAMOTORS": {"Industry": "Automobile", "Promoter%": 46.4, "PE": 11.6, "Ind_PE": 26.8, "PB": 3.8, "ROCE": 19.4, "52W_H": 1180.0, "52W_L": 650.0, "5Y_H": 1180.0, "5Y_L": 60.0},
    "TATASTEEL": {"Industry": "Metals & Mining", "Promoter%": 33.2, "PE": 45.3, "Ind_PE": 18.9, "PB": 1.9, "ROCE": 9.2, "52W_H": 185.0, "52W_L": 110.0, "5Y_H": 185.0, "5Y_L": 25.0},
    "TCS": {"Industry": "Information Technology", "Promoter%": 71.8, "PE": 30.1, "Ind_PE": 28.1, "PB": 13.2, "ROCE": 51.4, "52W_H": 4600.0, "52W_L": 3600.0, "5Y_H": 4600.0, "5Y_L": 1600.0},
    "TECHM": {"Industry": "Information Technology", "Promoter%": 34.6, "PE": 44.2, "Ind_PE": 28.1, "PB": 4.1, "ROCE": 17.2, "52W_H": 1550.0, "52W_L": 1100.0, "5Y_H": 1800.0, "5Y_L": 480.0},
    "TITAN": {"Industry": "Consumer Goods", "Promoter%": 52.9, "PE": 85.4, "Ind_PE": 51.1, "PB": 19.8, "ROCE": 23.5, "52W_H": 3890.0, "52W_L": 3050.0, "5Y_H": 3890.0, "5Y_L": 800.0},
    "ULTRACEMCO": {"Industry": "Materials & Cement", "Promoter%": 59.9, "PE": 41.2, "Ind_PE": 30.2, "PB": 4.8, "ROCE": 12.8, "52W_H": 12100.0, "52W_L": 8200.0, "5Y_H": 12100.0, "5Y_L": 3000.0},
    "WIPRO": {"Industry": "Information Technology", "Promoter%": 72.8, "PE": 22.9, "Ind_PE": 28.1, "PB": 4.6, "ROCE": 21.1, "52W_H": 550.0, "52W_L": 380.0, "5Y_H": 740.0, "5Y_L": 160.0},
    "JIOFIN": {"Industry": "Banking & Finance", "Promoter%": 47.7, "PE": 122.4, "Ind_PE": 24.5, "PB": 1.8, "ROCE": 4.9, "52W_H": 400.0, "52W_L": 200.0, "5Y_H": 400.0, "5Y_L": 200.0}
}

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # 50-Length parameters preserved for VWMA, Vol MA and structural tracking
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="900s")
def run_integrated_pipeline():
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    nifty_50_symbols = list(STOCK_METADATA.keys())
    
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(nifty_50_symbols)
    
    for index, symbol in enumerate(nifty_50_symbols):
        status_text.text(f"Syncing Matrix {index + 1}/{total_stocks}: {symbol}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        token = token_lookup.get(symbol)
        if not token:
            continue
        
        try:
            # 1. Fetch 15-Minute Structural Frame
            hist_15m = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            # 2. Fetch 1-Day Macro Frame (Requesting 200 days to clear 100-MA requirement)
            hist_1d = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="day"
            )
            
            if not hist_15m or len(hist_15m) < 110 or not hist_1d or len(hist_1d) < 110:
                continue
                
            # Process 15 Min Frame
            df_15m = pd.DataFrame(hist_15m)
            df_15m = calculate_indicators(df_15m)
            latest_15m = df_15m.iloc[-1]
            
            # Process 1 Day Frame
            df_1d = pd.DataFrame(hist_1d)
            df_1d = calculate_indicators(df_1d)
            latest_1d = df_1d.iloc[-1]
            
            # 15M Technical Calculations
            rsi_15m = latest_15m['RSI']
            vol_ma_15m = latest_15m['VOL_MA_50']
            if curr_vol_15m := latest_15m['volume']:
                if curr_vol_15m > vol_ma_15m and rsi_15m > 60: trend_15m = "🟢 BULLISH"
                elif curr_vol_15m > vol_ma_15m and rsi_15m < 40: trend_15m = "🔴 BEARISH"
                else: trend_15m = "⚪ NEUTRAL"
            
            # 1D Technical Calculations
            rsi_1d = latest_1d['RSI']
            vol_ma_1d = latest_1d['VOL_MA_50']
            if curr_vol_1d := latest_1d['volume']:
                if curr_vol_1d > vol_ma_1d and rsi_1d > 60: trend_1d = "🟢 BULLISH"
                elif curr_vol_1d > vol_ma_1d and rsi_1d < 40: trend_1d = "🔴 BEARISH"
                else: trend_1d = "⚪ NEUTRAL"
                
            st_15m = latest_15m.filter(like='SUPERT_').iloc[0]
            st_1d = latest_1d.filter(like='SUPERT_').iloc[0]
            
            meta = STOCK_METADATA.get(symbol, {"Industry": "Other", "Promoter%": 0.0, "PE": 0.0, "Ind_PE": 0.0, "PB": 0.0, "ROCE": 0.0, "52W_H": 0, "52W_L": 0, "5Y_H": 0, "5Y_L": 0})
            
            scan_results.append({
                "Stock Name": symbol,
                "Industry": meta["Industry"],
                "Promoter Holding (%)": meta["Promoter%"],
                "Stock PE": meta["PE"],
                "Industry PE": meta["Ind_PE"],
                "PB": meta["PB"],
                "ROCE": meta["ROCE"],
                "52W High": meta["52W_H"],
                "52W Low": meta["52W_L"],
                "5Y High": meta["5Y_H"],
                "5Y Low": meta["5Y_L"],
                "LTP": round(latest_15m['close'], 2),
                
                # Timeframe Parameter Outputs
                "RSI (15M)": round(rsi_15m, 2),
                "Vol MA (15M)": round(vol_ma_15m, 1),
                "Supertrend (15M)": round(st_15m, 2),
                "Trend Status (15M)": trend_15m,
                "VWMA 50 (15M)": round(latest_15m['VWMA_50'], 2),
                "VWMA 100 (15M)": round(latest_15m['VWMA_100'], 2),
                
                "RSI (1D)": round(rsi_1d, 2),
                "Vol MA (1D)": round(vol_ma_1d, 1),
                "Supertrend (1D)": round(st_1d, 2),
                "Trend Status (1D)": trend_1d,
                "VWMA 50 (1D)": round(latest_1d['VWMA_50'], 2),
                "VWMA 100 (1D)": round(latest_1d['VWMA_100'], 2),
            })
            time.sleep(0.2)
            
        except Exception as e:
            time.sleep(0.2)
            continue

    progress_bar.empty()
    status_text.empty()
    
    if not scan_results:
        st.warning("No data retrieved during pipeline scan.")
        return
        
    master_df = pd.DataFrame(scan_results)
    
    tab1, tab2 = st.tabs(["📊 Technical Multi-Timeframe Scanner", "🏢 Structural Bifurcation View"])
    
    # --- TAB 1: NEW MULTI-TIMEFRAME INTERACTION LAYOUT ---
    with tab1:
        st.subheader("⚙️ Timeframe Dashboard Configuration")
        active_tf = st.radio("Select Active Primary Focus Timeframe:", ["15 Minute", "1 Day"], horizontal=True)
        
        suffix = " (15M)" if active_tf == "15 Minute" else " (1D)"
        trend_col = f"Trend Status{suffix}"
        
        bullish_df = master_df[master_df[trend_col] == "🟢 BULLISH"]
        bearish_df = master_df[master_df[trend_col] == "🔴 BEARISH"]
        neutral_df = master_df[master_df[trend_col] == "⚪ NEUTRAL"]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Tracked", len(master_df))
        c2.metric(f"Bullish Vol Breakout ({active_tf})", len(bullish_df))
        c3.metric(f"Bearish Vol Breakdown ({active_tf})", len(bearish_df))
        c4.metric(f"Neutral Grid ({active_tf})", len(neutral_df))
        
        st.divider()
        
        tech_display_cols = [
            "Stock Name", "LTP", f"VWMA 50{suffix}", f"VWMA 100{suffix}", 
            f"RSI{suffix}", f"Vol MA{suffix}", f"Supertrend{suffix}"
        ]
        
        st.subheader(f"🔥 Vol Surge Buy Signals ({active_tf})")
        if not bullish_df.empty:
            st.dataframe(bullish_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently matching parameters on this timeframe.")
            
        st.divider()
        
        st.subheader(f"❄️ Vol Surge Sell Signals ({active_tf})")
        if not bearish_df.empty:
            st.dataframe(bearish_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No distribution vectors detected.")
            
        st.divider()
        
        st.subheader(f"⚖️ Neutral Baseline Matrix ({active_tf})")
        if not neutral_df.empty:
            st.dataframe(neutral_df[tech_display_cols], use_container_width=True, hide_index=True)

    # --- TAB 2: ADVANCED STRUCTURAL BIFURCATION (UPGRADED METRICS) ---
    with tab2:
        st.subheader("🔍 Macro Ownership & Valuation Filter Matrix")
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            all_industries = ["All Industries"] + sorted(list(master_df["Industry"].unique()))
            selected_industry = st.selectbox("Filter by Sector Class:", all_industries)
            
        with f_col2:
            master_df["Promoter Tier"] = master_df["Promoter Holding (%)"].apply(
                lambda x: "High (>50%)" if x >= 50.0 else ("Medium (30%-50%)" if x >= 30.0 else "Low/Institutional (<30%)")
            )
            all_tiers = ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"]
            selected_tier = st.selectbox("Filter by Insider Stake Strength:", all_tiers)
            
        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            bifurcated_df = bifurcated_df[bifurcated_df["Promoter Tier"] == selected_tier]
            
        st.divider()
        
        # Upgraded Columns: PE vs Industry PE side-by-side, PB, ROCE, and 52W & 5Y Ranges
        display_cols = [
            "Stock Name", "Industry", "Promoter Holding (%)", 
            "Stock PE", "Industry PE", "PB", "ROCE", 
            "52W High", "52W Low", "5Y High", "5Y Low"
        ]
        
        if not bifurcated_df.empty:
            st.dataframe(
                bifurcated_df[display_cols].sort_values(by=["Industry", "Promoter Holding (%)"], ascending=[True, False]),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No structural profile matches these specific asset metrics.")
            
    st.write(f"Pipeline Refresh Sync Complete: {datetime.now().strftime('%H:%M:%S')}")

run_integrated_pipeline()
